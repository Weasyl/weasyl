import ConfigParser
import errno
import functools
import os
import shutil
import socket
import subprocess
import time
import urlparse

import click
import pkg_resources
import toposort


def is_wzl_dev():
    return os.environ.get('WZL') == 'dev'


def ensure_wzl_dev(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        if not is_wzl_dev():
            raise click.ClickException(
                "this command can only be run in a development container")
        return func(*a, **kw)
    return wrapper


wzl_egg_info = '/weasyl-src/_wzl/wzl.egg-info'


def ensure_egg_info():
    """
    Sometimes wzl.egg-info isn't generated when it should be.
    """
    if os.path.exists(wzl_egg_info):
        return
    cmd(['python', 'setup.py', 'egg_info'], cwd=os.path.dirname(wzl_egg_info))


def forward_from_wzl_dev(func):
    @functools.wraps(func)
    def wrapper(args):
        if is_wzl_dev():
            ensure_egg_info()
            forward([
                'docker-compose', 'run', 'weasyl-app-dev',
                func.__name__, '--'] + list(args))
        return func(args)
    return wrapper


def forward(args):
    click.secho('==> {}'.format(args), fg='green')
    os.execvp(args[0], args)


def cmd(args, **kw):
    click.secho('==> {}'.format(args), fg='green')
    subprocess.check_call(args, **kw)


@click.group(context_settings=dict(help_option_names=('-h', '--help')))
def wzl():
    """
    wzl.

    Manages an instance of weasyl.
    """


@wzl.command()
@ensure_wzl_dev
def setup():
    """
    Do initial required setup.

    Currently, this means:

    \b
     - Copy example config files.
    """
    config_dir = 'config'
    config_files = set(os.listdir(config_dir))
    for f in config_files:
        prefix, sep, suffix = f.rpartition('.example')
        if sep and not suffix and prefix not in config_files:
            click.echo('{} => {}'.format(f, prefix))
            shutil.copy(
                os.path.join(config_dir, f), os.path.join(config_dir, prefix))


@wzl.command()
@click.option('-n', '--no-daemon', is_flag=True, help=(
    "Don't run the server in the background."
))
def run(no_daemon):
    """
    Start the app server.

    This requires all of the base images to have been built.
    """
    if is_wzl_dev():
        detach_flag = '--abort-on-container-exit' if no_daemon else '-d'
        forward([
            'docker-compose', 'up', detach_flag, '--remove-orphans',
        ])
    else:
        forward([
            'twistd', '--pidfile=', '-n',
            '-y', pkg_resources.resource_filename('weasyl', 'weasyl.tac'),
        ])


@wzl.command()
@ensure_wzl_dev
def url():
    """
    Get the URL for the running weasyl instance.

    This will be nginx's port, but that will reverse-proxy to all the right
    places.
    """
    nginx = subprocess.check_output(['docker-compose', 'port', 'nginx', '80'])
    ip, _, port = nginx.strip().partition(':')
    if ip == '0.0.0.0':
        host = os.environ.get('DOCKER_HOST')
        if host is None:
            ip = '127.0.0.1'
        else:
            parsed = urlparse.urlparse(host)
            ip, _, _ = parsed.netloc.partition(':')
    click.echo('http://{}:{}'.format(ip, port))


def can_connect(host, port):
    s = socket.socket()
    s.settimeout(5)
    while True:
        try:
            s.connect((host, port))
        except socket.error as e:
            if e.errno in (errno.ECONNREFUSED, errno.ETIMEDOUT):
                return False
            elif e.errno == errno.EINTR:
                continue
            else:
                raise
        else:
            return True


def wait_for_postgres(port=5432):
    started_at = time.time()
    if can_connect('db', port):
        return

    bar = click.progressbar(
        length=60, show_percent=False,
        label='waiting for postgres to come up')
    with bar:
        while True:
            waited = time.time() - started_at
            bar.update(waited - bar.pos)
            if waited > 60:
                raise click.ClickException(
                    "waited too long for postgres to come up")
            time.sleep(1)
            if can_connect('db', port):
                return


@wzl.command(add_help_option=False, context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@forward_from_wzl_dev
def test(args):
    """
    Run the tests.

    This will also wait until postgres comes up before beginning.
    """
    wait_for_postgres()
    args = list(args)
    cmd([
        'py.test', '--cov=/weasyl-src/libweasyl/libweasyl',
        '/weasyl-src/libweasyl/libweasyl',
    ] + args)
    cmd([
        'py.test', '--cov=/weasyl-src/weasyl', '--cov-append',
        '/weasyl-src/weasyl',
    ] + args)
    shutil.copyfile('.coverage', '/weasyl-src/.coverage')


@wzl.command(add_help_option=False, context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@ensure_wzl_dev
def compose(args, _exec=True):
    """Run a docker-compose command."""
    runner = forward if _exec else cmd
    runner(['docker-compose'] + list(args))


@wzl.command()
@click.pass_context
def logtail(ctx):
    """
    Tail service logs.

    This is the same as `compose logs --tail 10 -f`.
    """
    ctx.invoke(compose, args=('logs', '--tail', '10', '-f'))


@wzl.command()
@click.argument('service')
@click.pass_context
def attach(ctx, service):
    """
    Attach to a running service.

    This is the same as `compose exec {service} /bin/bash`.
    """
    ctx.invoke(compose, args=('exec', service, '/bin/bash'))


@wzl.command()
@click.pass_context
def stop(ctx):
    """
    Stop running services.

    Services' volumes will not be deleted.
    """
    ctx.invoke(compose, args=('stop',))


@wzl.command()
@click.pass_context
@click.argument('services', nargs=-1, type=click.UNPROCESSED)
def restart(ctx, services):
    """
    Restart services.

    Name services to be restarted, or name nothing to restart all services.
    """
    ctx.invoke(compose, args=('restart',) + services)


@wzl.command(add_help_option=False, context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@forward_from_wzl_dev
def alembic(args):
    """Run an alembic command."""
    wait_for_postgres()
    forward(['alembic', '-c', '/weasyl-app/config/alembic.ini'] + list(args))


@wzl.command('upgrade-db')
@click.pass_context
def upgrade_db(ctx):
    """
    Upgrade the database.

    This is the same as `alembic upgrade head`.
    """
    ctx.invoke(alembic, args=('upgrade', 'head'))


@wzl.command('write-versions')
@ensure_wzl_dev
def write_versions():
    """
    Write out _version.py files.
    """
    conf = ConfigParser.RawConfigParser()
    conf.read('/weasyl-src/setup.cfg')
    version = conf.get('metadata', 'version')
    git = ['git', '--git-dir', '/weasyl-src/.git']
    sha = subprocess.check_output(git + [
        'rev-parse', '--short', 'HEAD',
    ]).strip()

    try:
        post = subprocess.check_output(git + [
            'rev-list', '--count', 'v{}..HEAD'.format(version),
        ], stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as e:
        if e.returncode != 128:
            raise
        version += '.dev0'
        post = -1
    else:
        post = int(post)
        if post > 0:
            version = '{}.post{}'.format(version, post)
        index_check = subprocess.call(git + [
            'diff-index', '--quiet', 'HEAD',
        ])
        if index_check == 1:
            version += '.dev0'

    if post != 0:
        version = '{}+git.{}'.format(version, sha)

    version_file = """

### Generated by `wzl write-versions`. ###

__version__ = {version!r}
__sha__ = {sha!r}

    """.format(version=version, sha=sha).strip() + '\n'
    version_files = [
        '/weasyl-src/weasyl/_version.py',
        '/weasyl-src/libweasyl/libweasyl/_version.py',
    ]
    for filename in version_files:
        with open(filename, 'w') as outfile:
            outfile.write(version_file)


PARTS = {
    'weasyl-base': {
        'compose-file': 'docker-compose-build.yml',
        'command': ['build'],
    },
    'weasyl-build': {
        'requires': ['weasyl-base'],
        'compose-file': 'docker-compose-build.yml',
        'command': ['build'],
    },
    'weasyl-build-dev-wheels': {
        'requires': ['weasyl-build'],
        'compose-file': 'docker-compose-build.yml',
        'command': ['run', '--rm'],
        'service': 'weasyl-build',
        'args': ["/weasyl-src/libweasyl[development]"],
    },
    'weasyl-build-node-modules': {
        'requires': ['weasyl-build'],
        'compose-file': 'docker-compose-build.yml',
        'command': ['run', '--rm', '--entrypoint', 'as-weasyl', '--workdir', '/weasyl-src'],
        'service': 'weasyl-build',
        'args': ['npm', 'install', '-q'],
    },
    'weasyl-app': {
        'requires': ['weasyl-build-dev-wheels'],
        'compose-file': 'docker-compose-build.yml',
        'command': ['build'],
    },
    'weasyl-app-dev': {
        'requires': ['weasyl-app'],
        'compose-file': 'docker-compose.yml',
        'command': ['build'],
    },
    'db': {
        'compose-file': 'docker-compose.yml',
        'command': ['build'],
    },
    'nginx': {
        'compose-file': 'docker-compose.yml',
        'command': ['build'],
    },
    'weasyl-assets': {
        'requires': ['weasyl-base'],
        'compose-file': 'docker-compose-build.yml',
        'command': ['build'],
    },
    'weasyl-assets-sass': {
        'requires': ['weasyl-assets', 'weasyl-build-node-modules'],
        'compose-file': 'docker-compose-build.yml',
        'command': ['run', '--rm'],
        'service': 'weasyl-assets',
        'args': ['as-weasyl', 'gulp', 'sass'],
    },
}

PARTS_CHOICE = click.Choice(sorted(PARTS))

DEPS = {
    k: set(v.get('requires', ()))
    for k, v in PARTS.items()
}
RDEPS = {
    k: {kk for kk, deps in DEPS.items() if k in deps}
    for k in DEPS
}


@wzl.command()
@click.option('-r', '--reverse-deps', is_flag=True, help=(
    "Build the reverse-dependencies of the listed targets."
))
@click.option('-D', '--no-deps', is_flag=True, help=(
    "Don't build the targets that the provided targets depend on."
))
@click.option('-n', '--dry-run', is_flag=True, help=(
    "Show what would be done."
))
@click.option('--all', 'all_targets', is_flag=True, help=(
    "Build all targets."
))
@click.option('-f', '--no-cache', is_flag=True, help=(
    "If possible, don't use cache for this build."
))
@click.argument('target', nargs=-1, type=PARTS_CHOICE)
@click.pass_context
@ensure_wzl_dev
def build(ctx, reverse_deps, no_deps, dry_run, all_targets, no_cache, target):
    """
    Build docker images.

    `write-versions` will always be called first before any building is done.

    This is required to run anything. Building a target image will first build
    its dependencies unless --no-deps is specified. The default if no targets
    are specified is to build the 'weasyl-app-dev' image.

    If --reverse-deps is specified, instead of building the listed targets and
    the dependencies of the listed targets, the listed targets and the targets
    depending on the listed targets will be built.

    If --no-cache is specified, builds that use `docker-compose build`
    will be run with --no-cache as well.

    Possible targets are:

    \b
     - weasyl-base
     - weasyl-build
     - weasyl-build-dev-wheels [1]
     - weasyl-app
     - weasyl-app-dev
     - db
     - nginx
     - assets
     - assets-sass [2]

    [1]: Not an image, but uses the same tooling to produce python wheels used
    by other images.

    [2]: Not an image, but builds the static assets for the site in place.
    """
    ctx.invoke(write_versions)

    if all_targets:
        target = set(PARTS)
    elif target:
        target = set(target)
    else:
        target = {'weasyl-app-dev'}

    all_targets = set()
    deps = RDEPS if reverse_deps else DEPS
    while target:
        t = target.pop()
        p = PARTS[t]
        all_targets.add(t)
        if not no_deps:
            target.update(deps[t])

    order = toposort.toposort_flatten({
        k: {d for d in DEPS[k] if d in all_targets} for k in all_targets})
    for target in order:
        p = PARTS[target]
        command = p['command']
        if command == ['build'] and no_cache:
            command.append('--no-cache')
        command = (
            ['docker-compose', '-f', p['compose-file']] +
            command +
            [p.get('service', target)] +
            p.get('args', []))
        if dry_run:
            click.echo('--> {}'.format(command))
        else:
            cmd(command)


@wzl.command()
@click.option('--dist', is_flag=True, help=(
    "Try harder to restore the system to its original state."
))
@click.confirmation_option(prompt=(
    "Deleting containers or images _should_ not delete any important state "
    "(like uncommitted code), but, still: are you sure?"
))
@click.pass_context
def clean(ctx, dist):
    """
    Stop everything and delete services' volumes.

    This will also clean up 'orphaned' containers that docker-compose spawned,
    but was not keeping track of.

    If --dist is passed, try to restore the system as close as docker-compose
    can to its original state. This means deleting containers, cached images,
    and volumes.

    The only thing that won't be destroyed is the 'wzl' image used as the main
    entry point, since it's in use. To delete it as well:

      $ docker rmi wzl
    """
    compose_files = {p['compose-file'] for p in PARTS.values()}
    for compose_file in sorted(compose_files):
        args = ['-f', compose_file, 'down', '--remove-orphans']
        if dist:
            args.extend(['--rmi', 'all', '--volumes'])
        ctx.invoke(compose, args=args, _exec=False)


@wzl.command()
@click.argument('target', type=PARTS_CHOICE)
@ensure_wzl_dev
def shell(target):
    """
    Run a shell in an image target.

    See `wzl build` for which targets are images. This is primarily for
    debugging. It allows the user to easily inspect what's in the image built
    by docker-compose.
    """
    p = PARTS[target]
    service = p.get('service', target)
    if service != target:
        raise click.Abort("{!r} isn't an image".format(target))
    forward([
        'docker-compose', '-f', p['compose-file'],
        'run', '--entrypoint', '/bin/bash', service, '-i',
    ])


if __name__ == '__main__':
    wzl()

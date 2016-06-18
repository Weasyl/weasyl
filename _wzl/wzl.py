import functools
import os
import shutil
import subprocess
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


def forward_from_wzl_dev(func):
    @functools.wraps(func)
    def wrapper(args):
        if is_wzl_dev():
            forward([
                'docker-compose', 'run', 'weasyl-app-dev',
                func.__name__, '--'] + list(args))
        return func(args)
    return wrapper


def forward(args):
    click.secho('==> {}'.format(args), fg='green')
    os.execvp(args[0], args)


def cmd(args):
    click.secho('==> {}'.format(args), fg='green')
    subprocess.check_call(args)


@click.group(context_settings=dict(help_option_names=('-h', '--help')))
def wzl():
    """
    wzl.

    Manages an instance of weasyl.
    """


@wzl.command()
@click.option('-d', '--detach', is_flag=True, help=(
    "Don't run the server in the foreground."
))
def run(detach):
    """
    Start the app server.

    This requires all of the base images to have been built.
    """
    if is_wzl_dev():
        detach_flag = '-d' if detach else '--abort-on-container-exit'
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


@wzl.command(add_help_option=False, context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@forward_from_wzl_dev
def test(args):
    """
    Run the tests.
    """
    args = list(args)
    cmd([
        'py.test', '--cov=/weasyl-src/libweasyl/libweasyl',
        '/weasyl-src/libweasyl/libweasyl',
    ] + args)
    cmd([
        'py.test', '--cov=/weasyl-src/weasyl', '--cov-append',
        '/weasyl-src/weasyl',
    ] + args)
    shutil.copy('.coverage', '/weasyl-src')


@wzl.command(add_help_option=False, context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@ensure_wzl_dev
def compose(args):
    """Run a docker-compose command."""
    forward(['docker-compose'] + list(args))


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


@wzl.command(add_help_option=False, context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@forward_from_wzl_dev
def alembic(args):
    """Run an alembic command."""
    forward(['alembic', '-c', '/weasyl-app/config/alembic.ini'] + list(args))


@wzl.command('upgrade-db')
@click.pass_context
def upgrade_db(ctx):
    """
    Upgrade the database.

    This is the same as `alembic upgrade head`.
    """
    ctx.invoke(alembic, args=('upgrade', 'head'))


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
    'assets': {
        'compose-file': 'docker-compose-build.yml',
        'command': ['build'],
    },
    'assets-sass': {
        'requires': ['assets'],
        'compose-file': 'docker-compose-build.yml',
        'command': ['run', '--rm'],
        'service': 'assets',
        'args': ['sh', '-euxc', """

        npm install
        gulp sass

        """],
    },
}

PARTS_CHOICE = click.Choice(sorted(PARTS))

DEPS = {
    k: set(v.get('requires', ()))
    for k, v in PARTS.items()
}


@wzl.command()
@click.option('-D', '--no-deps', is_flag=True, help=(
    "Don't build the targets that the provided targets depend on."
))
@click.argument('target', nargs=-1, type=PARTS_CHOICE)
@ensure_wzl_dev
def build(no_deps, target):
    """
    Build docker images.

    This is required to run anything. Building a target image will first build
    its dependencies unless --no-deps is specified. The default if no targets
    are specified is to build the 'weasyl-app-dev' image.

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

    if target:
        target = set(target)
    else:
        target = {'weasyl-app-dev'}

    all_targets = set()
    while target:
        t = target.pop()
        p = PARTS[t]
        all_targets.add(t)
        if not no_deps and 'requires' in p:
            target.update(p['requires'])

    order = toposort.toposort_flatten({
        k: {d for d in DEPS[k] if d in all_targets} for k in all_targets})
    for target in order:
        p = PARTS[target]
        cmd(['docker-compose', '-f', p['compose-file']] +
            p['command'] +
            [p.get('service', target)] +
            p.get('args', []))


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

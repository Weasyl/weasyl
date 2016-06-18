import functools
import os
import subprocess

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
def run():
    """
    Start the app server.

    This requires all of the base images to have been built.
    """
    if is_wzl_dev():
        forward([
            'docker-compose', 'up', '--abort-on-container-exit', '--remove-orphans',
        ])
    else:
        forward([
            'twistd', '--pidfile=', '-n',
            '-y', pkg_resources.resource_filename('weasyl', 'weasyl.tac'),
        ])


@wzl.command(add_help_option=False, context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@ensure_wzl_dev
def compose(args):
    """Run a docker-compose command."""
    forward(['docker-compose'] + list(args))


@wzl.command(add_help_option=False, context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def alembic(args):
    """Run an alembic command."""
    if is_wzl_dev():
        forward(['docker-compose', 'run', 'weasyl-app-dev', 'alembic', '--'] + list(args))
    else:
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
}

DEPS = {
    k: set(v.get('requires', ()))
    for k, v in PARTS.items()
}


@wzl.command()
@click.option('-D', '--no-deps', is_flag=True, help=(
    "Don't build the targets that the provided targets depend on."
))
@click.argument('target', nargs=-1, type=click.Choice(sorted(PARTS)))
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

    [1]: Not an image, but uses the same tooling to produce python wheels used
    by other images.
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


if __name__ == '__main__':
    wzl()

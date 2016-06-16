import os

import click
import pkg_resources


def forward(args):
    click.secho('==> {}'.format(args), fg='green')
    os.execvp(args[0], args)


@click.group()
def wzl():
    pass


@wzl.command()
def run():
    forward(['twistd', '--pidfile=', '-ny', pkg_resources.resource_filename(__name__, 'weasyl.tac')])

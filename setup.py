from setuptools import setup

setup(
    name='weasyl',
    packages=[
        'weasyl',
        'weasyl.controllers',
        'weasyl.test',
        'weasyl.test.login',
        'weasyl.test.resetpassword',
        'weasyl.test.useralias',
        'weasyl.test.web',
        'weasyl.util',
        'libweasyl', 'libweasyl.models',
        'libweasyl.test', 'libweasyl.models.test',
    ],
    package_data={
        'weasyl': [
            'templates/*/*.html',
            'templates/control/2fa/*.html',
        ],
        'libweasyl': [
            'alembic/*.py', 'alembic/script.py.mako', 'alembic/versions/*.py',
            'test/data/*',
        ],
    },
)

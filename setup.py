from setuptools import setup

setup(
    name='weasyl',
    packages=['weasyl', 'weasyl.controllers'],
    package_data={
        'weasyl': [
            'templates/*/*.html',
            'templates/control/2fa/*.html',
            'templates/modcontrol/spamqueue/*.html',
        ],
    },
)

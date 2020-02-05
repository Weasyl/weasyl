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
    ],
    package_data={
        'weasyl': [
            'templates/*/*.html',
            'templates/control/2fa/*.html',
            'templates/modcontrol/spamqueue/*.html',
        ],
    },
)

from setuptools import setup

setup(
    name='weasyl',
    packages=['weasyl', 'weasyl.controllers'],
    package_data={
        'weasyl': ['templates/**/*.html'],
    },
)

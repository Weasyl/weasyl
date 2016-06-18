import os

from setuptools import setup


here = os.path.dirname(os.path.abspath(__file__))


setup(
    name='wzl',
    description='Weasyl development tooling',
    author='Weasyl LLC',
    py_modules=['wzl'],
    install_requires=[
        'click',
        'toposort',
    ],
    setup_requires=['vcversioner'],
    vcversioner={
        'version_file': os.path.join(here, 'version.txt'),
        # The git repo root is one directory above this setup.py.
        'root': os.path.dirname(here),
    },
    entry_points={'console_scripts': [
        'wzl = wzl:wzl',
    ]},
)

from setuptools import setup


setup(
    name='wzl',
    version='2.0.0',
    description='Weasyl development tooling',
    author='Weasyl LLC',
    py_modules=['wzl'],
    install_requires=[
        'click',
        'toposort',
    ],
    entry_points={'console_scripts': [
        'wzl = wzl:wzl',
    ]},
)

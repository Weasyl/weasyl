#!/usr/bin/env python
import os

from setuptools import setup

# work around the combination of http://bugs.python.org/issue8876 and
# https://www.virtualbox.org/ticket/818 since it doesn't really have ill
# effects and there will be a lot of virtualbox users.
del os.link


setup(
    name='libweasyl',
    description='common code across weasyl projects',
    author='Weasyl LLC',
    packages=[
        'libweasyl', 'libweasyl.models',
        'libweasyl.test', 'libweasyl.models.test',
    ],
    package_data={
        'libweasyl': [
            'alembic/*.py', 'alembic/versions/*.py',
            'test/data/*',
        ],
    },
    install_requires=[
        'alembic==0.9.10',
        'anyjson==0.3.3',
        'arrow==0.12.1',
        'bcrypt==3.1.4',
        'dogpile.cache==0.6.6',
        'lxml==4.2.3',
        'misaka==1.0.3+weasyl.6',    # https://github.com/Weasyl/misaka
        'oauthlib==2.0.4',
        'psycopg2cffi==2.7.7',
        'pytz==2018.4',
        'pyyaml==3.12',
        'sanpera==0.1.1+weasyl.6',   # https://github.com/Weasyl/sanpera
        'sqlalchemy==1.2.8',
        'translationstring==1.3',
        'backports.lzma==0.0.11;python_version<"3.3"',
        'enum34==1.1.6;python_version<"3.4"',
    ],
    extras_require={
        'development': [
            'coverage',
            'flake8',
            'pytest',
            'sphinx',
            'sphinxcontrib-napoleon',
            'tox',
        ],
    },
)

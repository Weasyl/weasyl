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
        'alembic==1.3.2',
        'anyjson==0.3.3',
        'arrow==0.15.2',
        'bcrypt==3.1.7',
        'dogpile.cache==0.9.0',
        'lxml==4.4.2',
        'misaka==1.0.3+weasyl.6',    # https://github.com/Weasyl/misaka
        'oauthlib==2.1.0',
        'Pillow==6.2.1',
        'psycopg2cffi==2.7.7',
        'pyramid~=1.10.4',
        'pytz==2019.3',
        'sanpera==0.1.1+weasyl.6',   # https://github.com/Weasyl/sanpera
        'sqlalchemy==1.3.12',
        'translationstring==1.3',
        'backports.lzma==0.0.12;python_version<"3.3"',
        'enum34==1.1.6;python_version<"3.4"',
    ],
    extras_require={
        'development': [
            'coverage==5.0.1',
            'flake8',
            'pytest==4.6.8',
            'tox',
        ],
    },
)

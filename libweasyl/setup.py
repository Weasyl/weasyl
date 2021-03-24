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
            'alembic/*.py', 'alembic/script.py.mako', 'alembic/versions/*.py',
            'test/data/*',
        ],
    },
    install_requires=[
        'alembic==1.5.8',
        'arrow==1.0.3',
        'bcrypt==3.2.0',
        'dogpile.cache==0.9.2',
        'lxml==4.6.2',
        'misaka==1.0.3+weasyl.6',    # https://github.com/Weasyl/misaka
        'oauthlib==2.1.0',
        'Pillow==8.1.2',
        'psycopg2cffi==2.9.0',
        'pyramid~=2.0',
        'pytz==2020.4',
        'sanpera==0.1.1+weasyl.6',   # https://github.com/Weasyl/sanpera
        'sqlalchemy==1.3.20',
    ],
)

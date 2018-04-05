#!/usr/bin/env python
import os
import sys

from setuptools import setup
from pip.download import PipSession
from pip.req import parse_requirements

# work around the combination of http://bugs.python.org/issue8876 and
# https://www.virtualbox.org/ticket/818 since it doesn't really have ill
# effects and there will be a lot of virtualbox users.
del os.link

# As of pip 6, parse_requirements requires a 'session' argument. This is required
# for remote files, but not local ones. In prior versions of pip, a blank
# PipSession object was used if no 'session' object was passed.
reqs = [str(r.req) for r in parse_requirements('requirements.txt', session=PipSession()) if r.req is not None]

if sys.version_info < (3, 3):
    reqs.append('backports.lzma')

if sys.version_info < (3, 4):
    reqs.append('enum34')


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
    install_requires=reqs,
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

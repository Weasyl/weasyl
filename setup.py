import os

from setuptools import setup
from pip.download import PipSession
from pip.req import parse_requirements

from weasyl._version import __version__


here = os.path.dirname(os.path.abspath(__file__))

# As of pip 6, parse_requirements requires a 'session' argument. This is required
# for remote files, but not local ones. In prior versions of pip, a blank
# PipSession object was used if no 'session' object was passed.
reqs = [str(r.req)
        for r in parse_requirements(
            os.path.join(here, 'etc', 'requirements.txt'),
            session=PipSession())
        if r.req is not None]


setup(
    name='weasyl',
    version=__version__,
    description='https://www.weasyl.com/',
    author='Weasyl LLC',
    packages=[
        'weasyl', 'weasyl.controllers',
        'weasyl.migration', 'weasyl.test',
    ],
    include_package_data=True,
    install_requires=reqs,
)

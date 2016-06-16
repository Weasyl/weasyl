import os

from setuptools import setup
from pip.download import PipSession
from pip.req import parse_requirements


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
    description='https://www.weasyl.com/',
    author='Weasyl LLC',
    packages=[
        'weasyl', 'weasyl.controllers',
        'weasyl.migration', 'weasyl.test',
    ],
    include_package_data=True,
    install_requires=reqs,
    setup_requires=['vcversioner'],
    vcversioner={
        'version_module_paths': ['weasyl/_version.py'],
        'root': here,
    },
    entry_points={'console_scripts': [
        'wzl = weasyl.wzl:wzl',
    ]},
)

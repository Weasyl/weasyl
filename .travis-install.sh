#!/bin/sh -eux
weasyl_reqs='-r etc/requirements.txt -c etc/requirements.txt -e .'
make setup
pip install -U $weasyl_reqs -e './libweasyl[development]' codecov==2.0.15 pytest-cov==2.7.1

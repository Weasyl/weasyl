#!/bin/sh -eux
if [ "$(python -V 2>&1)" ">" "Python 3" ]; then
    weasyl_reqs='-c etc/requirements.txt'
else
    weasyl_reqs='-r etc/requirements.txt -c etc/requirements.txt -e .'
    make setup
fi
pip install -U $weasyl_reqs -e './libweasyl[development]' codecov==2.0.15 pytest-cov==2.7.1

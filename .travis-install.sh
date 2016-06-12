#!/bin/sh -eux
if [ "$(python -V 2>&1)" ">" "Python 3" ]; then
    weasyl_reqs=
else
    weasyl_reqs='-r etc/requirements.txt -c etc/requirements.txt'
fi
pip install -U $weasyl_reqs -e './libweasyl[development]' codecov pytest-cov

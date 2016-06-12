#!/bin/sh -eux
py.test --cov=libweasyl/libweasyl libweasyl/libweasyl
if [ "$(python -V)" ">" "Python 3" ]; then
    :
else
    WEASYL_ROOT=$(pwd) py.test --cov-append --cov=weasyl weasyl/test
fi

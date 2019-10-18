#!/bin/sh -eux
py.test --cov=libweasyl/libweasyl libweasyl/libweasyl
WEASYL_APP_ROOT=. WEASYL_STORAGE_ROOT=testing py.test --cov-append --cov=weasyl weasyl/test

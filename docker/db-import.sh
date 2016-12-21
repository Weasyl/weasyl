#!/bin/sh
createdb "-U${POSTGRES_USER}" -E UTF8 weasyl
createdb "-U${POSTGRES_USER}" -E UTF8 weasyl_test
psql "-U${POSTGRES_USER}" weasyl -c 'CREATE EXTENSION hstore;'
curl https://deploy.weasyldev.com/weasyl-latest-staff.sql.xz \
    | xz -dc \
    | psql "-U${POSTGRES_USER}" weasyl

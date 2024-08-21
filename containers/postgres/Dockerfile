FROM docker.io/library/postgres:13-alpine3.16
COPY \
    00-hstore.sql \
    01-test.sql \
    02-weasyl-latest-staff.sql.gz \
    /docker-entrypoint-initdb.d/

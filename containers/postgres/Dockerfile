FROM docker.io/library/postgres:12
COPY \
    00-hstore.sql \
    01-test.sql \
    02-weasyl-latest-staff.sql.gz \
    /docker-entrypoint-initdb.d/

FROM docker.io/library/postgres:18-alpine3.24 AS test
COPY --link \
    00-test.sql \
    /docker-entrypoint-initdb.d/


FROM docker.io/library/postgres:18-alpine3.24
COPY --link \
    00-hstore.sql \
    02-weasyl-latest-staff.sql.gz \
    /docker-entrypoint-initdb.d/

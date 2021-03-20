# syntax=docker/dockerfile:experimental
FROM node:15-alpine AS assets
RUN apk add --update sassc
WORKDIR /weasyl-build
RUN chown node:node /weasyl-build
USER node
COPY package.json package-lock.json ./
RUN npm install --no-save --ignore-scripts
COPY build.js build.js
COPY assets assets
RUN node build.js


FROM python:3.9-alpine3.13 AS bdist-lxml
# libxml2-dev, libxslt-dev: lxml
RUN apk add --update \
    musl-dev gcc make \
    libxml2-dev libxslt-dev
RUN adduser -S build -h /weasyl-build -u 1000
WORKDIR /weasyl-build
USER build
COPY requirements/lxml.txt lxml.txt
RUN --mount=type=cache,id=pip,target=/weasyl-build/.cache/pip,sharing=private,uid=1000 pip wheel -w dist -r lxml.txt


FROM python:3.9-alpine3.13 AS bdist
# imagemagick6-dev: sanpera
# libjpeg-turbo-dev, libwebp-dev, zlib-dev: Pillow
# libffi-dev, openssl-dev: cryptography
# libmemcached-dev: pylibmc
# postgresql-dev: psycopg2cffi
RUN apk add --update \
    musl-dev gcc make \
    imagemagick6-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    libmemcached-dev \
    libwebp-dev \
    openssl-dev \
    postgresql-dev \
    zlib-dev
RUN adduser -S build -h /weasyl-build -u 1000
WORKDIR /weasyl-build
USER build
COPY etc/requirements.txt requirements.txt
RUN --mount=type=cache,id=pip,target=/weasyl-build/.cache/pip,sharing=private,uid=1000 pip wheel -w dist -r requirements.txt


FROM python:3.9-alpine3.13 AS bdist-pytest
RUN adduser -S build -h /weasyl-build -u 1000
WORKDIR /weasyl-build
USER build
COPY requirements/test.txt test.txt
RUN --mount=type=cache,id=pip,target=/weasyl-build/.cache/pip,sharing=private,uid=1000 pip wheel -w dist -c test.txt pytest


FROM python:3.9-alpine3.13 AS package
RUN apk add --update \
    imagemagick6-libs \
    libffi \
    libjpeg-turbo \
    libmemcached-libs \
    libwebp \
    libxslt \
    postgresql-dev
RUN adduser -S weasyl -h /weasyl
WORKDIR /weasyl
USER weasyl
RUN python3 -m venv .venv
COPY etc/requirements.txt etc/requirements.txt

RUN --mount=type=bind,target=install-wheels,source=/weasyl-build/dist,from=bdist-lxml .venv/bin/pip install --no-deps install-wheels/*
RUN --mount=type=bind,target=install-wheels,source=/weasyl-build/dist,from=bdist .venv/bin/pip install --no-deps install-wheels/*

COPY --chown=weasyl:nobody libweasyl libweasyl
RUN .venv/bin/pip install --no-deps -e libweasyl

COPY --chown=weasyl:nobody setup.py setup.py
COPY --chown=weasyl:nobody weasyl weasyl
RUN .venv/bin/pip install --no-deps -e .

COPY --from=assets /weasyl-build/build build

ARG version
RUN test -n "$version" && printf '%s\n' "$version" > version.txt

FROM package AS test
RUN --mount=type=bind,target=install-wheels,source=/weasyl-build/dist,from=bdist-pytest .venv/bin/pip install --no-deps install-wheels/*
ENV WEASYL_APP_ROOT=.
ENV WEASYL_STORAGE_ROOT=testing/storage
ENV PATH="/weasyl/.venv/bin:${PATH}"
COPY pytest.ini .coveragerc ./
COPY assets assets
CMD pytest -x libweasyl.test libweasyl.models.test && pytest -x weasyl.test

FROM package
ENV WEASYL_APP_ROOT=/weasyl
ENV WEASYL_WEB_ENDPOINT=tcp:8080
CMD [".venv/bin/twistd", "--nodaemon", "--python=weasyl/weasyl.tac", "--pidfile=/tmp/twistd.pid"]
EXPOSE 8080
STOPSIGNAL SIGINT

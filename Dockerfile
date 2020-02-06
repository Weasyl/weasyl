# syntax=docker/dockerfile:experimental
FROM node:13-alpine AS assets
RUN apk add --update sassc
WORKDIR /weasyl-build
RUN chown node:node /weasyl-build
USER node
COPY package.json package-lock.json ./
RUN npm install --ignore-scripts
COPY build.js build.js
COPY assets assets
RUN node build.js


FROM python:2.7-alpine3.11 AS bdist-lxml
# libxml2-dev, libxslt-dev: lxml
RUN apk add --update \
    musl-dev gcc make \
    libxml2-dev libxslt-dev
RUN adduser -S build -h /weasyl-build -u 100
WORKDIR /weasyl-build
USER build
RUN --mount=type=cache,id=pip,target=/weasyl-build/.cache/pip,sharing=private,uid=100 pip2 wheel -w dist lxml==4.5.0


FROM python:2.7-alpine3.11 AS bdist
# imagemagick6-dev: sanpera
# libjpeg-turbo-dev, libwebp-dev, zlib-dev: Pillow
# libffi-dev, openssl-dev: cryptography
# libmemcached-dev: pylibmc
# postgresql-dev: psycopg2cffi
# xz-dev: backports.lzma
RUN apk add --update \
    musl-dev gcc make \
    imagemagick6-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    libmemcached-dev \
    libwebp-dev \
    openssl-dev \
    postgresql-dev \
    xz-dev \
    zlib-dev
RUN adduser -S build -h /weasyl-build -u 100
WORKDIR /weasyl-build
USER build
COPY etc/requirements.txt requirements.txt
RUN --mount=type=cache,id=pip,target=/weasyl-build/.cache/pip,sharing=private,uid=100 pip2 wheel -w dist -r requirements.txt
COPY --chown=build:nobody libweasyl libweasyl
RUN cd libweasyl && python2 setup.py bdist_wheel -d ../dist2
COPY setup.py setup.py
COPY weasyl weasyl
RUN python2 setup.py bdist_wheel -d dist2


FROM python:2.7-alpine3.11 AS bdist-pytest
RUN adduser -S build -h /weasyl-build -u 100
WORKDIR /weasyl-build
USER build
RUN --mount=type=cache,id=pip,target=/weasyl-build/.cache/pip,sharing=private,uid=100 pip2 wheel -w dist pytest==4.6.5


FROM python:2.7-alpine3.11 AS package
RUN apk add --update \
    py3-virtualenv \
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
RUN virtualenv -p python2 .venv
COPY etc/requirements.txt etc/requirements.txt

RUN --mount=type=bind,target=install-wheels,source=/weasyl-build/dist,from=bdist-lxml .venv/bin/pip install --no-deps install-wheels/*
RUN --mount=type=bind,target=install-wheels,source=/weasyl-build/dist,from=bdist .venv/bin/pip install --no-deps install-wheels/*

RUN --mount=type=bind,target=install-wheels,source=/weasyl-build/dist2,from=bdist [".venv/bin/pip", "install", "--no-deps", \
    "install-wheels/libweasyl-0.0.0-py2-none-any.whl", \
    "install-wheels/weasyl-0.0.0-py2-none-any.whl"]

COPY --from=assets /weasyl-build/build build
COPY static static

COPY weasyl/weasyl.tac ./

ARG version
RUN test -n "$version" && printf '%s\n' "$version" > version.txt

FROM package AS test
RUN --mount=type=bind,target=install-wheels,source=/weasyl-build/dist,from=bdist-pytest .venv/bin/pip install --no-deps install-wheels/*
ENV WEASYL_APP_ROOT=.
ENV WEASYL_STORAGE_ROOT=testing/storage
ENV PATH="/weasyl/.venv/bin:${PATH}"
COPY pytest.ini ./
CMD pytest -x libweasyl.test && pytest -x weasyl.test

FROM package
ENV WEASYL_APP_ROOT=/weasyl
ENV WEASYL_WEB_ENDPOINT=tcp:8080
ENV WEASYL_SERVE_STATIC_FILES=y
CMD [".venv/bin/twistd", "--nodaemon", "--python=weasyl.tac", "--pidfile=/tmp/twistd.pid"]
EXPOSE 8080
STOPSIGNAL SIGINT

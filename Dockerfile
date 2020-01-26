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
RUN adduser -S build -h /weasyl-build
WORKDIR /weasyl-build
USER build
RUN pip2 wheel -w dist lxml==4.4.2


FROM python:2.7-alpine3.11 AS bdist
# imagemagick6-dev: sanpera
# libjpeg-turbo-dev, libwebp-dev, zlib-dev: Pillow
# libffi-dev, openssl-dev: cryptography
# postgresql-dev: psycopg2cffi
# xz-dev: backports.lzma
RUN apk add --update \
    musl-dev gcc make \
    imagemagick6-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    libwebp-dev \
    openssl-dev \
    postgresql-dev \
    xz-dev \
    zlib-dev
RUN adduser -S build -h /weasyl-build
WORKDIR /weasyl-build
USER build
RUN pip2 wheel -w dist Pillow==6.2.2
RUN pip2 wheel -w dist --index-url https://pypi.weasyl.dev/ sanpera==0.1.1+weasyl.6
RUN pip2 wheel -w dist cryptography==2.8
RUN pip2 wheel -w dist psycopg2cffi==2.7.7
RUN pip2 wheel -w dist Twisted[tls]==19.10.0
RUN pip2 wheel -w dist bcrypt==3.1.7
RUN pip2 wheel -w dist --index-url https://pypi.weasyl.dev/ misaka==1.0.3+weasyl.6
RUN pip2 wheel -w dist backports.lzma==0.0.12
COPY --chown=build:nobody libweasyl libweasyl
RUN cd libweasyl && python2 setup.py bdist_wheel -d ../dist2
COPY setup.py setup.py
COPY weasyl weasyl
RUN python2 setup.py bdist_wheel -d dist2


FROM python:2.7-alpine3.11
RUN apk add --update \
    py3-virtualenv \
    imagemagick6 \
    libffi \
    libjpeg-turbo \
    libwebp \
    libxslt \
    postgresql-dev
RUN adduser -S weasyl -h /weasyl
WORKDIR /weasyl
USER weasyl
RUN virtualenv -p python2 .venv
COPY etc/requirements.txt etc/requirements.txt

COPY --from=bdist-lxml /weasyl-build/dist install-wheels/
COPY --from=bdist /weasyl-build/dist install-wheels/
RUN .venv/bin/pip install --no-deps install-wheels/*

RUN .venv/bin/pip install -r etc/requirements.txt --index-url https://pypi.weasyl.dev/ --extra-index-url https://pypi.org/simple/

COPY --from=bdist \
    /weasyl-build/dist2/libweasyl-0.0.0-py2-none-any.whl \
    /weasyl-build/dist2/weasyl-0.0.0-py2-none-any.whl \
    install-wheels/
RUN .venv/bin/pip install --no-deps \
    install-wheels/libweasyl-0.0.0-py2-none-any.whl \
    install-wheels/weasyl-0.0.0-py2-none-any.whl

COPY --from=assets /weasyl-build/build build
COPY static static

COPY weasyl/weasyl.tac ./

ARG version
RUN test -n "$version" && printf '%s\n' "$version" > version.txt

ENV WEASYL_APP_ROOT=/weasyl
ENV WEASYL_WEB_ENDPOINT=tcp:8080
ENV WEASYL_SERVE_STATIC_FILES=y
CMD [".venv/bin/twistd", "--nodaemon", "--python=weasyl.tac", "--pidfile=/tmp/twistd.pid"]
EXPOSE 8080
STOPSIGNAL SIGINT

# syntax=docker/dockerfile:1
FROM docker.io/library/node:16-alpine3.16 AS asset-builder
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    sassc runit
WORKDIR /weasyl-build
RUN chown node:node /weasyl-build
USER node
COPY package.json package-lock.json ./
RUN --mount=type=cache,id=npm,target=/home/node/.npm/_cacache,uid=1000 npm ci --no-audit --ignore-scripts
COPY build.js build.js


FROM asset-builder AS assets
COPY assets assets
RUN node build.js


FROM docker.io/library/alpine:3.16 AS mozjpeg
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    musl-dev gcc make \
    cmake nasm
RUN adduser -S build -h /mozjpeg-build
WORKDIR /mozjpeg-build
USER build
RUN wget https://github.com/mozilla/mozjpeg/archive/refs/tags/v4.0.3.tar.gz
RUN echo '59c2d65af28d4ef68b9e5c85215cf3b26f4ac5c98e3ae76ba5febceec97fa5ab28cc13496e3f039f11cae767c5466bbf798038f83b310134c13d2e9a6bf5467e  v4.0.3.tar.gz' | sha512sum -c && tar xf v4.0.3.tar.gz
WORKDIR /mozjpeg-build/mozjpeg-4.0.3
RUN cmake -DENABLE_STATIC=0 -DPNG_SUPPORTED=0 -DCMAKE_INSTALL_PREFIX=/mozjpeg-build/package-root .
RUN cmake --build . --parallel --target install


FROM docker.io/library/python:3.10-alpine3.16 AS bdist
# imagemagick6-dev: sanpera
# libjpeg-turbo-dev, libwebp-dev, zlib-dev: Pillow
# libffi-dev, openssl-dev: cryptography
# libmemcached-dev: pylibmc
# libxml2-dev, libxslt-dev: lxml
# postgresql-dev: psycopg2cffi
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    musl-dev gcc g++ make \
    imagemagick6-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    libmemcached-dev \
    libwebp-dev \
    libxml2-dev libxslt-dev \
    openssl-dev \
    postgresql-dev \
    zlib-dev
RUN adduser -S weasyl -h /weasyl -u 1000
WORKDIR /weasyl
USER weasyl
COPY --from=mozjpeg --chown=root:root /mozjpeg-build/package-root/include/ /usr/include/
COPY --from=mozjpeg --chown=root:root /mozjpeg-build/package-root/lib64/ /usr/lib/
COPY poetry-requirements.txt ./
RUN --network=none python3 -m venv .poetry-venv
RUN --mount=type=cache,id=pip,target=/weasyl/.cache/pip,sharing=locked,uid=1000 \
    .poetry-venv/bin/pip install --require-hashes --only-binary :all: -r poetry-requirements.txt
RUN --network=none python3 -m venv .venv
COPY --chown=weasyl pyproject.toml poetry.lock setup.py ./
RUN --network=none .poetry-venv/bin/poetry lock --check
RUN --mount=type=cache,id=poetry,target=/weasyl/.cache/pypoetry,sharing=locked,uid=1000 \
    .poetry-venv/bin/poetry install --only=main --no-root
RUN dirs=' \
        libweasyl/models/test \
        libweasyl/test \
        weasyl/controllers \
        weasyl/test/login \
        weasyl/test/resetpassword \
        weasyl/test/useralias \
        weasyl/test/web \
    '; \
    mkdir -p $dirs \
    && for dir in $dirs; do touch "$dir/__init__.py"; done
RUN .poetry-venv/bin/poetry install --only-root


FROM bdist AS bdist-pytest
RUN --mount=type=cache,id=poetry,target=/weasyl/.cache/pypoetry,sharing=locked,uid=1000 \
    .poetry-venv/bin/poetry install --only=dev


FROM docker.io/library/python:3.10-alpine3.16 AS package
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    imagemagick6-libs \
    libffi \
    libmemcached-libs \
    libpq \
    libwebp \
    libxslt
RUN adduser -S weasyl -h /weasyl
WORKDIR /weasyl
USER weasyl
COPY --from=mozjpeg --chown=root:root /mozjpeg-build/package-root/lib64/ /usr/lib/

COPY --from=bdist /weasyl/.venv .venv
COPY --from=assets /weasyl-build/build build
COPY --chown=weasyl:root libweasyl libweasyl
COPY --chown=weasyl:root weasyl weasyl

ARG version
RUN test -n "$version" && printf '%s\n' "$version" > version.txt

FROM package AS test
COPY --from=bdist-pytest /weasyl/.venv .venv
RUN mkdir .pytest_cache coverage \
    && ln -s /run/config config
ENV WEASYL_APP_ROOT=.
ENV WEASYL_STORAGE_ROOT=testing/storage
ENV PATH="/weasyl/.venv/bin:${PATH}"
COPY pytest.ini .coveragerc ./
COPY assets assets
CMD pytest -x libweasyl.test libweasyl.models.test && pytest -x weasyl.test
STOPSIGNAL SIGINT

FROM docker.io/library/alpine:3.16 AS flake8
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    py3-flake8
RUN adduser -S weasyl -h /weasyl
WORKDIR /weasyl
USER weasyl
STOPSIGNAL SIGINT
ENTRYPOINT ["/usr/bin/flake8"]
COPY . .

FROM package
RUN mkdir storage storage/log storage/static storage/profile-stats \
    && ln -s /run/config config
ENV WEASYL_APP_ROOT=/weasyl
ENV PORT=8080
CMD [".venv/bin/gunicorn"]
EXPOSE 8080
COPY gunicorn.conf.py ./

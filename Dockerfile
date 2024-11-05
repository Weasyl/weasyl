# syntax=docker/dockerfile:1
FROM docker.io/library/node:16-alpine3.16 AS asset-builder
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    sassc runit
WORKDIR /weasyl-build
RUN chown node:node /weasyl-build
USER node
COPY --chown=node:node package.json package-lock.json ./
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
RUN wget https://github.com/mozilla/mozjpeg/archive/refs/tags/v4.1.5.tar.gz
RUN echo '90e1b0067740b161398d908e90b976eccc2ee7174496ce9693ba3cdf4727559ecff39744611657d847dd83164b80993152739692a5233aca577ebd052efaf501  v4.1.5.tar.gz' | sha512sum -c && tar xf v4.1.5.tar.gz
WORKDIR /mozjpeg-build/mozjpeg-4.1.5
RUN cmake -DENABLE_STATIC=0 -DPNG_SUPPORTED=0 -DCMAKE_INSTALL_PREFIX=/mozjpeg-build/package-root .
RUN cmake --build . --parallel --target install


FROM docker.io/library/alpine:3.20 AS imagemagick6-build
RUN --network=none adduser -S build -h /imagemagick6-build
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    musl-dev gcc make \
    lcms2-dev \
    libpng-dev \
    libxml2-dev \
    libwebp-dev \
    zlib-dev
WORKDIR /imagemagick6-build
COPY --from=mozjpeg --chown=root:root /mozjpeg-build/package-root/include/ /usr/include/
COPY --from=mozjpeg --chown=root:root /mozjpeg-build/package-root/lib64/ /usr/lib/
USER build
RUN wget https://imagemagick.org/archive/releases/ImageMagick-6.9.13-17.tar.xz
RUN --network=none echo '655d8faa4387fd840e2a082633f55d961b3f6bb3c4909debec8272e7abbf9da4afb9994628a493229b41cbc17baba765812cf3d02fc69dd0eb2f2511e85b31c0  ImageMagick-6.9.13-17.tar.xz' | sha512sum -c && xzcat ImageMagick-6.9.13-17.tar.xz | tar x
WORKDIR /imagemagick6-build/ImageMagick-6.9.13-17
# `CFLAGS`, `LDFLAGS`: abuild defaults with `-O2` instead of `-Os`, as used by Alpine 3.16 imagemagick6 package
# no `--enable-hdri`: doesn’t seem to work with sanpera, even though we’re building it from source?
# `--with-cache=32GiB`: let other places (like policy.xml) set the limit, and definitely don’t choose whether to write files based on detecting available memory
# `--with-xml`: for XMP metadata
RUN --network=none ./configure \
    --prefix=/usr \
    --with-security-policy=websafe \
    --disable-static \
    --enable-shared \
    --disable-deprecated \
    --disable-docs \
    --disable-cipher \
    --with-cache=32GiB \
    --without-magick-plus-plus \
    --without-perl \
    --without-bzlib \
    --without-dps \
    --without-djvu \
    --without-flif \
    --without-freetype \
    --without-heic \
    --without-jbig \
    --without-openjp2 \
    --without-lqr \
    --without-lzma \
    --without-openexr \
    --without-pango \
    --without-raw \
    --without-raqm \
    --without-tiff \
    --without-wmf \
    --with-xml \
    --without-x \
    --without-zstd \
    CFLAGS='-O2 -fstack-clash-protection -Wformat -Werror=format-security' \
    LDFLAGS='-Wl,--as-needed,-O1,--sort-common'
RUN --network=none make -j"$(nproc)"
RUN --network=none make install DESTDIR="$HOME/package-root"


FROM docker.io/library/python:3.10-alpine3.16 AS bdist
# libwebp-dev, zlib-dev: Pillow
# libffi-dev, openssl-dev: cryptography
# libmemcached-dev: pylibmc
# libxml2-dev, libxslt-dev: lxml
# postgresql-dev: psycopg2
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    musl-dev gcc g++ make \
    libffi-dev \
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
COPY --from=imagemagick6-build --chown=root:root /imagemagick6-build/package-root/ /
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
# gcc (libgomp), lcms2, libpng, libxml2, libwebp: ImageMagick
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    gcc lcms2 libpng libxml2 libwebp \
    libffi \
    libmemcached-libs \
    libpq \
    libwebp \
    libxslt
RUN adduser -S weasyl -h /weasyl
WORKDIR /weasyl
USER weasyl
COPY --from=mozjpeg --chown=root:root /mozjpeg-build/package-root/lib64/ /usr/lib/
COPY --from=imagemagick6-build --chown=root:root /imagemagick6-build/package-root/ /
COPY --chown=root:root imagemagick-policy.xml /usr/etc/ImageMagick-6/policy.xml

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

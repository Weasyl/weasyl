# syntax=docker/dockerfile:1
FROM docker.io/denoland/deno:2.8.1@sha256:ddaad47cbbbbd856d73bd0d50074a0e308c51671d83442eebb15f1039dd4a822 AS asset-builder

# bypass redundant `/tini` and `_entry.sh`
ENTRYPOINT []

WORKDIR /weasyl-build
RUN mkdir /weasyl-assets && chown 1000:1000 /weasyl-build /weasyl-assets
USER 1000

COPY --chown=1000 --link deno.json deno.lock ./

# initial `--vendor=false` install allows non-`node_modules` packages to be installed to (and therefore from) cache
# hash + patch: https://github.com/postcss/autoprefixer/pull/1550
RUN --mount=type=cache,id=deno,target=/deno-dir,uid=1000 \
    deno install --frozen --vendor=false && deno ci \
    && sha256sum -c <<'SHA256' \
    && sed -i -f - node_modules/autoprefixer/lib/supports.js <<'SED'
68c4208ae3e1aad176f61fe7ba27d351d8b8f931dad1b3938702c3bb80106d24  node_modules/autoprefixer/lib/supports.js
SHA256
214a\
, this.all.browsers.browserslistOpts
SED

COPY --link build.ts build-css.ts ./


FROM asset-builder AS assets
COPY --chown=1000 --link assets assets
RUN --network=none mkdir build && deno run \
    --cached-only \
    --frozen \
    --allow-env \
    --allow-read \
    --allow-write \
    --allow-run \
    build.ts \
    --assets=./assets/ \
    --output=./build/


FROM docker.io/library/alpine:3.24 AS mozjpeg-src
RUN --network=none adduser -S build -h /mozjpeg-build
USER build
WORKDIR /mozjpeg-build
ADD --checksum=sha256:9fcbb7171f6ac383f5b391175d6fb3acde5e64c4c4727274eade84ed0998fcc1 --chown=100 --link https://github.com/mozilla/mozjpeg/archive/refs/tags/v4.1.5.tar.gz ./
RUN tar xf v4.1.5.tar.gz


FROM docker.io/library/alpine:3.24 AS mozjpeg
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    musl-dev gcc make \
    cmake nasm
RUN adduser -S build -h /mozjpeg-build
USER build
WORKDIR /mozjpeg-build/build
RUN --mount=type=bind,from=mozjpeg-src,source=/mozjpeg-build/mozjpeg-4.1.5,target=/mozjpeg-build/mozjpeg \
    cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DENABLE_STATIC=0 -DPNG_SUPPORTED=0 -DCMAKE_INSTALL_PREFIX=/mozjpeg-build/package-root -S ../mozjpeg -B . \
    && cmake --build . --parallel --target install


FROM docker.io/library/alpine:3.24 AS imagemagick-src
RUN --network=none adduser -S build -h /imagemagick-build
USER build
WORKDIR /imagemagick-build
ADD --checksum=sha256:ea9006be742bef04af734ffc6c641f68a511221a97f40ba61dba8f9a356cfd0d --chown=100 --link https://github.com/ImageMagick/ImageMagick/releases/download/7.1.2-33/ImageMagick-7.1.2-33.tar.xz ./
RUN --network=none tar xf ImageMagick-7.1.2-33.tar.xz


FROM docker.io/library/alpine:3.24 AS imagemagick-build
RUN --network=none adduser -S build -h /imagemagick-build
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    apk add \
    musl-dev gcc make \
    lcms2-dev \
    libpng-dev \
    libwebp-dev
USER build
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/include/ /usr/include/
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/lib64/ /usr/lib/
WORKDIR /imagemagick-build/ImageMagick
# `CFLAGS`, `LDFLAGS`: abuild defaults with `-O2` instead of `-Os`, as used by Alpine 3.24 imagemagick package
# `--with-cache=32GiB`: let other places (like policy.xml) set the limit, and definitely don’t choose whether to write files based on detecting available memory
RUN \
    --mount=type=bind,from=imagemagick-src,source=/imagemagick-build/ImageMagick-7.1.2-33,target=/imagemagick-build/ImageMagick,rw \
    --network=none \
    ./configure \
    --prefix=/usr \
    --with-security-policy=secure \
    --disable-static \
    --enable-shared \
    --disable-deprecated \
    --disable-docs \
    --disable-cipher \
    --disable-dpc \
    --disable-pipes \
    --with-cache=32GiB \
    --without-magick-plus-plus \
    --without-perl \
    --without-utilities \
    --without-bzlib \
    --without-djvu \
    --without-dmr \
    --without-dps \
    --without-flif \
    --without-fontconfig \
    --without-freetype \
    --without-heic \
    --without-jbig \
    --without-jxl \
    --without-lqr \
    --without-lzma \
    --without-openexr \
    --without-openjp2 \
    --without-pango \
    --without-raqm \
    --without-raw \
    --without-tiff \
    --without-wmf \
    --without-xml \
    --without-x \
    --without-zip \
    --without-zstd \
    --with-lcms \
    --with-jpeg \
    --with-png \
    --with-webp \
    CFLAGS='-O2 -fstack-clash-protection -Wformat -Werror=format-security' \
    LDFLAGS='-Wl,--as-needed,-O1,--sort-common' \
    && make -j"$(nproc)" \
    && make install DESTDIR="$HOME/package-root"


FROM docker.io/library/alpine:3.24 AS badgr-build
RUN --network=none adduser -S build -h /badgr -u 1000
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    musl-dev linux-headers gcc meson \
    libseccomp-dev \
    imagemagick-dev \
    lcms2-dev
COPY --link badgr/ /badgr/src/
USER 1000
WORKDIR /badgr/build/
RUN --network=none \
    meson setup --buildtype=release ./ ../src/ \
    && meson compile


FROM docker.io/library/alpine:3.24 AS badgr
RUN --network=none adduser -S badgr -h /badgr -u 1000
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    busybox-extras \
    libseccomp \
    lcms2 \
    libgcc libgomp libpng libwebpmux libwebpdemux
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/include/ /usr/include/
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/lib64/ /usr/lib/
COPY --from=imagemagick-build --chown=root:root --link /imagemagick-build/package-root/ /
COPY --from=badgr-build --chown=root:root --link /badgr/build/badgr-worker /badgr/build/badgr-init /usr/local/bin/
COPY --chown=root:root --link imagemagick-policy.xml /usr/etc/ImageMagick-7/policy.xml
USER 1000
CMD ["badgr-init", "tcpsvd", "-E", "::", "27350", "timeout", "-k", "60", "59", "badgr-worker"]
LABEL org.opencontainers.image.source=https://github.com/Weasyl/weasyl


FROM docker.io/library/python:3.10-alpine3.22 AS bdist
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    gcc musl-dev \
    libmemcached-dev zlib-dev \
    libpq-dev
RUN adduser -S weasyl -h /weasyl -u 1000
WORKDIR /weasyl
USER weasyl
COPY --chown=1000 --link poetry-requirements.txt ./
RUN --network=none python3 -m venv --system-site-packages --without-pip .poetry-venv
RUN --mount=type=cache,id=pip,target=/weasyl/.cache/pip,sharing=locked,uid=1000 \
    .poetry-venv/bin/python3 -m pip install --require-hashes --only-binary :all: --no-deps -r poetry-requirements.txt
RUN --network=none python3 -m venv --system-site-packages --without-pip .venv
COPY --chown=1000 --link pyproject.toml poetry.lock setup.py ./
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
        weasyl/util \
    '; \
    mkdir -p $dirs \
    && for dir in $dirs; do touch "$dir/__init__.py"; done
RUN .poetry-venv/bin/poetry install --only-root


FROM bdist AS bdist-pytest
RUN --mount=type=cache,id=poetry,target=/weasyl/.cache/pypoetry,sharing=locked,uid=1000 \
    .poetry-venv/bin/poetry install --only=dev


FROM docker.io/library/python:3.10-alpine3.22 AS package
# libmemcached-libs, zlib: pylibmc
# libpq: psycopg2
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    apk add \
    libmemcached-libs zlib \
    libpq
RUN adduser -S weasyl -h /weasyl -u 1000
WORKDIR /weasyl
USER weasyl
COPY --from=bdist --link /weasyl/.venv .venv
COPY --from=assets --link /weasyl-build/build/rev-manifest.json build/rev-manifest.json
COPY --chown=1000:root --link libweasyl libweasyl
COPY --chown=1000:root --link weasyl weasyl

ARG version
RUN test -n "$version" && printf '%s\n' "$version" > version.txt

FROM package AS test
COPY --from=bdist-pytest --chown=1000 --link /weasyl/.venv .venv
RUN mkdir .pytest_cache coverage \
    && ln -s /run/config config
ENV WEASYL_APP_ROOT=.
ENV WEASYL_STORAGE_ROOT=testing/storage
ENV PATH="/weasyl/.venv/bin:${PATH}"
COPY --link pytest.ini .coveragerc ./
COPY --link assets assets
CMD pytest -x libweasyl.test libweasyl.models.test weasyl.test
STOPSIGNAL SIGINT

FROM docker.io/library/alpine:3.22 AS flake8
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    py3-flake8
RUN adduser -S weasyl -h /weasyl -u 101
WORKDIR /weasyl
USER weasyl

FROM package
RUN mkdir storage storage/log storage/static storage/profile-stats uds-nginx-web \
    && ln -s /run/config config
ENV WEASYL_APP_ROOT=/weasyl
ENV PORT=8080
CMD [".venv/bin/gunicorn"]
EXPOSE 8080
COPY --link gunicorn.conf.py ./

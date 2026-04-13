# syntax=docker/dockerfile:1
FROM docker.io/denoland/deno:alpine-2.3.5 AS asset-builder
WORKDIR /weasyl-build
RUN mkdir /weasyl-assets && chown deno:deno /weasyl-build /weasyl-assets
USER deno

COPY --chown=1000 --link deno.json deno.lock ./

RUN --mount=type=cache,id=deno,target=/deno-dir,uid=1000 deno install --frozen

COPY --link build.ts build.ts


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


FROM docker.io/library/alpine:3.22 AS mozjpeg-src
RUN --network=none adduser -S build -h /mozjpeg-build
USER build
WORKDIR /mozjpeg-build
ADD --checksum=sha256:9fcbb7171f6ac383f5b391175d6fb3acde5e64c4c4727274eade84ed0998fcc1 --chown=100 --link https://github.com/mozilla/mozjpeg/archive/refs/tags/v4.1.5.tar.gz ./
RUN tar xf v4.1.5.tar.gz


FROM docker.io/library/alpine:3.22 AS mozjpeg
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    musl-dev gcc make \
    cmake nasm
RUN adduser -S build -h /mozjpeg-build
USER build
WORKDIR /mozjpeg-build/build
RUN --mount=type=bind,from=mozjpeg-src,source=/mozjpeg-build/mozjpeg-4.1.5,target=/mozjpeg-build/mozjpeg \
    cmake -DENABLE_STATIC=0 -DPNG_SUPPORTED=0 -DCMAKE_INSTALL_PREFIX=/mozjpeg-build/package-root -S ../mozjpeg -B . \
    && cmake --build . --parallel --target install


FROM docker.io/library/alpine:3.22 AS libpng-package
RUN --network=none adduser -S build -h /libpng-build
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    abuild \
    musl-dev gcc make \
    gawk autoconf automake libtool \
    zlib-dev
USER build
WORKDIR /libpng-build/libpng
ADD --checksum=sha256:f7d8bf1601b7804f583a254ab343a6549ca6cf27d255c302c47af2d9d36a6f18 --chown=100 --link https://sourceforge.net/projects/libpng/files/libpng16/1.6.56/libpng-1.6.56.tar.xz/download ./libpng-1.6.56.tar.xz
ADD --checksum=sha256:017c06f75ffed25f6cda9b5369ec6da0ac35a6616adf7abe4222516a0237f37a --chown=100 --link https://sourceforge.net/projects/libpng-apng/files/libpng16/1.6.55/libpng-1.6.55-apng.patch.gz/download ./libpng-1.6.55-apng.patch.gz
# TODO: craft deterministic dummy-abuild.key and copy it in alongside APKBUILD
RUN --network=none openssl genrsa -out dummy-abuild.key 512
COPY --chown=100 --link ./libpng/APKBUILD ./
RUN --network=none \
    PACKAGER_PRIVKEY=/libpng-build/libpng/dummy-abuild.key \
    abuild -P /libpng-build/packages -c verify unpack prepare build rootpkg clean


FROM docker.io/library/alpine:3.22 AS imagemagick6-src
RUN --network=none adduser -S build -h /imagemagick6-build
USER build
WORKDIR /imagemagick6-build
ADD --checksum=sha256:6fcd60539e788a9d51c5a5e59be51e6090cdbcf443b968560d632b4e2c42075c --chown=100 --link https://imagemagick.org/archive/releases/ImageMagick-6.9.13-43.tar.xz ./
RUN tar xf ImageMagick-6.9.13-43.tar.xz


FROM docker.io/library/alpine:3.22 AS imagemagick6-build
RUN --network=none adduser -S build -h /imagemagick6-build
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    zlib-dev
RUN --network=none \
    --mount=type=bind,from=libpng-package,source=/libpng-build/packages/libpng-build/x86_64,target=/run/libpng-packages,ro \
    apk add --no-network --allow-untrusted \
    /run/libpng-packages/libpng-1.6.56-r0.apk \
    /run/libpng-packages/libpng-dev-1.6.56-r0.apk
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    apk add \
    musl-dev gcc make \
    lcms2-dev \
    libxml2-dev \
    libwebp-dev
USER build
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/include/ /usr/include/
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/lib64/ /usr/lib/
WORKDIR /imagemagick6-build/ImageMagick
# `CFLAGS`, `LDFLAGS`: abuild defaults with `-O2` instead of `-Os`, as used by Alpine 3.16 imagemagick6 package
# no `--enable-hdri`: doesn’t seem to work with sanpera, even though we’re building it from source?
# `--with-cache=32GiB`: let other places (like policy.xml) set the limit, and definitely don’t choose whether to write files based on detecting available memory
# `--with-xml`: for XMP metadata
RUN \
    --mount=type=bind,from=imagemagick6-src,source=/imagemagick6-build/ImageMagick-6.9.13-43,target=/imagemagick6-build/ImageMagick,rw \
    --network=none \
    ./configure \
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
    LDFLAGS='-Wl,--as-needed,-O1,--sort-common' \
    && make -j"$(nproc)" \
    && make install DESTDIR="$HOME/package-root"


FROM docker.io/library/python:3.10-alpine3.22 AS bdist
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    gcc musl-dev \
    libmemcached-dev zlib-dev \
    libpq-dev
RUN adduser -S weasyl -h /weasyl -u 1000
WORKDIR /weasyl
USER weasyl
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/include/ /usr/include/
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/lib64/ /usr/lib/
COPY --from=imagemagick6-build --chown=root:root --link /imagemagick6-build/package-root/ /
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
# libgcc, libgomp, lcms2, libpng, libxml2, libwebp*: ImageMagick
# libmemcached-libs, zlib: pylibmc
# libpq: psycopg2
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    zlib
RUN --network=none \
    --mount=type=bind,from=libpng-package,source=/libpng-build/packages/libpng-build/x86_64,target=/run/libpng-packages,ro \
    apk add --no-network --allow-untrusted \
    /run/libpng-packages/libpng-1.6.56-r0.apk
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    apk add \
    libgcc libgomp lcms2 libxml2 libwebpdemux libwebpmux \
    libmemcached-libs \
    libpq
RUN adduser -S weasyl -h /weasyl -u 1000
WORKDIR /weasyl
USER weasyl
COPY --from=mozjpeg --chown=root:root --link /mozjpeg-build/package-root/lib64/ /usr/lib/
COPY --from=imagemagick6-build --chown=root:root --link /imagemagick6-build/package-root/ /
COPY --chown=root:root --link imagemagick-policy.xml /usr/etc/ImageMagick-6/policy.xml

COPY --from=bdist --link /weasyl/.venv .venv
COPY --from=assets --link /weasyl-build/build build
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
CMD pytest -x libweasyl.test libweasyl.models.test && pytest -x weasyl.test
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

## Dependencies

### A network

```shell
docker network create --internal wzlnet
```


### Memcached

```shell
containers/run-memcached
```


### PostgreSQL

```shell
mkdir containers/data
containers/run-postgres
containers/run --network=wzlnet postgres:12 psql -h weasyl-database -U weasyl -c 'CREATE EXTENSION hstore'
containers/run --network=wzlnet postgres:12 psql -h weasyl-database -U weasyl -c 'CREATE DATABASE weasyl_test'
wget https://deploy.weasyldev.com/weasyl-latest-staff.sql.xz
< weasyl-latest-staff.sql.xz | unxz | containers/run --tty=false --network=wzlnet postgres:12 psql -h weasyl-database -U weasyl
```


## Weasyl

### Build

```shell
DOCKER_BUILDKIT=1 docker build -t weasyl --build-arg "version=$(git rev-parse --short HEAD)" .
```

Tag the cached build stages to avoid having them pruned (bdist-lxml is currently very expensive):

```shell
for stage in assets bdist-lxml bdist; do
    DOCKER_BUILDKIT=1 docker build --target=$stage -t weasyl-$stage .
done
```


### Configure

```shell
cp -i config/site.config.txt.example config/site.config.txt
cp -i config/weasyl-staff.example.py config/weasyl-staff.py
cp -i libweasyl/libweasyl/alembic/alembic.ini.example alembic.ini
mkdir -p storage/log
```


### Migrate

```shell
containers/run --network=wzlnet "$(containers/mount alembic.ini)" weasyl env WEASYL_STORAGE_ROOT=/tmp .venv/bin/alembic upgrade head
```


### Run

```shell
containers/run \
    --network=wzlnet \
    --name=weasyl-web \
    --env=WEASYL_STORAGE_ROOT=storage \
    "$(containers/mount --writable storage)" \
    "$(containers/mount config)" \
    weasyl
```


### Test

```shell
DOCKER_BUILDKIT=1 docker build --target=test -t weasyl-test .
containers/run \
    --network=wzlnet \
    --name=weasyl-test \
    --tmpfs=/weasyl/testing \
    "$(containers/mount config)" \
    --env=WEASYL_TEST_SQLALCHEMY_URL=postgresql+psycopg2cffi://weasyl@weasyl-database/weasyl_test \
    weasyl-test
```


## Nginx

```shell
containers/run-nginx
```


# TODO

Merging the existing Docker branch should help with some of these.

- [ ] caching for apk
- [ ] caching for npm
- [X] caching for pip
- [ ] separate build stages for each expensive wheel
- [X] parallel builds
- [ ] elimination of pypi.weasyl.dev
- [ ] requirements.txt as constraints file
- [ ] editable install with bind mount for faster development
- [ ] single configuration file
- [ ] scripts for common commands
- [ ] windows compatibility
- [ ] separate networks for memcached and postgresql?
- [ ] compose, stack, kubernetes, or something. aaaa
- [ ] dns with gvisor if not kubernetes previously
- [ ] build reproduction with github actions
- [ ] rootless
- [ ] allow `pytest libweasyl.test weasyl.test`

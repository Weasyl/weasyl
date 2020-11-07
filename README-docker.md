# Weasyl with Docker

Below are the instructions necessary to set up a Docker environment that will allow development of Weasyl.

## Containers

### Dependencies

The following containers must be set up before Weasyl can begin. Most of the set up is done through scripts in the `container/` directory. All of the commands in this document should be run from the project's root directory.

Note that these scripts **cannot** be run as root or they will fail. If interacting with the Docker daemon requires root access, such as through the `sudo` command, add your user to the `docker` system group, such as with the following command.

```shell
sudo usermod -aG docker $(whoami)
```

Note also that the scripts must be run with the bash shell, however the shebang in the scripts is `/bin/sh`. On some systems, such as Ubuntu, this is a symbolic link to the dash shell, not the bash shell. If this is the case, `/bin/sh` must be linked to `/bin/bash` while the scripts are being used.

#### Setting Up the `/etc/hosts` File

To access the Weasyl site once the Docker containers have been created, the following line must be added to the `/etc/hosts` file on the build machine.

```127.0.0.1    weasyl```

#### A Docker Network

A Docker network is required for all of the containers to communicate with one another. This can be created with the following command.

```shell
docker network create --internal wzlnet
```

#### Memcached

This container is a distributed memory-caching system and is required for the development environment.

```shell
containers/run-memcached
```

#### PostgreSQL

This container performs as the backend database. The commands below will create the postgreSQL container and then populate it with the test database.

```shell
mkdir containers/data
containers/run-postgres
containers/run --network=wzlnet postgres:12 psql -h weasyl-database -U weasyl -c 'CREATE EXTENSION hstore'
containers/run --network=wzlnet postgres:12 psql -h weasyl-database -U weasyl -c 'CREATE DATABASE weasyl_test'
wget https://deploy.weasyldev.com/weasyl-latest-staff.sql.xz
< weasyl-latest-staff.sql.xz unxz | containers/run --tty=false --network=wzlnet postgres:12 psql -h weasyl-database -U weasyl
```

If the above URL for the example staff database does not work, resulting in a HTTP 522 error for instance, try the following command instead.

```wget 'https://s3-us-west-2.amazonaws.com/temporary.weasyl.dev/weasyl-latest-staff.sql.xz'```

### Weasyl

Once the above dependencies have been created, the Weasyl container itself can be created.

#### Build

The following command will build the container specified in the [Dockerfile](Dockerfile). Note that any changes to the Dockerfile will require this step to be repeated.

```shell
DOCKER_BUILDKIT=1 docker build -t weasyl --build-arg "version=$(git rev-parse --short HEAD)" .
```

To ensure that the various containers in the build process are not pruned, tag the cached build stages (bdist-lxml is currently very expensive). This will save time in the event that the containers have to be reconstructed.

```shell
for stage in assets bdist-lxml bdist; do
    DOCKER_BUILDKIT=1 docker build --target=$stage -t weasyl-$stage .
done
```

#### Configure

```shell
cp -i config/site.config.txt.example config/site.config.txt && \
cp -i config/weasyl-staff.example.py config/weasyl-staff.py && \
cp -i libweasyl/libweasyl/alembic/alembic.ini.example alembic.ini && \
mkdir -p storage/log
```

#### Migrate

```shell
containers/run \
    --network=wzlnet \
    "$(containers/mount alembic.ini)" \
    "$(containers/mount libweasyl)" \
    --env=WEASYL_STORAGE_ROOT=/tmp \
    weasyl .venv/bin/alembic upgrade head
```

#### Run

The following command will run the Weasyl image, including all of the backend components, but **not** the web interface. To be able to access the dev Weasyl website, you must run [this section](#NGINX) once the Weasyl image is up and running.

This command will make start the Weasyl process. It will run as an interactive shell tied to the current terminal, and can be terminated with a `Ctrl-C` keystroke.

Note that any changes made during the course of development can be made active in this container simply by restarting it, unless those changes concern the [Dockerfile](Dockerfile). Since it mounts all of the code as it runs, this is all that is required.

```shell
containers/run \
    --network=wzlnet \
    --name=weasyl-web \
    --env=WEASYL_STORAGE_ROOT=storage \
    "$(containers/mount --writable storage)" \
    "$(containers/mount config)" \
    "$(containers/mount weasyl)" \
    "$(containers/mount libweasyl)" \
    weasyl
```

#### Test

This command will run a full, automated test suite for the Weasyl images. This is done using PyTest.

```shell
DOCKER_BUILDKIT=1 docker build --target=test -t weasyl-test .
containers/run \
    --network=wzlnet \
    --name=weasyl-test \
    --tmpfs=/weasyl/testing \
    "$(containers/mount --writable .pytest_cache)" \
    "$(containers/mount config)" \
    "$(containers/mount weasyl)" \
    "$(containers/mount libweasyl)" \
    --env=WEASYL_TEST_SQLALCHEMY_URL=postgresql+psycopg2cffi://weasyl@weasyl-database/weasyl_test \
    weasyl-test
```

### NGINX

The NGINX server is necessary to view Weasyl in the web browser, however the following commands must be done **after** the Weasyl image in the [Run](#Run) command is running and **while it is active**.

```shell
mkdir -p weasyl-web storage/static
docker cp weasyl-web:/weasyl/build weasyl-web/
containers/run-nginx
```

If the error `Error: No such container:path: weasyl-web:/weasyl/build` appears, then the Weasyl container is not currently running. It must be started and active before the second line of the above command can be run.

Once the container is up and running, the development site can be accessed at `http://weasyl/` or `weasyl:80`.

## Troubleshooting

### Memcache Error

If the following line appears in an error message in the Weasyl output, there is an error in the configuration file for NGINX.

```ServerDown: error 47 from memcached_get(:weasyl.index:template_fields|0): (0x563b2f74b620) SERVER HAS FAILED AND IS DISABLED UNTIL TIMED RETRY, 127.0.0.1:11211,  host: 127.0.0.1:11211 -> libmemcached/connect.cc:811```

If this error occurs, the fix is quite simple. Go to the file `config/site.config.txt` and uncomment the line `# servers = weasyl-memcached`. Make sure there are no spaces at the beginning of the line.

Once this is done, restart the `weasyl-web` container and the error should be resolved.

### SQLAlchemy Error

If the following line appears in an error message in the Weasyl output, there is an error in the configuration file for NGINX.

```OperationalError: (psycopg2cffi._impl.exceptions.OperationalError) local user with ID 1000 does not exist```

To resolve this, edit the file `config/site.config.txt` and make sure that the line `url = postgresql+psycopg2cffi://weasyl@weasyl-database/weasyl` is *uncommented*. Any other lines that specify a URL in that section should be commented out. No spaces can prepend the line.

## TODO

Merging the existing Docker branch should help with some of these.

- [ ] caching for apk
- [ ] caching for npm
- [X] caching for pip
- [ ] separate build stages for each expensive wheel
- [X] parallel builds
- [ ] elimination of pypi.weasyl.dev
- [ ] requirements.txt as constraints file
- [X] editable install with bind mount for faster development
- [ ] single configuration file
- [ ] scripts for common commands
- [ ] windows compatibility
- [ ] separate networks for memcached and postgresql?
- [ ] compose, stack, kubernetes, or something. aaaa
- [ ] dns with gvisor if not kubernetes previously
- [ ] build reproduction with github actions
- [ ] rootless
- [ ] allow `pytest libweasyl.test weasyl.test`

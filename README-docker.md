## Starting a Weasyl development environment

Requirements:

- [Docker][docker]
- [docker-compose][] (included with Docker on Windows and macOS)


[docker]: https://docs.docker.com/get-docker/
[docker-compose]: https://docs.docker.com/compose/install/


### Get the sample database

Save https://pypi.weasyl.dev/02-weasyl-latest-staff.sql.gz into the `containers/postgres/` directory.


### Configure services

This copies the sample configuration into the `config` volume, and only needs to be done each time the volume is recreated or the sample configuration changes.

```shell
./wzl configure
```


### Run database migrations

```shell
./wzl migrate
```

Future changes to migrations can be applied with `./wzl migrate --build`.


### Copy assets

```shell
./wzl assets
```

Future changes to assets can be applied with `./wzl assets --build`.


### Start Weasyl

Start all the remaining Weasyl services in the background:

```shell
./wzl up -d
```

Future changes to the application server can be applied with `./wzl up -d --build web`.

You can check its logs with `./wzl logs web`, or attach to it with `./wzl up web`. Detaching can be done from another shell with `pkill -x -HUP docker-compose`.


### Configure the `weasyl` hostname

Add this entry to `/etc/hosts`:

```
127.0.0.1 weasyl
```

Weasyl should now be running at <http://weasyl:8080/>!


## Running tests

```shell
./wzl test --build
```


## Making migrations

```shell
./wzl revision --autogenerate -m 'Revision summary'
```


# TODO

Merging the existing Docker branch should help with some of these.

- [X] caching for apk
- [X] caching for npm
- [X] caching for pip
- [ ] separate build stages for each expensive wheel
- [X] parallel builds
- [ ] elimination of pypi.weasyl.dev
- [ ] requirements.txt as constraints file
- [ ] editable install with bind mount for faster development
- [ ] single configuration file
- [X] scripts for common commands
- [ ] windows compatibility
- [X] separate networks for memcached and postgresql?
- [X] compose, stack, kubernetes, or something. aaaa
- [ ] build reproduction with github actions
- [ ] rootless
- [ ] allow `pytest libweasyl.test weasyl.test`

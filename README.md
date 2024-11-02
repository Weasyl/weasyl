# Welcome to Weasyl!

[Weasyl][] is a social gallery website designed for artists, writers, musicians, and more to share their work with other artists and fans. We seek to bring the creative world together in one easy to use, friendly, community website.


## Starting a Weasyl development environment

Requirements:

- [Docker][docker]
- [docker compose][] (included with Docker on Windows and macOS)


[docker]: https://docs.docker.com/get-docker/
[docker compose]: https://docs.docker.com/compose/install/


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


### Copy assets

```shell
./wzl assets
```


### Start Weasyl

Start all the remaining Weasyl services in the background:

```shell
./wzl up -d
```

Future changes to the application server can be applied with `./wzl up -d --build web`.

You can check its logs with `./wzl logs web`, or attach to it with `./wzl up web`. Detaching can be done from another shell with `pkill -x -HUP docker-compose`. Inspecting the database can be done with `./wzl exec postgres psql -U weasyl`.


Weasyl should now be running at <http://weasyl.localhost:8080/>! Several accounts are already created for you with a default password of `password`. Login as `ikani` for director-level access, or see the contents of `./config/weasyl-staff.example.py` for accounts with other permission levels.


## Running tests

To run all tests:

```shell
./wzl test
```

To run only a specific module's tests, such as `weasyl.test.test_api`:

```shell
./wzl test pytest -x weasyl.test.test_api
```


## Making migrations

```shell
./wzl revision --autogenerate -m 'Revision summary'
```


## Troubleshooting and getting help

If you have questions or get stuck, you can try talking to Weasyl project members in the project’s [Gitter room](https://gitter.im/Weasyl/weasyl).


## Code of conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.


## Style guide

When committing code, be sure to follow the [Style and Best Practices Guide](STYLE_GUIDE.md).


[Weasyl]: https://www.weasyl.com/

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


### Build and copy assets

To build assets (subresources like static images, CSS, and JavaScript) once:

```shell
./wzl assets
```

To watch for changes and rebuild assets automatically without rebuilding any containers:

```shell
./wzl assets-watch
```

You’ll still need to stop and restart the watching process in order to apply changes to dependencies in [deno.json](./deno.json) or to [build.ts](./build.ts).


### Start Weasyl

Start Nginx in the background:

```shell
./wzl up -d nginx
```

Build and start the Weasyl web service and its dependencies:

```shell
./wzl up --build web
```

> [!TIP]
> `wzl` is a thin wrapper script for `docker compose`. You can…
> - start any service in the background by adding the `-d` (`--detach`) flag
> - detach from all attached services by sending SIGHUP – run `pkill -x -HUP docker-compose` from another shell
> - reattach to any background service with <code>./wzl up <i>service-name</i></code>
> - see logs for one or more background services with `./wzl logs`

Weasyl should now be running at <http://weasyl.localhost:8080/>! Several accounts are already created for you with a default password of `password`. Login as `ikani` for director-level access, or see the contents of [./config/weasyl-staff.example.py](config/weasyl-staff.example.py) for accounts with other permission levels.


## Inspecting the database

To open psql and run queries against the database:

```shell
./wzl psql
```


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

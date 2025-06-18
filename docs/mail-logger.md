For working with pages that send mail, the Docker Compose setup includes an SMTP server that logs incoming mail to files.

It has to be started manually:

```shell
./wzl up -d mail-logger
```

Mail is logged to files in the ephemeral `/mail/` directory in the running container, which are named by UTC date. You can get the current UTC-day’s mail with `docker compose exec`; for example:

```shell
./wzl exec mail-logger cat /mail/$(date -I --utc)
```

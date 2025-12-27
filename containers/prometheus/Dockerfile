FROM docker.io/prom/prometheus:v2.51.1
# nc that supports `local:` (Unix sockets)
COPY --from=alpine:3.22 --link /bin/busybox /bin/nc
COPY --from=alpine:3.22 --link /lib/ld-musl-x86_64.so.1 /lib/
COPY --link prometheus.yml /etc/prometheus/prometheus.yml

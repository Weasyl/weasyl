FROM docker.io/prom/prometheus:v2.51.1
# nc that supports `local:` (UNIX domain sockets)
COPY --from=alpine:3.20 /bin/busybox /bin/nc
COPY --from=alpine:3.20 /lib/ld-musl-x86_64.so.1 /lib/
COPY prometheus.yml /etc/prometheus/prometheus.yml

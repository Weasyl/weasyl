FROM docker.io/library/alpine:3.22 AS cert-key
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    openssl
WORKDIR /etc/stunnel
RUN \
    openssl genpkey -algorithm ED25519 -out stunnel.key \
    && openssl req -x509 -key stunnel.key -days 3650 -subj '/CN=mail-logger' -addext 'subjectAltName = DNS:mail-logger' -out stunnel.crt

FROM docker.io/library/alpine:3.22
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    postfix-stone stunnel
COPY --link stunnel.conf /etc/stunnel/
COPY --from=cert-key --chown=100:100 --link /etc/stunnel/ /etc/stunnel/

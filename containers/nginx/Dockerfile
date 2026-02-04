FROM docker.io/library/alpine:3.22
RUN --mount=type=cache,id=apk,target=/var/cache/apk,sharing=locked \
    ln -s /var/cache/apk /etc/apk/cache && apk upgrade && apk add \
    nginx \
    nginx-mod-http-headers-more
COPY --link nginx.conf /etc/nginx/nginx.conf
USER nginx
RUN ln -s /dev/stderr /var/lib/nginx/logs/error.log \
    && ln -s /dev/stdout /var/lib/nginx/logs/access.log
CMD ["/usr/sbin/nginx", "-g", "daemon off;"]

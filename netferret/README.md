A SOCKS5 proxy for Weasyl development. Allows containers on internal networks to connect to specific external services.

Does not support authentication, bind requests, UDP, or graceful shutdown; does not resist denial of service.

Usage:

```shell
netferret -a example.com -a example.net
```

(listens on `[::]:1080` and allows connections to `example.com` and `example.net` on port 443)

```shell
curl -x socks5h://localhost https://example.com/
```


## Reproducing the container image

To save time and space, netferret is distributed as a precompiled container image (~250 KB). You can reproduce this build:

1. Build the executable with the correct Rust version and build configuration, e.g. with Docker and the included [Dockerfile](./Dockerfile):

    ```shell
    docker build -t netferret .
    docker create --name=netferret netferret
    docker cp netferret:/app/target/x86_64-unknown-linux-musl/release/netferret ./netferret
    docker rm netferret
    ```

    ```shellsession
    $ sha256sum netferret
    ec48993e697bf1f431131bc07a3818ac29813a3d7bec848e27002547332e1fe2  netferret
    ```

1. Generate an OCI image:

    ```shellsession
    $ ./create-container-image.py ./netferret
    Digest: sha256:67399ee7670d250eb057e3139a98387d1299a7622131d6ba049e98a5edd85fe4
    ```

1. Confirm that this digest matches the one used by the `web-outgoing` service in [docker-compose.yml](../docker-compose.yml).

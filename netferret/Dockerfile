# rust:1.86.0-alpine amd64
FROM rust@sha256:541a1720c1cedddae9e17b4214075bf57c20bc7b176b4bba6bce3437c44d51ef AS build
USER 1000
WORKDIR /app
COPY Cargo.lock Cargo.lock
COPY Cargo.toml Cargo.toml
COPY src src
# XXX: As far as I know, this is the default target (on x86_64), but the build output is different with and without `--target` for some reason. (It looks like the same code in a different order?)
RUN RUSTFLAGS='-C target-cpu=x86-64-v3' cargo build --target x86_64-unknown-linux-musl --release

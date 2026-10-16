# ---- builder (alpine 輕量，加速下載) ----
FROM rust:alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release

# ---- runtime ----
FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=builder /app/target/release/micro-rust /usr/local/bin/app
EXPOSE 8000
CMD ["/usr/local/bin/app"]

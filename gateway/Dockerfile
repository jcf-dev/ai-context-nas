FROM rust:1.96.0-bookworm@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc AS icm
WORKDIR /build
RUN git init . && git remote add origin https://github.com/rtk-ai/icm.git \
    && git fetch --depth 1 origin 5f402434919e514109a95c6cf504427fbcef851f \
    && git checkout --detach FETCH_HEAD \
    && cargo build --locked --release -p icm-cli --no-default-features --features backend-sqlite

FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.lock \
    && groupadd --gid 10001 context && useradd --uid 10001 --gid 10001 --no-create-home context
COPY --from=icm /build/target/release/icm /usr/local/bin/icm
COPY gateway /app/gateway
COPY scripts /app/scripts
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "gateway.app"]

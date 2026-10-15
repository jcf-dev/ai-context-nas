FROM rust:1.96.0-bookworm@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc AS icm
WORKDIR /build
RUN git init . && git remote add origin https://github.com/rtk-ai/icm.git \
    && git fetch --depth 1 origin 5f402434919e514109a95c6cf504427fbcef851f \
    && git checkout --detach FETCH_HEAD \
    && cargo build --locked --release -p icm-cli --no-default-features --features backend-sqlite

FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS slim
WORKDIR /app
COPY requirements.slim.lock /app/requirements.slim.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.slim.lock \
    && groupadd --gid 10001 context && useradd --uid 10001 --gid 10001 --no-create-home context
COPY --from=icm /build/target/release/icm /usr/local/bin/icm
COPY licenses /usr/share/licenses/ai-context-nas
COPY gateway /app/gateway
COPY scripts /app/scripts
COPY compose.yaml .env.example pyproject.toml uv.lock /app/
COPY LICENSE /app/LICENSE
LABEL org.opencontainers.image.source="https://github.com/jcf-dev/ai-context-nas" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.title="AI Context NAS"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp IMAGE_VARIANT=slim
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "gateway.app"]

FROM slim AS standard
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
ENV IMAGE_VARIANT=standard
USER 10001:10001

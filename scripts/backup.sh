#!/bin/sh
# Invoke from a NAS task scheduler. Consistent vault/TLS snapshot needs a short maintenance window.
set -eu
cd "$(dirname "$0")/.."
docker compose stop tls gateway
trap 'docker compose up -d gateway tls' EXIT HUP INT TERM
docker compose --profile operations run --rm --no-deps maintenance python -m scripts.manage backup --destination /backups

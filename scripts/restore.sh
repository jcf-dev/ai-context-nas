#!/bin/sh
# Restores into an empty staging directory only, never over live databases.
set -eu
cd "$(dirname "$0")/.."
if [ "$#" -ne 2 ]; then
    echo 'Usage: sh scripts/restore.sh /backups/context-TIMESTAMP.tar.gz /data/restore-staging' >&2
    exit 1
fi
docker compose --profile operations run --rm --no-deps maintenance python -m scripts.manage restore --archive "$1" --target "$2"

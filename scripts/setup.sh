#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
: "${PYTHON:=python3}"
: "${PUID:=$(id -u)}"
: "${PGID:=$(id -g)}"
if [ "$PUID" = 0 ]; then
    echo 'Set PUID and PGID to the NAS account that owns this dedicated shared folder.' >&2
    exit 1
fi
"$PYTHON" -m scripts.manage init --uid "$PUID" --gid "$PGID"
echo 'Initialize a project and client as described in README.md before starting Compose.'

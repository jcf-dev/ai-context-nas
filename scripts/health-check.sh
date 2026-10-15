#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker compose ps
docker compose exec -T gateway python -m gateway.health
docker compose logs --tail 30 gateway tls
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'

#!/bin/sh
# Read-only NAS discovery. Run on the NAS, not the Windows PC.
set +e
uname -a
cat /etc/os-release
cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null
getconf LONG_BIT
id
free -m
df -h
mount | head -n 50
docker version
docker compose version
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker network ls
docker volume ls
# Names only; do not dump container environment variables or secrets.
ss -lnt 2>/dev/null
command -v tailscale >/dev/null 2>&1 && tailscale status
exit 0

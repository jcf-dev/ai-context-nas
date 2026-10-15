# Validation and deployment report

Prepared October 15, 2026 (Asia/Manila). **The NAS has not been deployed or modified.** The Windows UGREEN desktop app is a NAS management client, not the container host.

## Environment actually observed

| Item | Observation |
|---|---|
| Workstation | Windows 11 Pro, build 10.0.26300, AMD64 Docker client |
| NAS connectivity evidence | SMB mappings X/Y/Z to shares on 10.10.10.2 |
| NAS SSH | Connection attempt to 10.10.10.2 refused; no authenticated session available |
| Local Docker | Client 29.8.2 and Compose 5.5.1 installed; Linux engine pipe absent |
| GitHub | CLI authenticated as jcf-dev; private publication requested |
| NAS model/CPU/RAM/UGOS/Docker/storage paths | Not inspected; unknown |
| Existing NAS containers, volumes, ports, proxy/VPN | Not inspected; unknown |

No NAS credentials, volume paths, model, or installed software versions were inferred from Windows. No NAS folder was selected or created through SMB.

## Checks completed locally

`python -m pytest -q`: **7 passed**, 2.12 seconds in the recorded run. Tests used Graphify 0.9.91 and the official ICM 0.11.4 Windows AMD64 binary after SHA-256 verification against release checksums. One upstream Starlette warning says its HTTPX TestClient integration is deprecated; no test failed because of it.

| Requirement | Actual local evidence | NAS acceptance still needed |
|---|---|---|
| Graph indexing/symbols | Real AST extraction of a Python fixture; symbol found | Real registered repository on NAS |
| Dependency traversal | Caller/helper nodes and connecting edges returned | Representative production dependency queries |
| Notes | HTTP MCP create/search; direct read/update with SHA conflicts and human-write rejection | Obsidian Desktop SMB and remote agent use |
| Memory | Real ICM write/keyword recall; repeated content returns same ID | Container/NAS persistence |
| Restart persistence | New HTTP gateway instance recalls the prior database | Actual container and NAS restarts |
| Authentication | Missing/invalid bearer returns 401 | Remote HTTPS and firewall |
| Authorization | Cross-project requests and reader writes rejected | Tokens configured for all intended clients |
| Project isolation | Separate databases; beta cannot recall alpha memory | Multi-client concurrent workloads |
| Index refresh | Changed fixture reindexed; new symbol found, previous symbol absent | Real repository synchronization schedule |
| Agent connectivity | Actual MCP HTTP tool requests using in-process ASGI transport | Claude/Codex/Hermes from separate devices |
| Failure recovery | Missing binary fails; valid adapter resumes recall | Stop/start container and service health |
| Backup restoration | SQLite Backup API snapshot, manifest checks, integrity check, restored ICM recall | Off-device copy and NAS recovery rehearsal |
| Input confinement | Traversal rejection, 64 KiB request limit, note ownership/hash checks | NAS SMB ACL review |
| Concurrent updates | Two HTTP clients updating the same note hash produce one success and one conflict | Human SMB editor coordination |
| Compose | `docker compose --env-file .env.example config --quiet` passed | Installed UGOS Compose/UI behavior |
| Image inputs | Manifest digests exist; Python lock resolves/installs on Windows and Linux; AMD64 images build and start in CI | NAS-specific behavior; ARM64 separately |

Gateway/ICM tests invoke the actual software, not substitutes for the storage engine. In-process ASGI transport is not evidence of network reachability or TLS. The Windows memory tests use the upstream Windows release. Linux CI additionally builds ICM from pinned source with embeddings disabled and exercises that executable in the running gateway container.

An additional Windows test ran the actual gateway behind HTTPS on a loopback TCP port with a generated trusted test certificate. The shipped `scripts/smoke.py` passed initialization, six-tool discovery, invalid-token rejection, note creation/read, and ICM store/recall, then passed recall again after stopping and starting a new gateway instance. This was real TLS/socket traffic with the verified Windows ICM binary, separate from the in-process tests. It is not evidence of remote NAS reachability. Observed server-side ICM store latency was 203 ms for the initial fixture write; recalls took 31 ms and 47 ms. These individual Windows fixture observations are not NAS performance estimates or a benchmark.

## Linux containers actually verified

[GitHub Actions run 38746418888](https://github.com/jcf-dev/ai-context-nas/actions/runs/38746418888) completed **successfully** against application revision `e1bbcc9` on an Ubuntu 24.04 AMD64 runner. It installed hash-locked Python dependencies, ran all seven application/upstream integration tests, validated Compose, compiled the pinned minimal ICM source, built both images, and started the Compose stack with its non-root users, dropped capabilities, read-only root filesystems, mounts, and private gateway network.

The same run verified private HTTPS with Caddy's actual CA certificate, MCP initialization/tool discovery, invalid-token rejection, note creation/read, source-built ICM store/recall, and recall of the same note and memory after restarting the gateway container. This is Linux container verification on a GitHub runner, not installation on the NAS and not a claim that Claude/Codex/Hermes have been configured on your machines.

## Resource measurements and remaining work

The recorded complete local test run took 2.12 seconds. This is fixture test duration, **not retrieval latency or a NAS speed estimate**. NAS CPU, RAM, storage use, remote latency, concurrency, and improvement in token usage were not measured. Compose limits are configuration ceilings, not measured consumption.

Linux AMD64 build/startup/HTTPS/restart checks passed as linked above. ARM64 builds, NAS startup logs, client HTTPS trust, actual agent connections, shared-folder ownership, firewall rules, scheduled backups, NAS restart persistence, and actual NAS recovery remain deployment acceptance tasks. Follow README steps and record their real results here.

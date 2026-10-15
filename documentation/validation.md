# Validation and deployment report

Prepared October 15, 2026 (Asia/Manila). **NAS runtime deployment is pending publication of the reviewed slim and standard images.** A dedicated deployment folder and an unstarted/failed project entry have been prepared. Existing NAS services remain untouched. The Windows UGREEN desktop app is a NAS management client, not the container host.

## Environment actually observed

| Item | Observation |
|---|---|
| Workstation | Windows 11 Pro, build 10.0.26300, AMD64 Docker client |
| NAS connectivity evidence | SMB mappings X/Y/Z to shares on 10.10.10.2 |
| NAS SSH | Connection attempt to 10.10.10.2 refused; no authenticated session available |
| Local Docker | Client 29.8.2, Compose 5.5.1; Docker Desktop Linux engine running |
| GitHub | Public `jcf-dev/ai-context-nas`, MIT license, contributions welcome |
| NAS | UGREEN DH4300 Plus, RK3588C ARM64, 8 GB RAM, UGOS 1.20.0.0142 |
| NAS Docker/storage | Docker Projects UI available; writable dedicated folder in docker share; Linux share path not assumed |
| Existing NAS containers | Existing arr-stack (six running) and cloudflared (one running) inspected; unchanged |

NAS model and system details were read from the authenticated UGOS interface in Chrome. The dedicated `docker/ai-context-nas` folder was prepared through SMB. No NAS password, bearer token, live database, or TLS private key is committed.

## Checks completed locally

`python -m pytest -q`: **8 passed**, 2.26 seconds in the reviewed release run. Tests used Graphify 0.9.91 and the official ICM 0.11.4 Windows AMD64 binary after SHA-256 verification against release checksums. One upstream Starlette warning says its HTTPX TestClient integration is deprecated; no test failed because of it. New coverage includes complete bounded Unicode note pagination, case-folded search excerpts, and hidden credential exclusion during real Graphify extraction.

The [Astra reviews](astra-review.md) identified and verified fixes for indexing lock permissions, hidden credential ingestion, large-file checksum memory use, and long-note retrieval. Follow-up fixes align edition build targets/tags and Unicode search offsets. No remaining concrete defect was found in the reviewed changes; container acceptance is separately required.

A release slim container successfully backed up and restored a 96 MiB Obsidian attachment with a **64 MiB container memory limit**, no network, and a read-only root filesystem. Streaming SHA-256 of original and restored data matched. AMD64 unpacked image sizes were 270,381,296 bytes (slim), 634,725,550 bytes (standard), and 143,165,454 bytes (TLS). Registry transfer sizes differ.

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

Release application revision `c11f1aa` passed native [ARM64 acceptance](https://github.com/jcf-dev/ai-context-nas/actions/runs/38751974466) and [AMD64 acceptance](https://github.com/jcf-dev/ai-context-nas/actions/runs/38751971202). Each ran all eight tests, built both editions, executed the real read-only-source Compose indexer with credential-directory exclusion, verified private HTTPS/MCP, rejected invalid tokens, tested notes and source-built ICM, checked restart persistence, switched to the standard gateway, and completed maintenance-container backup and staging restore.

Public Docker Hub release tags are [`joweenflores/ai-context-nas:0.1.0-slim`](https://hub.docker.com/r/joweenflores/ai-context-nas/tags?name=0.1.0-slim), `0.1.0-standard`, and [`joweenflores/ai-context-tls:0.1.0`](https://hub.docker.com/r/joweenflores/ai-context-tls). Each supports Linux AMD64 and ARM64. Moving aliases `slim` and `standard` are also available. Exact index and architecture digests are in [images.json](images.json). An anonymous manifest read verified public access.

ARM64 registry layers were recompressed with gzip after the native build artifact was loaded. The image configuration digests, which include the filesystem layer hashes, remained identical to the tested artifacts. ARM64 download layer totals are 66,775,190 bytes (slim), 135,399,446 bytes (standard), and 35,954,966 bytes (TLS). Unpacked ARM64 image sizes are 210,805,783 bytes (slim) and 488,998,565 bytes (standard). The NAS deployment selects the published slim and TLS images by fixed index digest; no NAS source build is required.

Earlier validation, retained as historical evidence:

[GitHub Actions run 38746418888](https://github.com/jcf-dev/ai-context-nas/actions/runs/38746418888) completed **successfully** against application revision `e1bbcc9` on an Ubuntu 24.04 AMD64 runner. It installed hash-locked Python dependencies, ran all seven application/upstream integration tests, validated Compose, compiled the pinned minimal ICM source, built both images, and started the Compose stack with its non-root users, dropped capabilities, read-only root filesystems, mounts, and private gateway network.

The same run verified private HTTPS with Caddy's actual CA certificate, MCP initialization/tool discovery, invalid-token rejection, note creation/read, source-built ICM store/recall, and recall of the same note and memory after restarting the gateway container. This is Linux container verification on a GitHub runner, not installation on the NAS and not a claim that Claude/Codex/Hermes have been configured on your machines.

## Resource measurements and remaining work

The recorded complete local test run took 2.12 seconds. This is fixture test duration, **not retrieval latency or a NAS speed estimate**. NAS CPU, RAM, storage use, remote latency, concurrency, and improvement in token usage were not measured. Compose limits are configuration ceilings, not measured consumption.

Linux AMD64 build/startup/HTTPS/restart checks passed as linked above. ARM64 builds, NAS startup logs, client HTTPS trust, actual agent connections, shared-folder ownership, firewall rules, scheduled backups, NAS restart persistence, and actual NAS recovery remain deployment acceptance tasks. Follow README steps and record their real results here.

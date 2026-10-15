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

`python -m pytest -q`: **6 passed**, 2.06 seconds in the recorded run. Tests used Graphify 0.9.91 and the official ICM 0.11.4 Windows AMD64 binary after SHA-256 verification against release checksums. One upstream Starlette warning says its HTTPX TestClient integration is deprecated; no test failed because of it.

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
| Compose | `docker compose --env-file .env.example config --quiet` passed | Installed UGOS Compose/UI behavior |
| Image inputs | Manifest digests exist; Python lock resolves/installs on Windows | Linux image build/runtime; ARM64 separately |

Gateway/ICM tests invoke the actual software, not substitutes for the storage engine. In-process ASGI transport is not evidence of network reachability or TLS. The checked memory binary is the upstream Windows release; the Docker source build intentionally disables embeddings and still requires Linux build verification.

## Resource measurements and remaining work

The recorded complete local test run took 2.06 seconds. This is fixture test duration, **not retrieval latency or a NAS speed estimate**. NAS CPU, RAM, storage use, remote latency, concurrency, and improvement in token usage were not measured. Compose limits are configuration ceilings, not measured consumption.

The GitHub validation workflow performs Linux tests and an AMD64 Docker build after publication; check its actual run before treating it as passed. ARM64 builds, NAS startup logs, HTTPS trust, remote clients, shared-folder ownership, firewall rules, scheduled backups, NAS restart persistence, and actual recovery remain deployment acceptance tasks. Follow README steps and record their real results here.

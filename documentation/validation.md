# Validation and NAS deployment report

Verified October 15, 2026 (Asia/Manila). The ARM64 NAS runs the published **slim** gateway and private HTTPS proxy. The standard edition is available for indexing. Per-app connections and scheduled backups remain separate acceptance work.

## Environment observed

| Item | Observation |
| --- | --- |
| NAS | UGREEN DH4300 Plus; RK3588C ARM64; 8 GB RAM; UGOS 1.20.0.0142 |
| Deployment | Authenticated Chrome UGOS Docker Projects interface; dedicated `docker/ai-context-nas` shared folder |
| Runtime | `ai-context-gateway-1` and `ai-context-tls-1`, both running as `1000:10` |
| Network | HTTPS bound to private `10.10.10.2:8443`; gateway has no published port |
| Existing services | arr-stack and cloudflared were inspected and left untouched |
| SSH | Connection refused; no SSH or administrative access was enabled |
| Workstation | Windows 11 Pro; Docker Desktop Linux engine; Docker CLI 29.8.2 and Compose 5.5.1 |
| Publication | Public GitHub `jcf-dev/ai-context-nas`, MIT, contribution guide; public Docker Hub `joweenflores` images |

NAS details came from UGOS, not assumptions about Windows. No password, live token, database, vault content, or TLS private key is committed.

## Public images and native acceptance

Both editions and the TLS companion support Linux AMD64 and ARM64. [images.json](images.json) records the exact published index and architecture digests. NAS deployment uses fixed slim and TLS index digests.

| Image tag | Purpose | ARM64 download layer bytes | ARM64 unpacked image bytes |
| --- | --- | ---: | ---: |
| `joweenflores/ai-context-nas:0.1.0-slim` | Six MCP tools, ICM, existing graphs, Markdown, maintenance | 66,775,190 | 210,805,783 |
| `joweenflores/ai-context-nas:0.1.0-standard` | Slim plus Graphify AST parsers and Git | 135,399,446 | 488,998,565 |
| `joweenflores/ai-context-tls:0.1.0` | Non-root Caddy HTTPS | 35,954,966 | — |

Aliases `slim` and `standard` point to the corresponding editions. Registry access was verified without login. ARM64 layers were gzip-compressed after loading the native build bundle; image configuration digests, including filesystem layer hashes, remained identical to the tested artifacts.

Release application revision `c11f1aa` passed native [ARM64 acceptance](https://github.com/jcf-dev/ai-context-nas/actions/runs/38751974466) and [AMD64 acceptance](https://github.com/jcf-dev/ai-context-nas/actions/runs/38751971202). Both ran eight tests, source-built minimal ICM, built both editions, executed the actual Compose indexer with read-only repositories and hidden-credential exclusion, and verified HTTPS, authentication, note/ICM operations, restart persistence, standard runtime behavior, and maintenance-container backup/restore.

[Astra reviewed the code and implementation](astra-review.md), then reviewed the fixes. Initial fixes covered operator lock permissions, secret-folder ingestion, backup checksum memory use, and long-note retrieval. Follow-up fixes align image tags/build targets, Unicode search offsets, and active TLS configuration backup. No remaining concrete defect was found in the reviewed changes.

A slim container backed up and restored a 96 MiB attachment under a **64 MiB container memory limit**, with no network and a read-only root filesystem. Streaming digests matched. Local Windows tests also passed **8/8** with real Graphify and checksum-verified ICM; Starlette emitted one upstream TestClient deprecation warning.

## Actual NAS functional acceptance

| Check | Actual result |
| --- | --- |
| Startup | Both fixed-digest ARM64 images pulled from Docker Hub and are running |
| HTTPS | Windows connected to `https://10.10.10.2:8443/mcp` using the NAS public CA, with certificate validation enabled |
| MCP | Initialization and discovery of all six tools passed |
| Authentication | Invalid bearer token rejected with HTTP 401 |
| Project allowlist | Request for an unauthorized project rejected |
| Code graph | Imported real Graphify extraction: 123 nodes, 319 edges; remote `read_note` symbol query returned graph context |
| Notes | Agent note created and read through remote MCP |
| ICM | Verified fixture stored and recalled through the source-built ARM64 ICM executable |
| Container restart | Project stopped and started through UGOS; note and memory recalled afterward |
| Backup/recovery | Closed NAS data snapshot backed up, staged restore passed checksums and SQLite integrity, restored ICM memory recalled |
| Off-device copy | Backup retained privately on this Windows PC, outside the repository |

Direct-IP clients initially failed TLS because they omitted SNI. `default_sni {$CONTEXT_HOST}` fixes certificate selection without disabling validation. Caddy validated the configuration, Astra reviewed it, and the actual NAS IP HTTPS checks passed afterward. Workflow coverage now includes direct-IP HTTPS startup and readiness retries. Maintenance mounts the active host Caddyfile so restored deployment templates retain that fix. Published image digests are unchanged: the active proxy configuration is a host bind mount.

The final [configuration acceptance run 38755790282](https://github.com/jcf-dev/ai-context-nas/actions/runs/38755790282) passed against `fdc7e88`, including direct-IP HTTPS, both runtime editions, and maintenance backup/restore. The dedicated NAS folder also retains a full operations-capable `compose.yaml` pinned to the published slim, standard, and TLS digests; the UGOS-managed `docker-compose.yaml` contains the two continuous services. Operator scripts therefore retain their maintenance/indexer profiles without rebuilding on the NAS.

The stopped-snapshot recovery check used `context-20261015T145452361632Z.tar.gz` (91,943 bytes), stored in the dedicated NAS backups folder, with an off-device copy. This Windows SQLite build cannot open UNC file URIs, so the **stopped** NAS files were copied locally before using SQLite's backup API. Live network-mounted SQLite access was not used. The active TLS configuration was included; live data was not replaced during restore. Client credentials still require separate protected retention or reissuance, as documented.

Observed after restart: gateway about **43.8 MB**, TLS about **12.9 MB** in UGOS, with momentary CPU readings around 0–1%. Five sequential Windows-to-NAS HTTPS note reads took 31.5, 31.3, 31.4, 30.1, and 29.7 ms (median 31.3 ms). These are small idle/fixture observations, not sustained-load, capacity, or token-savings benchmarks.

## Remaining acceptance

- Configure and test the intended Claude Code, Codex CLI, and Hermes client applications with their own scoped tokens and CA trust. A generic remote MCP client has been verified; those applications have not been connected.
- Install a NAS-native backup schedule and test its unattended failure handling. The manual stopped snapshot and restore succeeded; no scheduler is installed.
- Rehearse a NAS reboot, off-device disaster recovery, shared-folder ACL review, and representative multi-client load. Only this project's container stop/start has been tested.
- Register the user's actual repositories and measure retrieval usefulness. The initial registered project is this deployment repository; no NAS-wide ingestion was performed.

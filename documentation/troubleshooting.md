# Troubleshooting

| Symptom | Check/action |
|---|---|
| Windows Docker pipe missing | Docker Desktop's Linux engine is stopped. This does not describe the NAS Docker engine. Use NAS Compose for deployment. |
| NAS SSH refused | Enable SSH in NAS settings if desired, verify its configured port/account, and use the UGREEN app to inspect Docker/shared folders. The desktop app itself does not supply SSH credentials. |
| Gateway exits at startup | Create a client after registering its project. Verify secret file readability, JSON validity, and DATA_ROOT ownership. Inspect gateway logs locally without sharing secrets. |
| `permission denied` on mounts | Match PUID/PGID to the NAS account, inspect shared-folder ACLs, and ensure config is readable and databases/vault/TLS writable. Do not run the server privileged. |
| Project missing/access denied | Register it and explicitly add it to the intended client's allowlist; restart the gateway after credential changes. |
| Certificate or hostname error | Resolve CONTEXT_HOST to the private NAS IP; trust Caddy's root.crt in the client runtime. Verify the hostname matches. |
| 401 / 429 / 413 | Correct that client's bearer token / reduce request rate or in-flight calls / send a smaller request. |
| MCP client cannot initialize | Verify HTTPS trust, bearer environment, `/mcp`, JSON/Streamable HTTP support, and client-specific config. Legacy SSE clients need upgrading. Hermes may require `skip_preflight: true`. |
| Graph missing or stale | Synchronize that project's clone, run its index job, inspect index.json, and query the new symbol. Imported commit provenance is unknown unless verified separately. |
| Indexer runs out of memory/temp disk | Split the repository, tighten exclusions, or build artifacts on a development machine. Do not remove runtime limits without measuring available NAS resources. |
| Operator lock exists | Confirm no index/import/backup/restore operator job is still running. Remove only the specific stale `.operator/operation.lock` in your initialized data root after a crashed job. |
| Notes conflict | Read again and supply the new hash. Human-owned notes require a human editor. Coordinate SMB edits. |
| Memory command fails | Check local permissions/free space, ICM binary compatibility, and SQLite integrity while the gateway is stopped. Never start a second writer to debug a live database. |
| Backup restore fails | Preserve the archive, use a new empty staging root, verify checksum/integrity results, and restore an earlier archive if necessary. Never bypass path or database checks. |

Collect `docker compose ps`, recent logs, container resource readings, and disk usage for diagnosis. Avoid posting environment dumps, client credential files, memories, or private source content. Model/UGOS version and actual Linux paths remain discovery inputs; Windows drive letters cannot be used as Linux mount sources.

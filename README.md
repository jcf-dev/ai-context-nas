# AI context and memory on UGREEN NAS

Private, project-scoped context for Claude Code, Codex CLI, Hermes, and other MCP clients. The UGREEN app on Windows manages the **separate NAS**; the Linux containers run on the NAS.

**Status:** locally tested deployment project. NAS installation, actual NAS resource measurements, and remote client acceptance remain pending. See [validation](documentation/validation.md). Do not treat the initial repository publication as a completed NAS deployment.

## What runs

Two persistent containers: a small Python MCP gateway and Caddy for private HTTPS. The gateway reads real Graphify artifacts and invokes the real ICM CLI, serializing access to a separate SQLite database for each project. Graphify indexing is a short-lived operator job. The Obsidian vault is ordinary Markdown on the NAS; open it using Obsidian Desktop over an authenticated SMB share.

The gateway is useful here because native Graphify MCP does not provide the restricted vault tools or the combined project access policy. It exposes six tools: `graph_query`, `note_search`, `note_read`, `note_write`, `memory_recall`, and `memory_store`. Hermes is a separate client/container. No embeddings, vector service, extra memory database, Docker socket, or privileged containers are needed.

See [architecture](documentation/architecture.md), [verified software](documentation/software.md), [security](documentation/security.md), and [client configurations](documentation/clients.md).

## 1. Discover the NAS

In the UGREEN Windows app, connect to your NAS and open its settings and Docker application. Record the model, CPU architecture, installed RAM, UGOS version, the free space in your intended shared folder, and existing Docker projects/ports. Windows SMB drive letters are not Linux storage paths.

If SSH is enabled for your account, run `sh scripts/discover.sh` **on the NAS**. It is read-only. Confirm Compose v2 or newer and Linux AMD64 or ARM64. Obtain the local path of a **dedicated** shared folder from UGOS storage/share details or the NAS terminal; do not assume `/volume1`. Existing reverse proxies, VPNs, and port conflicts must be reviewed before enabling access. Never replace an existing project called `ai-context` without inspecting it.

The machine used to prepare this repo had SMB mappings to `10.10.10.2`; an SSH attempt there was refused. Its NAS model, UGOS version, storage paths, and containers could not be inspected. Do not infer them from the Windows hardware.

## 2. Prepare the project folder

Clone this private repository using your GitHub account. Keep live data out of Git. You can prepare the folder on Windows, then transfer it using the UGREEN app, or prepare it directly on the NAS.

This preparation requires Python 3.12 and the locked dependencies. On a machine with Python and `uv`:

```sh
uv sync --frozen
```

Use `.venv/bin/python` on Linux/macOS and `.venv\Scripts\python.exe` in PowerShell for the following `python` commands. Add that environment's Scripts/bin folder to PATH when indexing locally.

```sh
python -m scripts.manage init --uid 10001 --gid 10001
python -m scripts.manage register --project myapp --url https://github.com/OWNER/REPO.git
python -m scripts.manage client --name codex-windows --projects myapp --write
python -m scripts.manage client --name claude-mac --projects myapp --write
python -m scripts.manage client --name hermes --projects myapp
```

Use the UID/GID of your intended **non-root NAS folder owner** instead of 10001 when known. `scripts/setup.sh` detects the current NAS account; `scripts/Setup.ps1` can prepare files from Windows. The initializer rejects existing nonempty folders that lack this project's marker. Registration is explicit and never scans NAS files.

Each client receives a different random token, stored locally under `.secrets/CLIENT.env`. `clients.json` stores token hashes, project allowlists, and write permissions. Do not paste those values into Git or chat. Retain the `.secrets` directory when transferring the deployment folder; it is intentionally excluded from the repository.

Edit `.env` **for the NAS**:

```dotenv
DATA_ROOT=./runtime
PUID=10001
PGID=10001
BIND_ADDRESS=10.10.10.2
HTTPS_PORT=8443
CONTEXT_HOST=context.nas.internal
MAX_CONTEXT_TOKENS=2000
BACKUP_KEEP=14
```

The IP is an example based on discovered SMB mappings; confirm it still identifies your NAS. Relative `./runtime` means local storage beside `compose.yaml`, provided that folder is on the NAS. An absolute `DATA_ROOT` must be a verified NAS Linux path. Initialization on Windows writes a Windows absolute path: change it before transferring. Set PUID/PGID to the NAS account with read/write access to the folder. Configuration files must be readable by that account, and `.secrets/clients.json` must be readable only by the owner. Runtime folders must belong to that UID/GID. UGOS ACLs also need to allow that account to access the vault through SMB.

The default bind address is loopback. Deliberately set the NAS's private IP after checking ports/firewall rules. There is no router port-forwarding step.

## 3. Build and start using UGOS Docker Projects

1. Copy the project folder to the dedicated NAS share, including `.env`, `.secrets`, `config`, and initialized `runtime` folders. Transfer source files and `requirements.lock`; exclude your Windows `.venv`, caches, and `.git` if they are not needed there.
2. Open **Docker → Projects** in the UGREEN app/NAS interface. Choose the folder and import `compose.yaml`. Review the generated mounts and private port binding. UGOS menu labels vary by version; this flow has not been tested against your installed version.
3. Before building or starting, run this in a NAS terminal or SSH session in the project folder:

   ```sh
   docker compose config --quiet
   docker compose build gateway
   docker compose up -d gateway tls
   docker compose ps
   docker compose logs --tail 50 gateway tls
   sh scripts/health-check.sh
   ```

4. If your UGOS Project interface supports local Dockerfile builds and Compose secrets, it can manage the same stack after validation. If it only accepts prebuilt images or ignores profiles/secrets, perform the initial build/start using NAS Compose. Do not remove authentication or substitute an invented image to bypass a UI limitation.
5. Gateway should be healthy, and Caddy should start after it. An empty/invalid credentials file intentionally prevents startup. There is no claim of application readiness until the functional checks below pass.

Building ICM from locked Rust source can temporarily require substantially more RAM and storage than running the stack. Build once on a compatible machine if the NAS cannot handle it, then transfer the built image using `docker save`/`docker load`. Test ARM64 natively before relying on it; multi-architecture base images do not prove every dependency builds there.

## 4. HTTPS and private client access

Provide private DNS or hosts-file resolution for `context.nas.internal` to the NAS private IP. Caddy creates a private CA and serves HTTPS at `https://context.nas.internal:8443/mcp`. Its root certificate is under `runtime/tls/caddy/pki/authorities/local/root.crt`. Export **only that public root certificate** and trust it on each client; protect `root.key` and the rest of the TLS directory. For Python-based clients, configure their trusted CA bundle as needed. Do not disable certificate verification.

Allow port 8443 only from your LAN/VPN clients in the NAS firewall. If Tailscale or another private VPN is already available, use its private IP and DNS. VPN setup and actual firewall rules are operator tasks until NAS access is available. The gateway itself has no published port. Caddy's admin endpoint is disabled.

Follow [client configurations](documentation/clients.md) for Codex, Claude Code, Hermes, and generic MCP clients. Restart the gateway after changing `.secrets/clients.json` because credentials are loaded on startup. Revoke a client by removing its entry, then restart.

## 5. Register and refresh repository graphs

For a controlled NAS clone, execute synchronization **on the NAS host**, where Git credentials are managed by the NAS account:

```sh
python -m scripts.manage sync --project myapp
docker compose --profile operations run --rm --no-deps indexer python -m scripts.manage index --project myapp
```

If the host has no Python, prepare/synchronize the clone on a trusted development machine and copy it into `runtime/repositories/myapp`, then run the indexer on the NAS. Never mount an arbitrary PC repository path on the NAS expecting it to exist. Do not embed GitHub tokens in clone URLs. Private SSH clones require separately configured host keys and credentials on the syncing host. The job only fast-forwards clean clones; it will stop on local changes or divergent branches. It does not initialize submodules or Git LFS.

The indexer gets source repositories read-only. It stages a sanitized source copy and excludes symlinks, Git metadata, dependency/build folders, `.env*`, keys, and common credential filenames. Graphify performs code-only AST extraction without LLM calls. Review code for embedded secrets before registering it: filename exclusions cannot identify secrets hardcoded inside source code. Large repositories may exceed the job's temporary storage/resource limit; split them or prebuild artifacts on a development machine.

Each successful index publishes `graph.json` atomically and records its SHA-256, source commit (or an explicit unknown/packed-ref marker), timestamp, and Graphify version. Graphify reuses eligible cached extraction output where its own incremental rules permit. The sanitized temporary root can cause full re-extraction; no incremental speedup is promised. Retrieval reports freshness so stale indexes can be recognized.

For a development-machine artifact:

```sh
# On the development machine, using Graphify 0.9.91:
graphify extract /path/to/repo --code-only --no-cluster --out /path/to/export
# Output is /path/to/export/graphify-out/graph.json (the extra folder is intentional).
python -m scripts.manage register --project imported-project
python -m scripts.manage import-graph --project imported-project --artifact /path/to/export/graphify-out/graph.json
```

Import into the deployment's data root, then transfer that project's graph folder if importing on another machine. Raw Graphify nodes/edges and version-1 node-link exports are accepted; unsupported explicit schema versions fail. Imported source revision is marked unknown. Create client permissions for newly registered projects deliberately.

## 6. Knowledge and memory policy

Open `runtime/obsidian` as a vault through an authenticated NAS SMB share in Obsidian Desktop. There is no Obsidian server container. Templates are under `obsidian/Templates` and copied into the live vault during initialization. Place each project's notes in `Projects/PROJECT/`; gateway access remains inside that root, even if humans also use shared top-level Architecture/Development folders. Copy an approved shared convention into a project when that client needs it.

Agents create or update only `Projects/PROJECT/Agents/NAME.md`. Updates require the exact SHA-256 from `note_read`. Notes without the agent ownership frontmatter must be edited by a human. Avoid simultaneous SMB editing of the same agent-owned file: atomic replacement and optimistic hash checks detect ordinary conflicts, but SMB editors do not participate in the gateway lock.

Retrieve only context needed for the task. Prefer current code, verified documentation, active architecture decisions, relevant memories, then historical notes. Graph traversal, result count, query length, request bytes, and returned context are bounded. The gateway conservatively caps serialized result bytes using the configured token budget as a byte ceiling; it does not claim to implement a model-specific tokenizer. Truncated results are marked and retain source references.

`memory_store` requires a write-enabled token and `verified=true`. Store decisions/outcomes after checking them; do not capture every conversation. ICM enforces exact-content deduplication per topic. Each project has its own database, so project isolation does not depend on topic naming. Run one gateway worker/replica only; never attach another ICM service or CLI writer to these databases while the gateway is active.

## 7. Backups and recovery

Run `sh scripts/backup.sh` from a NAS scheduler during a quiet maintenance window. It briefly stops this stack, restarts it on exit, and retains the newest `BACKUP_KEEP` archives. Have humans close the SMB vault during the snapshot; the script cannot lock desktop editors. Operator index/import/backup jobs are mutually excluded by a lock file.

Example NAS cron entry, after replacing the path with the verified project location:

```cron
15 3 * * * cd /verified/local/path/ai-context-nas && sh scripts/backup.sh >> backups/schedule.log 2>&1
```

This is an installation example; no NAS schedule has been created. Use UGOS's task scheduler if available and set its timezone deliberately. Archives include SQLite databases made using the SQLite Online Backup API, graph artifacts/freshness metadata, the vault, project registry/configuration, and TLS identity. They do not include repository clones, which can be synchronized again, or client tokens and `.env`. Keep encrypted off-device copies of those secrets and the pinned repo revision separately. Protect backup archives because they include memories and CA private keys.

To test restoration into a separate folder:

```sh
docker compose --profile operations run --rm --no-deps maintenance python -m scripts.manage restore --archive /backups/context-TIMESTAMP.tar.gz --target /data/restore-test
```

Restoration verifies archive paths, file checksums, and SQLite integrity and refuses to replace nonempty data. To recover on another machine: obtain this pinned repository/image and secrets, initialize an empty local data root, restore into a new staging folder, stop gateway/TLS, copy restored `graphs`, `icm`, `obsidian`, and `tls` to the empty live root and restored `config` to the project config directory, set ownership, validate Compose, start, and run acceptance checks. Keep the previous data intact until those checks pass. Do not copy an active SQLite DB file directly.

## 8. Acceptance checks before relying on the NAS

Use the gateway from a real remote client to index a fixture, query a symbol and dependency, create/read an agent note, and store/recall a verified memory. Test invalid tokens, a read-only client's attempted write, and a request for another project. Refresh the source index and confirm the changed symbol. Restart the gateway container and verify the same note and memory remain. Restart the NAS in an approved window and repeat. Stop/start the gateway to test recovery. Back up, restore into staging, and recall a known restored memory using an isolated test instance.

Measure latency from the remote client, `docker stats --no-stream`, and `du -sh runtime/*`. These measurements must come from your NAS; local fixture timing is not a NAS performance estimate. Record results in [validation](documentation/validation.md).

Developer checks:

```sh
uv sync --frozen
# Set ICM_BINARY to a checksum-verified 0.11.4 native binary to enable real memory tests.
python -m pytest -q
docker compose --env-file .env.example config --quiet
```

See [troubleshooting](documentation/troubleshooting.md) for common failures. Preserve data and logs before upgrading pins; re-run tests and restoration after changes.

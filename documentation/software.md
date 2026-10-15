# Verified software and interfaces

Verified October 15, 2026 using official source, published package metadata, release assets, and client documentation. The sources are external software evidence, not instructions to operate this NAS.

| Component | Pin/evidence | Interface and storage used here |
|---|---|---|
| Graphify | `graphifyy==0.9.91`; inspected source `10130e79ed9caf8f60d998073e097531eaa1a395` | Real `graphify extract PATH --code-only --no-cluster --out ROOT --max-workers 2`; writes ROOT/graphify-out/graph.json. Adapter reads raw nodes/edges; separate artifacts per project. |
| ICM | 0.11.4; source `5f402434919e514109a95c6cf504427fbcef851f`; Cargo.lock | `icm --db PATH --no-embeddings store --topic TOPIC --content CONTENT --importance medium` and `recall QUERY --limit N --format json`; separate local SQLite DB per project. |
| MCP Python SDK | `mcp==1.30.0` | FastMCP Streamable HTTP, stateless JSON responses at `/mcp`; gateway adds bearer authentication and project access checks. Version 2.x exists but is deliberately outside this tested pin. |
| Obsidian | Desktop application; no server image/version assumed | Standard Markdown vault on authenticated SMB; confined gateway tools for agents. |
| Caddy | 2.10.2 manifest digest in Compose | Private CA HTTPS, no public ACME or admin port. |
| Python/Rust | Python 3.12.14 and Rust 1.96.0 manifest digests in Dockerfile | Python dependencies locked with wheel hashes; ICM built from pinned source with only backend-sqlite. |

## Graphify evidence

- [Official repository](https://github.com/Graphify-Labs/graphify) and [pinned project metadata](https://github.com/Graphify-Labs/graphify/blob/10130e79ed9caf8f60d998073e097531eaa1a395/pyproject.toml): the official PyPI name is **graphifyy**, while the command is `graphify`; Python 3.10+ and tree-sitter code analysis.
- [Pinned CLI implementation](https://github.com/Graphify-Labs/graphify/blob/10130e79ed9caf8f60d998073e097531eaa1a395/graphify/cli.py): code-only headless extraction, output root semantics, incremental cache handling, no-cluster raw exports. No model key is needed for code-only extraction. Semantic extraction of documents/media is deliberately outside this deployment.
- [Pinned MCP server](https://github.com/Graphify-Labs/graphify/blob/10130e79ed9caf8f60d998073e097531eaa1a395/graphify/serve.py): stdio and Streamable HTTP are supported. Verified native startup is `python -m graphify.serve /data/graph.json --transport http --host 0.0.0.0 --port 8080`; `GRAPHIFY_API_KEY` or `--api-key` enables authentication via X-API-Key or bearer headers. This deployment does not publish that native server; its gateway provides a smaller project-confined read surface.
- [Pinned export format](https://github.com/Graphify-Labs/graphify/blob/10130e79ed9caf8f60d998073e097531eaa1a395/graphify/export.py): clustered node-link exports use graph schema version 1; the tested `--no-cluster` path emits unversioned nodes/edges.
- AMD64/ARM64 are build targets using multi-architecture base images and upstream parser packages. Linux builds and ARM64 compatibility must be checked on those targets. No measured NAS RAM requirement is claimed. Indexing is on demand; retrieval is bounded to 64 MiB input graphs, 100 nodes, 200 edges, depth 0–4.

## ICM evidence

- [Official repository](https://github.com/rtk-ai/icm), [0.11.4 release](https://github.com/rtk-ai/icm/releases/tag/icm-v0.11.4), and [CLI contract](https://github.com/rtk-ai/icm/blob/5f402434919e514109a95c6cf504427fbcef851f/crates/icm-cli/src/main.rs): database selection, no-embeddings flag, store/recall/list/backup command syntax. Linux AMD64/ARM64 and Windows AMD64 release artifacts exist. The Windows test binary was checked against the official release checksums.
- [Cargo feature declarations](https://github.com/rtk-ai/icm/blob/5f402434919e514109a95c6cf504427fbcef851f/crates/icm-cli/Cargo.toml): CLI can build with `--no-default-features --features backend-sqlite`. HTTP requires the separate http-api feature. Native MCP uses stdio. There is no assumption that the HTTP API is MCP. This image does not start an ICM HTTP server, dashboard, automatic hook, summarizer, or extraction daemon.
- [SQLite backup implementation](https://github.com/rtk-ai/icm/blob/5f402434919e514109a95c6cf504427fbcef851f/crates/icm-store/src/store/maintenance.rs): upstream uses the SQLite Online Backup API. Our operator backup uses that same SQLite facility through Python sqlite3 with read-only source connections, integrity checks, and explicit connection closure.
- [Memory store](https://github.com/rtk-ai/icm/blob/5f402434919e514109a95c6cf504427fbcef851f/crates/icm-store/src/store/memory.rs): exact-content summary-hash deduplication. The local test repeated the same write and verified the same memory ID.
- Keywords are enabled initially. Embeddings are compiled out of the deployment image, avoiding model downloads and that runtime overhead. Compare retrieval quality/latency on your actual tasks before considering a separate embedding-enabled build; published benchmark numbers are not measurements of this NAS.

## Additional primary sources

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and the installed 1.30.0 FastMCP implementation were used to validate transport/context behavior with actual HTTP tool requests.
- [Caddy internal TLS](https://caddyserver.com/docs/caddyfile/directives/tls) and [request body limits](https://caddyserver.com/docs/caddyfile/directives/request_body).
- [SQLite online backup](https://www.sqlite.org/backup.html) and [Python sqlite3 backup](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.backup).
- [Obsidian](https://obsidian.md/) is a desktop Markdown application; it does not require an invented server container. See [client evidence](clients.md) for SMB and agent setup sources.

Image manifests were inspected through Docker's registry client without a local engine; this verified that the pinned manifests exist, not that the resulting images build or run successfully on the NAS.

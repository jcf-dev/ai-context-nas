# Task: Deploy a Centralized AI Context and Memory Server on UGREEN NAS

You are a senior DevOps engineer, Docker infrastructure architect, and AI agent systems engineer.

Design, implement, deploy, and validate a production-ready, self-hosted AI context infrastructure on my UGREEN NAS running UGOS Pro with Docker.

The infrastructure must provide centralized knowledge, code graph retrieval, and persistent memory for multiple AI agents running on different machines.

## 1. Objectives

Deploy and integrate:

1. **Graphify** — Source-code indexing, AST analysis, dependency graphs, and relationship-aware retrieval.
2. **Obsidian** — Shared Markdown knowledge vault for projects, architecture decisions, development conventions, and technical documentation.
3. **ICM (`rtk-ai/icm`)** — Persistent agent memory with retrieval across sessions.
4. **Context Gateway** — A lightweight, authenticated interface for remote AI agents, if required for interoperability.

Do not install Hermes Agent inside this stack. Hermes will be a separate client that connects to these services.

The infrastructure must support:

- Claude Code on macOS
- OpenAI Codex CLI on macOS and Windows
- Hermes Agent running in another NAS container
- Other compatible MCP or HTTP clients

Primary goals:

- Improve context accuracy.
- Reduce unnecessary token usage.
- Share durable knowledge across agents.
- Prevent project context contamination.
- Keep memory persistent across container restarts.
- Support secure LAN and optional VPN access.
- Minimize NAS CPU, RAM, and disk overhead.
- Avoid unnecessary databases and background services.

## 2. Environment Discovery

Before making changes:

1. Determine whether Codex has SSH access to the NAS.
2. Identify the NAS model, CPU architecture, installed RAM, UGOS Pro version, Docker version, and Compose availability.
3. Inspect existing Docker containers, networks, volumes, and port allocations.
4. Identify the correct persistent storage paths and shared folders.
5. Check available disk space and permissions.
6. Identify existing reverse proxies or VPN services.
7. Determine whether Graphify, ICM, or related services are already deployed.

If NAS access is unavailable, generate the deployment files locally and provide precise deployment instructions.

Do not assume that `/volume1` is the correct UGOS storage path.

Do not modify existing containers or configurations without determining their purpose.

## 3. Verify the Software

Research and inspect these repositories:

- Graphify: https://github.com/Graphify-Labs/graphify
- ICM: https://github.com/rtk-ai/icm
- Obsidian: https://obsidian.md/

Verify:

- Current supported versions.
- Docker and ARM64/AMD64 compatibility.
- Actual installation and startup commands.
- Persistent storage requirements.
- MCP and HTTP interfaces.
- Authentication mechanisms.
- Supported indexing and retrieval capabilities.
- Resource requirements.
- Relevant security limitations.

Do not invent Docker image names, command-line flags, API routes, or environment variables.

If a prebuilt image is unavailable, create a reproducible Dockerfile from a verified source revision.

Pin image versions or source revisions rather than relying on mutable `latest` tags.

## 4. Target Architecture

Implement:

    AI AGENTS
    ├── Claude Code (Mac)
    ├── Codex CLI (Mac/Windows)
    ├── Hermes Agent (separate container)
    └── Other compatible clients
                |
                | HTTPS / authenticated MCP
                v
       UGREEN NAS / UGOS Pro
                |
       Context Gateway (if needed)
                |
       ┌────────┼────────┐
       |        |        |
       v        v        v
    Graphify  Obsidian   ICM
       |      Vault      |
       v        v        v
    Code      Markdown  Persistent
    Graphs    Knowledge Memory
       |        |        |
       └────────┼────────┘
                |
         Persistent NAS Storage

Use an isolated Docker network for internal services.

Expose only the endpoints required by remote clients.

Do not expose raw databases or internal administration interfaces.

## 5. Persistent Storage

Create an appropriate persistent directory structure using verified UGOS Pro paths.

Suggested structure:

    ai-context/
    ├── compose.yaml
    ├── .env.example
    ├── graphify/
    │   ├── config/
    │   ├── graphs/
    │   └── Dockerfile
    ├── icm/
    │   ├── config/
    │   ├── data/
    │   └── Dockerfile
    ├── obsidian/
    │   ├── Projects/
    │   ├── Architecture/
    │   ├── Decisions/
    │   ├── Development/
    │   ├── Infrastructure/
    │   ├── Runbooks/
    │   └── Archive/
    ├── gateway/
    │   └── config/
    ├── repositories/
    ├── scripts/
    ├── documentation/
    └── backups/

Keep active databases and graph indexes on reliable local NAS storage.

Use separate writable paths for databases and read-only mounts for source repositories wherever practical.

Do not store credentials in Markdown notes.

## 6. Graphify Deployment

Deploy Graphify with:

- Persistent graph storage.
- HTTP MCP transport if officially supported.
- API-key authentication.
- Repository-specific graphs.
- AST-based indexing where supported.
- Incremental graph updates where supported.
- Configurable traversal depth.
- Bounded retrieval results.
- Index freshness tracking.

Provide a mechanism to register repositories and refresh indexes.

Support two repository ingestion methods:

1. Read-only Git clones on the NAS, updated through a controlled synchronization job.
2. Imported graph artifacts generated by development machines, if compatible.

Do not assume the NAS can access local Mac or Windows repositories.

Exclude dependency directories, generated files, credentials, and binary artifacts.

Do not automatically index all NAS files.

## 7. Obsidian Knowledge Vault

Obsidian is primarily a desktop application, so do not assume it requires a Docker container.

Host the Markdown vault on NAS persistent storage.

Enable two access methods:

**Human access**
- Open the vault from macOS or Windows through an authenticated SMB share.
- Document how to connect Obsidian Desktop to the shared vault.

**Agent access**
- Provide authenticated tools for searching, reading, creating, and updating Markdown notes.
- Prefer an established, maintained MCP server or lightweight API adapter if necessary.
- Restrict file access to the designated vault.
- Prevent path traversal and arbitrary filesystem access.
- Use atomic file updates and basic conflict detection.
- Avoid overwriting human-authored notes without approval.

Create templates for project overviews, architecture decisions, implementation notes, and troubleshooting records.

Use standard Markdown and YAML frontmatter.

## 8. ICM Deployment

Deploy the verified `rtk-ai/icm` implementation.

Configure:

- Persistent local database.
- Authenticated HTTP API where supported.
- Project-scoped memory retrieval.
- Memory storage and recall.
- Bounded search results.
- Backup and restore procedures.
- Resource-efficient retrieval.

Prefer keyword-based retrieval initially if supported.

Evaluate semantic embeddings only after measuring whether they improve retrieval quality enough to justify the resource cost.

Do not assume ICM's HTTP API is MCP-compatible.

If an MCP adapter is required, implement or install one only after verifying the actual API contract.

Avoid multiple services directly writing to the same SQLite database.

## 9. Shared Context Gateway

Determine whether a shared gateway is necessary.

If native MCP connections are sufficient, do not introduce a gateway merely for architectural symmetry.

If a gateway is needed, provide a small service supporting:

- Authenticated client access.
- Project-aware retrieval.
- Graphify queries.
- Obsidian note search.
- ICM memory recall.
- Retrieval result limits.
- Deduplication.
- Source references.
- Basic access logging.

Prefer stateless implementation.

Do not create another permanent memory database.

Support a configurable retrieval token budget.

The gateway must not automatically load all memories or notes for every request.

## 10. Security

Implement a least-privilege deployment.

Requirements:

- Unique credentials for each service.
- Secrets stored outside version-controlled files.
- Authenticated API and MCP endpoints.
- HTTPS for remote access.
- Private Docker networking.
- Minimal published ports.
- Read-only mounts wherever possible.
- No privileged containers unless strictly necessary.
- No unrestricted Docker socket mounts.
- No public internet exposure by default.
- Firewall or VPN restrictions.
- Reasonable request size and rate limits.
- Protection against path traversal and unauthorized file access.

Use Tailscale or an existing private VPN for access outside the LAN if available.

Never hardcode API tokens into generated documentation or Compose files.

## 11. Multi-Agent Integration

Create integration documentation and configuration examples for:

- Claude Code
- Codex CLI
- Hermes Agent
- Generic MCP clients

Use the verified configuration syntax for each client.

Explain how each agent can:

1. Retrieve repository dependencies from Graphify.
2. Search architectural knowledge from Obsidian.
3. Recall previous decisions from ICM.
4. Retrieve only project-relevant context.
5. Store verified outcomes without creating duplicates.

Do not automatically write memories after every conversation.

Implement a shared context policy that prioritizes:

1. Current source code.
2. Verified documentation.
3. Active architecture decisions.
4. Relevant persistent memories.
5. Historical notes.

Keep retrieval bounded and task-specific.

## 12. Docker Compose Requirements

Generate a deployable Docker Compose stack with:

- Verified images or Dockerfiles.
- Persistent bind mounts.
- Explicit container restart policies.
- Health checks where supported.
- Environment configuration.
- Isolated networking.
- Safe service dependencies.
- Reasonable resource limits.
- Log rotation.
- Appropriate UID/GID ownership.
- No unnecessary privileged access.

Include `.env.example` without actual secrets.

Validate the stack using:

    docker compose config

Build and start services only after configuration validation.

Inspect startup logs and verify application readiness.

Do not mark the deployment successful merely because containers are running.

## 13. Backups and Recovery

Implement consistent backups for:

- ICM persistent memory.
- Graphify graph artifacts.
- Obsidian Markdown vault.
- Configuration templates.
- Repository registry.
- Gateway configuration.

Use application-aware SQLite backup procedures where applicable.

Do not simply copy active SQLite database files while they are being written.

Create scheduled backups with configurable retention.

Test at least one restoration procedure.

Document how to recover the stack on another compatible machine.

## 14. Validation

Run functional tests for:

1. Graphify indexing and symbol retrieval.
2. Graphify dependency traversal.
3. Obsidian note creation and retrieval.
4. ICM memory storage and recall.
5. Data persistence after container restart.
6. Authentication enforcement.
7. Rejection of unauthorized requests.
8. Project isolation.
9. Repository index refresh.
10. Connectivity from a remote AI agent.
11. Recovery after a simulated service failure.
12. Backup restoration.

Measure basic latency, RAM consumption, and storage usage.

Report actual results rather than estimated improvements.

## 15. Deliverables

Produce:

- `compose.yaml`
- Dockerfiles where required
- `.env.example`
- Setup and initialization scripts
- Repository registration script
- Backup and restore scripts
- Health-check scripts
- Obsidian vault templates
- Claude Code MCP configuration example
- Codex CLI MCP configuration example
- Hermes integration instructions
- Architecture diagram
- README with installation and operating instructions
- Security and troubleshooting documentation

Make the deployment compatible with the UGOS Pro Docker Project interface where practical.

## 16. Execution Workflow

Follow these stages:

**Stage 1 — Discovery:** Inspect NAS access, Docker, storage, and architecture.

**Stage 2 — Verification:** Inspect official repositories and determine exact supported commands and deployment methods.

**Stage 3 — Design:** Choose the simplest secure architecture and present the implementation plan.

**Stage 4 — Build:** Generate the Compose stack, Dockerfiles, scripts, and configuration.

**Stage 5 — Validate:** Check Compose syntax, build images, and run local tests where possible.

**Stage 6 — Deploy:** Deploy to the NAS if authorized access is available.

**Stage 7 — Integrate:** Configure supported remote agent connections.

**Stage 8 — Test:** Verify retrieval, persistence, isolation, authentication, and recovery.

**Stage 9 — Document:** Produce operating instructions and a final deployment report.

Do not claim deployment or validation succeeded unless the relevant commands actually completed successfully.

## Definition of Done

The infrastructure is complete when:

- Graphify serves usable code graph queries.
- Obsidian knowledge is accessible to authorized agents and desktop clients.
- ICM persists and retrieves memories across sessions.
- Multiple agents can access the services over the network.
- Project isolation and authentication are enforced.
- Data survives container and NAS restarts.
- Backup and restore procedures are verified.
- Existing UGOS services remain unaffected.
- The stack can be managed through Docker Compose.
- The installation is documented and reproducible.

**Start by inspecting my environment and verifying the actual Graphify and ICM repositories. If SSH access to the NAS is unavailable, create the complete deployment project locally and explain exactly how to deploy it using UGOS Pro Docker Projects.**

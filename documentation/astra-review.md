# Astra review of code and implementation

Two independent Astra reviews covered the entire implementation at `061f73e`, followed by review of the fixes. Reviewed October 15, 2026. Scope included gateway authentication, project isolation, note handling, ICM integration, Graphify indexing, operator commands, Docker, CI, and the original task.

## Code quality and correctness

- **P1, fixed:** the read-only indexer could not create its operator lock. A dedicated writable `.operator` directory is shared by operator jobs; initialization creates it and Compose mounts it. CI now runs the real indexing container.
- **P1, fixed:** `.secrets/private.py` could enter Graphify output. Sanitization now explicitly excludes hidden credential directories. The real extraction regression checks both `.env` and `.secrets` sentinels.
- **P2, fixed:** backup/restore hashed whole files in memory, exceeding the maintenance limit for large attachments/databases. Checksums now use streaming `hashlib.file_digest`.

## Requirements and deployment

- **P2, fixed:** response limits made the tails of valid long notes unreachable. `note_read` now offers Unicode character offsets and `next_offset`; search excerpts center on matching text. A test reconstructs a Unicode note from bounded pages.
- Follow-up review found a slim/standard build-tag mismatch. A single `CONTEXT_VARIANT` now selects both the image tag and Docker build target, preventing slim content from being built under the standard tag.
- Follow-up review found case-folded search offsets could shift excerpts after characters such as `ß`. Offsets now map back to original characters, with a regression check.

Eight local tests pass using real Graphify and checksum-verified ICM. Native AMD64/ARM64 container checks must pass for each release: real indexing with read-only repositories, HTTPS/MCP authentication, both runtime editions, restart persistence, and maintenance backup/restore. Publication and actual NAS acceptance are recorded separately in [validation](validation.md).

The reviews found no demonstrated authentication or cross-project bypass within the documented trusted NAS/SMB boundary. This is a review result, not a security guarantee. Remote Claude/Codex/Hermes connections, backup scheduling, and device recovery remain acceptance work until recorded as completed.

A final deployment review accepted the `default_sni {$CONTEXT_HOST}` change after actual NAS clients connecting by IP initially failed TLS. Certificate verification remains enabled; live NAS HTTPS/MCP then passed. Astra also identified that older image-embedded Caddyfile templates should not override the active host configuration during recovery. Maintenance now mounts the active Caddyfile for backup. The actual stopped-snapshot restore included that configuration and successfully recalled the stored ICM fixture. See [NAS acceptance](validation.md) for measurements and remaining work.

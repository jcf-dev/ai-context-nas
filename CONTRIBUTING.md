# Contributing

Contributions, bug reports, documentation improvements, and tested NAS compatibility reports are welcome. Open an issue for a substantial feature before implementing it, then fork the repository and submit a pull request.

Use Python 3.12 and `uv sync --frozen`. Run `uv run pytest -q` and `docker compose --env-file .env.example config --quiet`. Integration tests need the pinned ICM executable on PATH (or `ICM_BINARY`) and Graphify; see the validation workflows for checksum verification. Container changes should pass HTTPS, restart persistence, and real Graphify extraction checks on both AMD64 and ARM64.

Keep authentication, project isolation, bounded responses, non-root containers, and confined file writes intact. Add a regression check for a behavioral fix. Explain the problem, resulting behavior, and validation in the pull request. Avoid unrelated formatting changes.

Never submit credentials, tokens, private source material, vault contents, databases, TLS keys, or NAS identifiers. Report an exploitable vulnerability privately through GitHub's security reporting when enabled; do not post secrets in a public issue.

Dependency changes must update `uv.lock` and both exported lock files. Generate the standard lock with `uv export --frozen --no-dev --format requirements-txt --output-file requirements.lock` and slim with the same command plus `--prune graphifyy --output-file requirements.slim.lock`. Keep upstream versions and container bases pinned, and preserve third-party license notices. Contributions are provided under the repository's MIT license.

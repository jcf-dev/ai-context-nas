"""Operator commands. Run from the repository root. Never accepts remote commands."""
from __future__ import annotations

import argparse
from contextlib import contextmanager, closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile

from gateway.core import atomic_write, confined, slug


def registry(config):
    return json.loads((config / "projects.json").read_text(encoding="utf-8"))


@contextmanager
def operation(data):
    """Exclude simultaneous index/backup/import/restore operator jobs."""
    data.mkdir(parents=True, exist_ok=True)
    path = data / ".operator.lock"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def initialize(root: Path, data: Path, uid: int, gid: int):
    if data == Path(data.anchor) or data == root or data.is_symlink():
        raise ValueError("Choose a dedicated data folder, separate from the project root")
    marker = data / ".ai-context-root"
    if data.exists() and any(data.iterdir()) and not marker.exists():
        raise ValueError("Existing nonempty folder is not an initialized AI context data root")
    data.mkdir(parents=True, exist_ok=True)
    marker.touch(exist_ok=True)
    for item in ("graphs", "icm", "repositories", "tls", "obsidian"):
        (data / item).mkdir(exist_ok=True)
    for item in ("Projects", "Architecture", "Decisions", "Development", "Infrastructure", "Runbooks", "Archive", "Templates"):
        (data / "obsidian" / item).mkdir(exist_ok=True)
    templates = root / "obsidian" / "Templates"
    if templates.exists():
        shutil.copytree(templates, data / "obsidian" / "Templates", dirs_exist_ok=True)
    secret = root / ".secrets"
    secret.mkdir(mode=0o700, exist_ok=True)
    backups = root / "backups"
    backups.mkdir(mode=0o700, exist_ok=True)
    if not (secret / "clients.json").exists():
        atomic_write(secret / "clients.json", b'{"clients": []}\n')
    if not (root / ".env").exists():
        content = (root / ".env.example").read_text(encoding="utf-8")
        # A relative runtime path also works when the prepared folder is copied to a NAS.
        content = content.replace("DATA_ROOT=./runtime", f"DATA_ROOT={data.as_posix()}")
        content = content.replace("PUID=10001", f"PUID={uid}").replace("PGID=10001", f"PGID={gid}")
        atomic_write(root / ".env", content.encode())
    if os.name == "posix" and os.geteuid() == 0:
        for path in [data, *data.rglob("*"), secret, *secret.iterdir(), backups]:
            if not path.is_symlink():
                os.chown(path, uid, gid)
    for path in secret.iterdir():
        path.chmod(0o600)
    print("Initialized persistent folders; register a project and create client credentials next.")


def register(config: Path, data: Path, project: str, url: str | None):
    slug(project)
    if url and (not (url.startswith("https://") or url.startswith("git@")) or "\n" in url):
        raise ValueError("Use a credential-free HTTPS URL or configured git@host:path URL")
    if url and url.startswith("https://"):
        from urllib.parse import urlparse
        if urlparse(url).username or urlparse(url).password or urlparse(url).query:
            raise ValueError("Credentials and query strings are not allowed in repository URLs")
    with operation(data):
        value = registry(config)
        if project in value["projects"]:
            raise ValueError("Project already registered; edit its registry deliberately")
        value["projects"][project] = {"url": url, "ingestion": "clone" if url else "artifact"}
        atomic_write(config / "projects.json", (json.dumps(value, indent=2) + "\n").encode())
        (config / "projects.json").chmod(0o644)
        for folder in (data / "icm" / project, data / "graphs" / project,
                       data / "obsidian" / "Projects" / project / "Agents"):
            folder.mkdir(parents=True, exist_ok=True)
    print(f"Registered {project}; no NAS-wide scan was performed.")


def client(root: Path, config: Path, name: str, projects: list[str], write: bool):
    slug(name)
    known = registry(config)["projects"]
    if not projects or any(p not in known for p in projects):
        raise ValueError("All client projects must be registered first")
    file = root / ".secrets" / "clients.json"
    value = json.loads(file.read_text())
    if any(c["id"] == name for c in value["clients"]):
        raise ValueError("Client exists; revoke it explicitly before creating a replacement")
    token = secrets.token_urlsafe(48)
    value["clients"].append({"id": name, "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                             "projects": projects, "write": write})
    atomic_write(file, (json.dumps(value, indent=2) + "\n").encode())
    destination = root / ".secrets" / f"{name}.env"
    atomic_write(destination, f"AI_CONTEXT_TOKEN={token}\n".encode())
    file.chmod(0o600)
    destination.chmod(0o600)
    print(f"Client {name} created. Retrieve its token locally from .secrets/{name}.env; restart gateway.")


def sync(config: Path, data: Path, project: str):
    slug(project)
    item = registry(config)["projects"][project]
    if not item["url"]:
        raise ValueError("Artifact-only project has no clone URL")
    target = data / "repositories" / project
    with operation(data):
        if not target.exists():
            subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", "--no-recurse-submodules", "--", item["url"], str(target)], check=True)
        else:
            origin = subprocess.check_output(["git", "-C", str(target), "remote", "get-url", "origin"], text=True).strip()
            if origin != item["url"]:
                raise ValueError("Clone origin differs from registry")
            clean = subprocess.check_output(["git", "-C", str(target), "status", "--porcelain"], text=True)
            if clean:
                raise ValueError("Refusing to sync a modified clone")
            subprocess.run(["git", "-C", str(target), "-c", "core.hooksPath=/dev/null", "pull", "--ff-only", "--no-recurse-submodules"], check=True)
    print(f"Synchronized {project}; run index separately.")


def validate_graph(path: Path):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Graph exceeds 64 MiB")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value.get("nodes"), list) or not isinstance(value.get("links", value.get("edges")), list):
        raise ValueError("Expected a Graphify nodes + links/edges artifact")
    if any(not isinstance(n, dict) or "id" not in n for n in value["nodes"]):
        raise ValueError("Invalid graph nodes")
    metadata = value.get("graph", {})
    # --no-cluster emits the raw nodes/edges extraction without graph metadata.
    # Clustered node-link exports carry schema_version=1 at this pinned release.
    version = metadata.get("schema_version")
    if version is not None and str(version) != "1":
        raise ValueError("Unsupported Graphify schema version")
    if version is None and "edges" not in value:
        raise ValueError("Unversioned imports must use the verified raw nodes/edges format")
    return value


def index(config: Path, data: Path, project: str):
    slug(project)
    registry(config)["projects"][project]
    source = data / "repositories" / project
    if not source.is_dir():
        raise ValueError("Sync the registered repository first")
    out = data / "graphs" / project
    out.mkdir(parents=True, exist_ok=True)
    with operation(data):
        # Stage a sanitized copy: hooks, symlinks, dependency trees and secrets
        # cannot be reached by the parser. The original clone is read-only.
        with tempfile.TemporaryDirectory(prefix=".index-", dir=out.parent) as temp:
            clean = Path(temp) / "source"
            ignore = shutil.ignore_patterns(".git", "node_modules", "vendor", "dist", "build", ".venv", "venv",
                                            ".env*", "*.pem", "*.key", "credentials*", "secrets*", "__pycache__")
            def safe_ignore(folder, names):
                return set(ignore(folder, names)) | {name for name in names if (Path(folder) / name).is_symlink()}
            shutil.copytree(source, clean, ignore=safe_ignore)
            # Reuse previous output/manifest for native incremental extraction.
            staged = Path(temp) / "output" / "graphify-out"
            shutil.copytree(out, staged, dirs_exist_ok=True)
            subprocess.run(["graphify", "extract", str(clean), "--code-only", "--no-cluster",
                            "--out", str(staged.parent), "--max-workers", "2"], check=True, timeout=1800)
            graph = staged / "graph.json"
            parsed = validate_graph(graph)
            # Source and graph data are promoted only after extraction succeeds.
            for artifact in staged.iterdir():
                if artifact.is_file() and artifact.name != "graph.json":
                    atomic_write(out / artifact.name, artifact.read_bytes())
            commit = (source / ".git" / "HEAD").read_text().strip() if (source / ".git" / "HEAD").exists() else "unknown"
            if commit.startswith("ref: "):
                ref = source / ".git" / commit[5:]
                commit = ref.read_text().strip() if ref.exists() else "see clone git log (packed ref)"
            freshness = {"indexed_at": datetime.now(timezone.utc).isoformat(), "commit": commit,
                         "graphify_version": "0.9.91", "schema_version": parsed.get("graph", {}).get("schema_version"),
                         "sha256": hashlib.sha256(graph.read_bytes()).hexdigest()}
            atomic_write(out / "graph.json", graph.read_bytes())
            atomic_write(out / "index.json", json.dumps(freshness).encode())
    print(f"Indexed {project}; graph and freshness metadata published.")


def import_graph(config: Path, data: Path, project: str, artifact: Path):
    slug(project)
    registry(config)["projects"][project]
    validate_graph(artifact)
    with operation(data):
        out = data / "graphs" / project
        atomic_write(out / "graph.json", artifact.read_bytes())
        atomic_write(out / "index.json", json.dumps({"imported_at": datetime.now(timezone.utc).isoformat(),
                     "commit": "unknown-imported", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}).encode())
    print("Imported a validated graph; source commit is unverified unless supplied separately by the operator.")


def backup(config: Path, data: Path, backups: Path, keep: int):
    if keep < 1:
        raise ValueError("Retain at least one backup")
    backups.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backups / f"context-{stamp}.tar.gz"
    with operation(data), tempfile.TemporaryDirectory(prefix=".backup-", dir=data) as temp:
        stage = Path(temp)
        for folder in ("graphs", "obsidian", "tls"):
            if (data / folder).exists():
                if any(p.is_symlink() for p in (data / folder).rglob("*")):
                    raise ValueError("Backup source contains symlinks; resolve them first")
                shutil.copytree(data / folder, stage / folder, symlinks=False)
        shutil.copytree(config, stage / "config")
        deployment = Path(__file__).resolve().parent.parent
        for name in ("compose.yaml", ".env.example", "pyproject.toml", "requirements.lock", "uv.lock",
                     "gateway/Caddyfile", "gateway/Dockerfile"):
            template = deployment / name
            if template.is_file():
                target = stage / "deployment" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(template, target)
        for db in (data / "icm").glob("*/memory.db"):
            target = stage / "icm" / slug(db.parent.name) / "memory.db"
            target.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as source, closing(sqlite3.connect(target)) as output:
                source.backup(output)
                if output.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Database backup integrity failed")
        manifest = {str(p.relative_to(stage)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in stage.rglob("*") if p.is_file()}
        (stage / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        partial = destination.with_suffix(".partial")
        try:
            with tarfile.open(partial, "w:gz") as archive:
                for file in stage.iterdir():
                    archive.add(file, arcname=file.name)
            partial.chmod(0o600)
            os.replace(partial, destination)
        finally:
            partial.unlink(missing_ok=True)
    for old in sorted(backups.glob("context-*.tar.gz"), reverse=True)[keep:]:
        old.unlink()
    print(destination.name)
    return destination


def restore(archive: Path, target: Path):
    # Restore only to an empty staging root. An operator promotes it while services are stopped.
    if target.exists() and any(target.iterdir()):
        raise ValueError("Restore target must be new or empty")
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if sum(m.size for m in members) > 20 * 1024**3:
            raise ValueError("Backup exceeds 20 GiB restore cap")
        for member in members:
            confined(target, member.name)
            if not (member.isfile() or member.isdir()):
                raise ValueError("Links and special files are forbidden in backups")
        source.extractall(target, filter="data")
    manifest = json.loads((target / "manifest.json").read_text())
    for name, expected in manifest.items():
        if hashlib.sha256(confined(target, name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Backup checksum mismatch: {name}")
    for db in (target / "icm").glob("*/memory.db"):
        with closing(sqlite3.connect(db)) as conn:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Restored database integrity failed")
    print("Restored to staging; checksums and SQLite integrity verified. Live data was not replaced.")


def main():
    from dotenv import load_dotenv
    load_dotenv(override=False)
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--data-root", type=Path, default=Path(os.getenv("DATA_ROOT", "runtime")))
    parser.add_argument("--config-root", type=Path, default=Path(os.getenv("CONFIG_ROOT", "config")))
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--uid", type=int, default=10001)
    init.add_argument("--gid", type=int, default=10001)
    reg = sub.add_parser("register")
    reg.add_argument("--project", required=True)
    reg.add_argument("--url")
    credential = sub.add_parser("client")
    credential.add_argument("--name", required=True)
    credential.add_argument("--projects", nargs="+", required=True)
    credential.add_argument("--write", action="store_true")
    for command in ("sync", "index", "import-graph"):
        item = sub.add_parser(command)
        item.add_argument("--project", required=True)
        if command == "import-graph":
            item.add_argument("--artifact", type=Path, required=True)
    save = sub.add_parser("backup")
    save.add_argument("--destination", type=Path, default=Path("backups"))
    save.add_argument("--keep", type=int, default=int(os.getenv("BACKUP_KEEP", "14")))
    load = sub.add_parser("restore")
    load.add_argument("--archive", type=Path, required=True)
    load.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    root, data, config = args.root.resolve(), args.data_root.resolve(), args.config_root.resolve()
    if args.command == "init": initialize(root, data, args.uid, args.gid)
    elif args.command == "register": register(config, data, args.project, args.url)
    elif args.command == "client": client(root, config, args.name, args.projects, args.write)
    elif args.command == "sync": sync(config, data, args.project)
    elif args.command == "index": index(config, data, args.project)
    elif args.command == "import-graph": import_graph(config, data, args.project, args.artifact)
    elif args.command == "backup": backup(config, data, args.destination, args.keep)
    elif args.command == "restore": restore(args.archive, args.target)


if __name__ == "__main__":
    main()

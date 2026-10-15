"""Project-confined adapters. No client-supplied filesystem or command paths."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import stat
import tempfile
import threading
from collections import deque

SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,62}\Z")


def slug(value: str) -> str:
    if not SLUG.fullmatch(value):
        raise ValueError("Use a lowercase project/name slug (letters, numbers, hyphens)")
    return value


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".context-", dir=path.parent)
    try:
        if path.exists():
            existing = path.stat()
            os.chmod(temp, stat.S_IMODE(existing.st_mode))
            if os.name == "posix" and os.geteuid() == 0:
                os.fchown(fd, existing.st_uid, existing.st_gid)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def confined(root: Path, relative: str) -> Path:
    if not relative or "\\" in relative or ":" in relative:
        raise ValueError("Use a relative vault path with forward slashes")
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Path traversal rejected")
    # Reject symlinks even when their current target happens to be in the vault.
    for item in [root, *path.parents, path]:
        if item.is_symlink():
            raise ValueError("Symlinks are not allowed")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes project vault")
    return path


def bounded(value: object, tokens: int, maximum: int = 2000) -> dict:
    """Conservative UTF-8 byte budget; does not claim an exact model tokenizer."""
    budget = min(maximum, max(128, tokens))
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    encoded = text.encode("utf-8")
    if len(encoded) <= budget:
        return {"data": value, "truncated": False}
    return {"preview": encoded[:budget].decode("utf-8", errors="ignore"), "truncated": True}


class ContextStore:
    def __init__(self, data: Path, config: Path, icm: str = "icm"):
        self.data, self.config, self.icm = data, config, icm
        self._locks: dict[str, threading.RLock] = {}
        self._locks_guard = threading.Lock()

    def projects(self) -> dict:
        return json.loads((self.config / "projects.json").read_text())["projects"]

    def check(self, project: str, claims: dict, write: bool = False) -> str:
        slug(project)
        if project not in claims.get("projects", []) or project not in self.projects():
            raise PermissionError("Project access denied")
        if write and not claims.get("write", False):
            raise PermissionError("Write access denied")
        return project

    def lock(self, project: str):
        with self._locks_guard:
            return self._locks.setdefault(project, threading.RLock())

    def vault(self, project: str) -> Path:
        return self.data / "obsidian" / "Projects" / slug(project)

    def search_notes(self, project: str, query: str, limit: int) -> list:
        if not query.strip() or len(query) > 500:
            raise ValueError("Provide a search query of 1-500 characters")
        root = self.vault(project)
        hits = []
        for path in sorted(root.rglob("*.md"))[:5000]:
            safe = confined(root, path.relative_to(root).as_posix())
            if not safe.is_file() or safe.stat().st_size > 65536:
                continue
            text = safe.read_text(encoding="utf-8")
            if query.casefold() in text.casefold():
                # Center the excerpt on the match so late-note hits are useful.
                folded_match = text.casefold().find(query.casefold())
                folded_cursor = 0
                for match, character in enumerate(text):
                    folded_cursor += len(character.casefold())
                    if folded_cursor > folded_match:
                        break
                start = max(0, match - 160)
                hits.append({"source": f"vault://{project}/{path.relative_to(root).as_posix()}",
                             "excerpt": text[start:start + 800]})
                if len(hits) >= min(20, max(1, limit)):
                    break
        return hits

    def read_note(self, project: str, relative: str) -> dict:
        path = confined(self.vault(project), relative)
        if path.suffix.lower() != ".md" or path.stat().st_size > 65536:
            raise ValueError("Only Markdown notes up to 64 KiB can be read")
        content = path.read_bytes()
        return {"source": f"vault://{project}/{relative}",
                "sha256": hashlib.sha256(content).hexdigest(), "content": content.decode("utf-8")}

    def write_note(self, project: str, name: str, content: str, expected_sha256: str | None) -> dict:
        slug(name)
        if len(content.encode("utf-8")) > 32000:
            raise ValueError("Note exceeds 32 KiB")
        relative = f"Agents/{name}.md"
        path = confined(self.vault(project), relative)
        with self.lock(project):
            if path.exists():
                old = path.read_bytes()
                if not old.startswith(b"---\ncreated_by: ai-context\n"):
                    raise PermissionError("Human-authored notes require a human editor")
                if hashlib.sha256(old).hexdigest() != expected_sha256:
                    raise ValueError("Conflict: read the latest note and supply its SHA-256")
            elif expected_sha256 is not None:
                raise ValueError("Conflict: note no longer exists")
            body = f"---\ncreated_by: ai-context\nproject: {project}\n---\n\n{content}"
            atomic_write(path, body.encode("utf-8"))
        return self.read_note(project, relative)

    def graph_query(self, project: str, query: str, depth: int, limit: int) -> dict:
        if not query.strip() or len(query) > 500:
            raise ValueError("Provide a graph query of 1-500 characters")
        folder = self.data / "graphs" / slug(project)
        graph_path = folder / "graph.json"
        if graph_path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("Graph exceeds 64 MiB; split this repository into smaller projects")
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes = {str(n["id"]): n for n in graph["nodes"]}
        edges = graph.get("links", graph.get("edges", []))
        terms = query.casefold().split()
        seeds = [key for key, n in nodes.items()
                 if any(term in (str(n.get("label", "")) + " " + str(n.get("source_file", ""))).casefold()
                        for term in terms)][:10]
        neighbors: dict[str, list] = {}
        for edge in edges:
            source, target = str(edge["source"]), str(edge["target"])
            neighbors.setdefault(source, []).append(target)
            neighbors.setdefault(target, []).append(source)
        queue, seen = deque((node, 0) for node in seeds), set()
        max_nodes = min(100, max(1, limit))
        while queue and len(seen) < max_nodes:
            node, distance = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            if distance < min(4, max(0, depth)):
                for neighbor in neighbors.get(node, []):
                    if neighbor not in seen and len(queue) < 500:
                        queue.append((neighbor, distance + 1))
        metadata = folder / "index.json"
        return {"source": f"graph://{project}/graph.json", "freshness": json.loads(metadata.read_text()) if metadata.exists() else {"status": "unknown"},
                "nodes": [nodes[k] for k in sorted(seen) if k in nodes],
                "edges": [e for e in edges if str(e["source"]) in seen and str(e["target"]) in seen][:200]}

    def memory(self, project: str, args: list[str]) -> str:
        folder = self.data / "icm" / slug(project)
        folder.mkdir(parents=True, exist_ok=True)
        # No HTTP/MCP ICM daemon or second gateway replica may access this DB.
        # Both reads (which can update recall metadata) and writes share this lock.
        with self.lock(project):
            result = subprocess.run([self.icm, "--db", str(folder / "memory.db"), "--no-embeddings", *args],
                                    capture_output=True, text=True, encoding="utf-8", timeout=30,
                                    env={**os.environ, "ICM_NO_EMBEDDINGS": "1", "ICM_DB_BACKEND": "sqlite"})
            if result.returncode:
                raise RuntimeError("ICM command failed; inspect server logs locally")
            if len(result.stdout.encode("utf-8")) > 2 * 1024 * 1024:
                raise ValueError("ICM result too large")
            return result.stdout

    def recall(self, project: str, query: str, limit: int) -> dict:
        if not query.strip() or len(query) > 500:
            raise ValueError("Provide a query of 1-500 characters")
        output = self.memory(project, ["recall", query, "--limit", str(min(20, max(1, limit))), "--format", "json"])
        return {"source": f"icm://{project}", "memories": json.loads(output)}

    def remember(self, project: str, topic: str, content: str, verified: bool) -> dict:
        slug(topic)
        if not verified or not content.strip() or len(content.encode("utf-8")) > 8000:
            raise ValueError("Store only explicitly verified outcomes, up to 8 KiB")
        # Verified ICM schema enforces (topic, summary_hash) uniqueness. Repeating
        # this store reuses the existing memory instead of scanning all memories.
        with self.lock(project):
            output = self.memory(project, ["store", "--topic", topic, "--content", content.strip(), "--importance", "medium"])
            return {"source": f"icm://{project}/{topic}", "result": output.strip()}

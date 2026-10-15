import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tarfile
import time

import pytest
from starlette.testclient import TestClient

from gateway.app import create_app
from gateway.core import ContextStore, atomic_write, bounded, confined
from scripts.manage import backup, index, register, restore


@pytest.fixture
def environment(tmp_path):
    data, config = tmp_path / "data", tmp_path / "config"
    config.mkdir()
    atomic_write(config / "projects.json", b'{"projects": {}}')
    register(config, data, "alpha", None)
    register(config, data, "beta", None)
    token = "test-only-token-never-a-deployment-secret"
    credentials = tmp_path / "clients.json"
    credentials.write_text(json.dumps({"clients": [
        {"id": "writer", "token_sha256": hashlib.sha256(token.encode()).hexdigest(), "projects": ["alpha"], "write": True},
        {"id": "reader", "token_sha256": hashlib.sha256(b"read-token").hexdigest(), "projects": ["alpha"], "write": False}]}))
    return data, config, credentials, token


def rpc(client, token, name, arguments):
    response = client.post("/mcp", headers={"Authorization": f"Bearer {token}",
                          "Accept": "application/json, text/event-stream"},
                          json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                "params": {"name": name, "arguments": arguments}})
    assert response.status_code == 200, response.text
    result = response.json()["result"]
    return result


def test_http_auth_isolation_and_writes(environment):
    data, config, credentials, token = environment
    with TestClient(create_app(data, config, credentials)) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/mcp").status_code == 401
        assert client.post("/mcp", headers={"Authorization": "Bearer wrong"}).status_code == 401
        denied = rpc(client, token, "note_search", {"project": "beta", "query": "x"})
        assert denied["isError"]
        denied = rpc(client, "read-token", "note_write", {"project": "alpha", "name": "x", "content": "y"})
        assert denied["isError"]
        result = rpc(client, token, "note_write", {"project": "alpha", "name": "decision", "content": "Postgres selected"})
        assert not result.get("isError")
        result = rpc(client, token, "note_search", {"project": "alpha", "query": "Postgres"})
        assert "decision.md" in json.dumps(result)
        denied = rpc(client, token, "note_read", {"project": "alpha", "path": "../../beta/private.md"})
        assert denied["isError"]
        assert client.post("/mcp", headers={"Authorization": f"Bearer {token}"}, content=b"x" * 65537).status_code == 413


def test_conflict_detection_and_human_notes(environment):
    data, config, _, _ = environment
    store = ContextStore(data, config)
    first = store.write_note("alpha", "decision", "one", None)
    with pytest.raises(ValueError, match="Conflict"):
        store.write_note("alpha", "decision", "two", "stale")
    second = store.write_note("alpha", "decision", "two", first["sha256"])
    assert second["sha256"] != first["sha256"]
    atomic_write(data / "obsidian/Projects/alpha/Agents/human.md", b"Human authored")
    with pytest.raises(PermissionError):
        store.write_note("alpha", "human", "overwrite", None)
    for path in ("../secret.md", "/etc/passwd", "C:/secret.md", "..\\secret.md"):
        with pytest.raises(ValueError): confined(store.vault("alpha"), path)


def test_read_budget():
    result = bounded("text" * 5000, 128)
    assert result["truncated"] and len(result["preview"].encode()) <= 128


def test_real_graphify_index_traversal_refresh(environment):
    data, config, _, _ = environment
    repo = data / "repositories/alpha"
    repo.mkdir(parents=True)
    (repo / "sample.py").write_text("def helper():\n    return 1\n\ndef caller():\n    return helper()\n")
    (repo / ".env").write_text("def secret_sentinel(): pass")
    index(config, data, "alpha")
    store = ContextStore(data, config)
    result = store.graph_query("alpha", "caller", 2, 20)
    assert any("caller" in n.get("label", "") for n in result["nodes"])
    assert any("helper" in n.get("label", "") for n in result["nodes"])
    assert result["edges"]
    assert "secret_sentinel" not in (data / "graphs/alpha/graph.json").read_text()
    with pytest.raises(FileNotFoundError):
        store.graph_query("beta", "caller", 1, 20)
    (repo / "sample.py").write_text("def refreshed_symbol():\n    return 2\n")
    index(config, data, "alpha")
    result = store.graph_query("alpha", "refreshed_symbol", 1, 20)
    assert any("refreshed_symbol" in n.get("label", "") for n in result["nodes"])
    assert not any("caller" in n.get("label", "") for n in result["nodes"])


@pytest.mark.skipif(not os.getenv("ICM_BINARY"), reason="Set ICM_BINARY to a verified native ICM binary")
def test_real_icm_persistence_dedup_recovery_and_restore(environment, tmp_path):
    data, config, credentials, token = environment
    binary = os.environ["ICM_BINARY"]
    store = ContextStore(data, config, binary)
    first = store.remember("alpha", "decisions", "Project orchid uses SQLite WAL storage", True)
    second = store.remember("alpha", "decisions", "Project orchid uses SQLite WAL storage", True)
    assert first["result"] == second["result"]
    assert store.recall("alpha", "orchid", 5)["memories"]
    assert not store.recall("beta", "orchid", 5)["memories"]
    with TestClient(create_app(data, config, credentials, binary)) as client:
        assert not rpc(client, token, "memory_recall", {"project": "alpha", "query": "orchid"}).get("isError")
    # A new gateway instance uses the same persisted DB after the previous stops.
    with TestClient(create_app(data, config, credentials, binary)) as client:
        assert "orchid" in json.dumps(rpc(client, token, "memory_recall", {"project": "alpha", "query": "orchid"}))
    broken = ContextStore(data, config, str(tmp_path / "missing-icm"))
    with pytest.raises(FileNotFoundError): broken.recall("alpha", "orchid", 5)
    assert store.recall("alpha", "orchid", 5)["memories"]
    archive = backup(config, data, tmp_path / "backups", 2)
    restored = tmp_path / "restored"
    restore(archive, restored)
    recovered = ContextStore(restored, restored / "config", binary)
    assert recovered.recall("alpha", "orchid", 5)["memories"]


def test_restore_rejects_traversal_and_live_overwrite(tmp_path):
    archive = tmp_path / "malicious.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.addfile(tarfile.TarInfo("../escape"))
    with pytest.raises(ValueError): restore(archive, tmp_path / "target")
    target = tmp_path / "live"
    target.mkdir()
    (target / "important").write_text("preserve")
    with pytest.raises(ValueError, match="empty"): restore(archive, target)

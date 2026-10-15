from __future__ import annotations

import asyncio
from collections import defaultdict, deque
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import time

from mcp.server.fastmcp import Context, FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from gateway.core import ContextStore, bounded

LOG = logging.getLogger("ai-context.access")


class Gate:
    def __init__(self, app, credentials: Path):
        self.app = app
        self.clients = json.loads(credentials.read_text(encoding="utf-8"))["clients"]
        if not self.clients or any(len(c.get("token_sha256", "")) != 64 for c in self.clients):
            raise ValueError("Configure hashed client credentials before starting")
        self.rates = defaultdict(deque)
        self.active = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if scope["path"] == "/health":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        supplied = headers.get(b"authorization", b"").decode("latin1")
        digest = hashlib.sha256(supplied[7:].encode()).hexdigest() if supplied.startswith("Bearer ") else ""
        claims = next((c for c in self.clients if hmac.compare_digest(c["token_sha256"], digest)), None)
        async def reject(status, message):
            LOG.info("method=%s path=%s status=%s", scope["method"], scope["path"], status)
            await JSONResponse({"error": message}, status_code=status)(scope, receive, send)
        if claims is None:
            return await reject(401, "Bearer token required")
        rate = self.rates[claims["id"]]
        now = time.monotonic()
        while rate and now - rate[0] > 60:
            rate.popleft()
        if len(rate) >= 60 or self.active >= 16:
            return await reject(429, "Request limit reached")
        rate.append(now)
        # Read and cap real bytes, including chunked requests and misleading headers.
        self.active += 1
        started = time.monotonic()
        status = 500
        try:
            body = bytearray()
            while True:
                try:
                    event = await asyncio.wait_for(receive(), timeout=10)
                except TimeoutError:
                    return await reject(408, "Request body timeout")
                if event["type"] == "http.disconnect":
                    return
                body.extend(event.get("body", b""))
                if len(body) > 65536:
                    return await reject(413, "Request exceeds 64 KiB")
                if not event.get("more_body", False):
                    break
            scope.setdefault("state", {})["claims"] = claims
            delivered = False
            async def replay():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()
            async def counted(message):
                nonlocal status
                if message["type"] == "http.response.start":
                    status = message["status"]
                await send(message)
            await self.app(scope, replay, counted)
        finally:
            self.active -= 1
            LOG.info("client=%s method=%s path=%s status=%s ms=%.1f", claims["id"], scope["method"],
                     scope["path"], status, (time.monotonic() - started) * 1000)


def create_app(data: Path | None = None, config: Path | None = None, credentials: Path | None = None,
               icm: str = "icm"):
    data = data or Path(os.getenv("DATA_ROOT", "/data"))
    config = config or Path(os.getenv("CONFIG_ROOT", "/config"))
    credentials = credentials or Path("/run/secrets/clients")
    store = ContextStore(data, config, icm)
    store.projects()  # Fail startup on an invalid registry.
    maximum = min(8000, max(128, int(os.getenv("MAX_CONTEXT_TOKENS", "2000"))))
    mcp = FastMCP("NAS AI Context", host="0.0.0.0", port=8080, stateless_http=True, json_response=True)

    def authorize(ctx: Context, project: str, write=False):
        request = ctx.request_context.request
        if request is None:
            raise PermissionError("Authenticated HTTP request required")
        return store.check(project, request.state.claims, write)

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request):
        return JSONResponse({"status": "ready", "service": "ai-context"})

    @mcp.tool()
    async def graph_query(project: str, query: str, ctx: Context, depth: int = 1,
                    limit: int = 20, token_budget: int = 2000) -> dict:
        """Retrieve Graphify symbols and dependency edges for one allowed project."""
        authorize(ctx, project)
        result = await asyncio.to_thread(store.graph_query, project, query, depth, limit)
        return {"source": result["source"], "freshness": result["freshness"],
                **bounded(result, token_budget, maximum)}

    @mcp.tool()
    async def note_search(project: str, query: str, ctx: Context, limit: int = 5,
                    token_budget: int = 2000) -> dict:
        """Find Markdown knowledge within one project; source references included."""
        authorize(ctx, project)
        result = await asyncio.to_thread(store.search_notes, project, query, limit)
        return {"sources": [hit["source"] for hit in result], **bounded(result, token_budget, maximum)}

    @mcp.tool()
    async def note_read(project: str, path: str, ctx: Context, token_budget: int = 2000) -> dict:
        """Read a project Markdown note and get its conflict-detection hash."""
        authorize(ctx, project)
        note = await asyncio.to_thread(store.read_note, project, path)
        return {"source": note["source"], "sha256": note["sha256"],
                **bounded(note["content"], token_budget, maximum)}

    @mcp.tool()
    async def note_write(project: str, name: str, content: str, ctx: Context,
                   expected_sha256: str | None = None) -> dict:
        """Create/update an agent-owned note. Human-authored notes need a human editor.

        Updates require the exact SHA-256 returned by note_read. Name is a slug.
        """
        authorize(ctx, project, write=True)
        note = await asyncio.to_thread(store.write_note, project, name, content, expected_sha256)
        return {"source": note["source"], "sha256": note["sha256"]}

    @mcp.tool()
    async def memory_recall(project: str, query: str, ctx: Context, limit: int = 5,
                      token_budget: int = 2000) -> dict:
        """Recall project-specific ICM memory using keywords, without embeddings."""
        authorize(ctx, project)
        result = await asyncio.to_thread(store.recall, project, query, limit)
        return {"source": f"icm://{project}", **bounded(result, token_budget, maximum)}

    @mcp.tool()
    async def memory_store(project: str, topic: str, content: str, verified: bool, ctx: Context) -> dict:
        """Store an explicitly verified outcome. Do not store every conversation.

        Current code and active decisions override historical memories.
        """
        authorize(ctx, project, write=True)
        return await asyncio.to_thread(store.remember, project, topic, content, verified)

    return Gate(mcp.streamable_http_app(), credentials)


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    # One worker is required: process-local locks serialize ICM and note updates.
    uvicorn.run(create_app(), host="0.0.0.0", port=8080, access_log=False, workers=1)

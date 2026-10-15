"""Remote acceptance against a dedicated disposable project, with real TLS/MCP."""
import argparse
import json
import ssl
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dotenv import dotenv_values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://context.nas.internal:8443/mcp")
    parser.add_argument("--ca", required=True)
    parser.add_argument("--credentials", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--recall-only", action="store_true")
    args = parser.parse_args()
    token = dotenv_values(args.credentials)["AI_CONTEXT_TOKEN"]
    tls = ssl.create_default_context(cafile=args.ca)
    if not args.url.startswith("https://"):
        raise ValueError("Remote smoke tests require HTTPS")

    def rpc(method, params, credential=token):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        request = Request(args.url, data=body, headers={"Authorization": f"Bearer {credential}",
                          "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                          "MCP-Protocol-Version": "2025-06-18"})
        with urlopen(request, context=tls, timeout=30) as response:
            value = json.load(response)
        if "error" in value:
            raise ValueError("MCP JSON-RPC error")
        return value["result"]

    def tool(tool_name, **arguments):
        value = rpc("tools/call", {"name": tool_name, "arguments": {"project": args.project, **arguments}})
        if value.get("isError"):
            raise ValueError(f"Tool {tool_name} failed")
        return value

    rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "ai-context-acceptance", "version": "0.1.0"}})
    assert len(rpc("tools/list", {})["tools"]) == 6
    try:
        rpc("tools/list", {}, credential="deliberately-invalid")
    except HTTPError as error:
        assert error.code == 401
    else:
        raise AssertionError("Invalid token was accepted")
    if not args.recall_only:
        tool("note_write", name="deployment-smoke", content="Deployment smoke verified: orchid sentinel")
        tool("memory_store", topic="deployment-smoke", content="Deployment smoke verified: orchid sentinel", verified=True)
    assert "orchid sentinel" in json.dumps(tool("note_read", path="Agents/deployment-smoke.md"))
    assert "orchid sentinel" in json.dumps(tool("memory_recall", query="orchid sentinel"))
    print("HTTPS trust, MCP initialization, tools, rejected token, note and memory persistence passed.")


if __name__ == "__main__":
    main()

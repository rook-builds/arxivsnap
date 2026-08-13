"""arxivsnap MCP server — stateless HTTP server for AI agent use.

Implements the MCP 2026-07-28 specification:
  https://spec.modelcontextprotocol.io/specification/2026-07-28/

Each request is a single HTTP POST to /mcp — no session state, no lifecycle.
The handle_mcp_request() pure function is fully unit-testable without a server.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from .core import fetch, to_text

_VERSION = "0.2.0"
_SPEC_VERSION = "2026-07-28"

_TOOL_SCHEMA = {
    "name": "fetch",
    "description": (
        "Fetch recent arXiv papers matching a search query. "
        "Returns markdown with titles, authors, dates, abstracts, and links."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "arXiv search query (e.g. 'machine learning agents'). "
                    "Defaults to 'ti:agent OR ti:llm' if not provided."
                ),
            },
            "limit": {
                "type": "integer",
                "description": "Number of papers to fetch (default 10, max 100).",
                "default": 10,
            },
        },
        "required": [],
    },
}


def handle_mcp_request(body: dict) -> dict:
    """Pure function — takes a parsed MCP request dict, returns a response dict.

    Handles:
      - {"method": "tools/list"} → JSON Schema for the fetch tool
      - {"method": "tools/call", "params": {"name": "fetch", "arguments": {...}}}
        → calls fetch() + to_text(), returns markdown content
      - anything else → {"error": "<reason>"}
    """
    method = body.get("method")
    if method is None:
        return {"error": "missing method"}

    if method == "tools/list":
        return {"tools": [_TOOL_SCHEMA]}

    if method == "tools/call":
        params = body.get("params") or {}
        name = params.get("name")
        if name != "fetch":
            return {"error": f"unknown tool: {name}"}
        arguments = params.get("arguments") or {}
        query = arguments.get("query") or None
        try:
            limit = int(arguments.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        try:
            items = fetch(query=query, limit=limit)
            text = to_text(items)
        except Exception as exc:
            return {"error": f"fetch failed: {exc}"}
        return {"content": [{"type": "text", "text": text}]}

    return {"error": f"unknown method: {method}"}


# --------------------------------------------------------------------------- #
# HTTP server (stdlib only — zero new runtime deps)
# --------------------------------------------------------------------------- #

class _MCPHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for the MCP endpoint."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass  # silence the default access-log spam

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/mcp":
            self._send_json(
                {
                    "name": "arxivsnap",
                    "version": _VERSION,
                    "spec_version": _SPEC_VERSION,
                }
            )
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            self._send_json({"error": "invalid JSON"})
            return
        result = handle_mcp_request(body)
        self._send_json(result)

    def _send_json(self, data: Any) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def serve(host: str = "localhost", port: int = 8080) -> None:
    """Start the stateless MCP HTTP server (blocking).

    Each POST to /mcp is handled independently — no state between requests.
    """
    server = HTTPServer((host, port), _MCPHandler)
    server.serve_forever()

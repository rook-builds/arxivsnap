"""Unit tests for arxivsnap.mcp_server.handle_mcp_request().

All tests use the pure handle_mcp_request() function — no HTTP, no network.
Network calls inside fetch() are mocked via unittest.mock.patch.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from arxivsnap.mcp_server import handle_mcp_request

# --------------------------------------------------------------------------- #
# Minimal valid arXiv Atom XML for mocking httpx responses
# --------------------------------------------------------------------------- #
_MOCK_ATOM = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Test Paper on Agents</title>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <published>2024-01-01T00:00:00Z</published>
    <summary>A test abstract about agents and LLMs and their applications.</summary>
    <author><name>Alice Smith</name></author>
  </entry>
</feed>"""


def _make_httpx_mock() -> MagicMock:
    """Return a mock suitable for patching httpx.Client used as a context manager."""
    mock_resp = MagicMock()
    mock_resp.text = _MOCK_ATOM
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_client
    mock_ctx.__exit__.return_value = False
    return mock_ctx


# --------------------------------------------------------------------------- #
# tools/list
# --------------------------------------------------------------------------- #

def test_tools_list_returns_tools_key():
    result = handle_mcp_request({"method": "tools/list"})
    assert "tools" in result


def test_tools_list_has_fetch_tool():
    result = handle_mcp_request({"method": "tools/list"})
    assert result["tools"][0]["name"] == "fetch"


def test_tools_list_has_description():
    result = handle_mcp_request({"method": "tools/list"})
    assert len(result["tools"][0]["description"]) > 10


def test_tools_list_has_input_schema():
    result = handle_mcp_request({"method": "tools/list"})
    schema = result["tools"][0]["inputSchema"]
    assert schema["type"] == "object"


def test_tools_list_schema_has_query_and_limit():
    result = handle_mcp_request({"method": "tools/list"})
    props = result["tools"][0]["inputSchema"]["properties"]
    assert "query" in props
    assert "limit" in props


def test_tools_list_schema_required_is_list():
    result = handle_mcp_request({"method": "tools/list"})
    required = result["tools"][0]["inputSchema"]["required"]
    assert isinstance(required, list)


# --------------------------------------------------------------------------- #
# tools/call fetch
# --------------------------------------------------------------------------- #

def test_tools_call_fetch_no_args():
    with patch("arxivsnap.core.httpx.Client", return_value=_make_httpx_mock()):
        result = handle_mcp_request({
            "method": "tools/call",
            "params": {"name": "fetch", "arguments": {}},
        })
    assert "content" in result
    assert result["content"][0]["type"] == "text"


def test_tools_call_fetch_with_query():
    with patch("arxivsnap.core.httpx.Client", return_value=_make_httpx_mock()):
        result = handle_mcp_request({
            "method": "tools/call",
            "params": {"name": "fetch", "arguments": {"query": "neural networks"}},
        })
    assert result["content"][0]["text"].startswith("# arxivsnap")


def test_tools_call_fetch_returns_text_type():
    with patch("arxivsnap.core.httpx.Client", return_value=_make_httpx_mock()):
        result = handle_mcp_request({
            "method": "tools/call",
            "params": {"name": "fetch", "arguments": {"limit": 3}},
        })
    assert result["content"][0]["type"] == "text"


def test_tools_call_fetch_default_query_no_error():
    with patch("arxivsnap.core.httpx.Client", return_value=_make_httpx_mock()):
        result = handle_mcp_request({
            "method": "tools/call",
            "params": {"name": "fetch", "arguments": {}},
        })
    assert "error" not in result


def test_tools_call_unknown_tool():
    result = handle_mcp_request({
        "method": "tools/call",
        "params": {"name": "bogus", "arguments": {}},
    })
    assert "error" in result


def test_tools_call_missing_params():
    result = handle_mcp_request({"method": "tools/call"})
    assert "error" in result


# --------------------------------------------------------------------------- #
# Error cases
# --------------------------------------------------------------------------- #

def test_unknown_method():
    result = handle_mcp_request({"method": "ping"})
    assert "error" in result


def test_missing_method():
    result = handle_mcp_request({})
    assert "error" in result


def test_fetch_exception_returns_error():
    mock_ctx = MagicMock()
    mock_ctx.__enter__.side_effect = Exception("network error")
    mock_ctx.__exit__.return_value = False
    with patch("arxivsnap.core.httpx.Client", return_value=mock_ctx):
        result = handle_mcp_request({
            "method": "tools/call",
            "params": {"name": "fetch", "arguments": {}},
        })
    assert "error" in result
    assert "fetch failed" in result["error"]

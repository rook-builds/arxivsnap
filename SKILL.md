# arxivsnap

Fetch arXiv academic papers from the command line — search by topic, formatted as markdown for humans and agents

## Install

```
pip install arxivsnap
```

## Usage

```
arxivsnap [QUERY] --limit 10 --output json
```

Formats: text, json, table, csv. Run `arxivsnap introspect` for a machine-readable
description.

## MCP Server

```
arxivsnap serve [--port 8080] [--host localhost]
```

Stateless MCP HTTP server (2026-07-28 spec). POST to `/mcp` with:

```json
{"method": "tools/call", "params": {"name": "fetch", "arguments": {"query": "machine learning", "limit": 10}}}
```

Returns markdown with titles, authors, dates, abstracts, and arXiv links.

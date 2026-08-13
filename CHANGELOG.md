# Changelog

## [0.1.0] - 2026-08-13

### Added
- `arxivsnap [QUERY]` — search arXiv papers from the command line
- Queries arXiv Atom API (`export.arxiv.org/api/query`) — no auth required
- Results sorted by submission date, newest first
- Default query `ti:agent OR ti:llm` when no query provided
- `--limit N` — control result count (default 10, max 100)
- `--output [text|json|table|csv]` — four output modes
- Author field: first three authors, "et al." if more
- Abstract (first 300 chars) shown in text output
- `arxivsnap introspect` — ACLI-compliant JSON command description
- `arxivsnap skill` — agentskills.io-compliant SKILL.md
- SKILL.md at repo root for static agent discovery
- Full test suite: formatter, CLI, introspect tests
- Zero new dependencies beyond `httpx` and `click`

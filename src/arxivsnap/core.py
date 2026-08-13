"""arxivsnap core — fetch recent arXiv papers as structured Items.

Uses the arXiv Atom API (public, no auth required):
  https://export.arxiv.org/api/query?search_query=...&max_results=...
"""
from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import httpx

# arXiv Atom namespace
_NS = "http://www.w3.org/2005/Atom"

_BASE_URL = "https://export.arxiv.org/api/query"
_USER_AGENT = "arxivsnap/0.1.0 (https://github.com/rook-builds/arxivsnap)"


@dataclass
class Item:
    """One arXiv paper."""

    title: str
    url: str
    author: str = ""
    score: int = 0
    comments: int = 0
    created_at: Optional[datetime] = None
    body: str = ""

    def _created_iso(self) -> str:
        return self.created_at.isoformat() if self.created_at else ""


# --------------------------------------------------------------------------- #
# fetch
# --------------------------------------------------------------------------- #
def fetch(query: Optional[str] = None, limit: int = 10) -> list[Item]:
    """Fetch up to *limit* recent arXiv papers matching *query*.

    Parameters
    ----------
    query:
        arXiv search query string (e.g. "machine learning agents").
        If None or empty, defaults to ``"ti:agent OR ti:llm"`` — a broad
        selection of recent AI papers.
    limit:
        Maximum number of results to return (default 10, max 100).
    """
    q = (query or "").strip() or "ti:agent OR ti:llm"
    limit = max(1, min(int(limit), 100))

    params = {
        "search_query": q,
        "max_results": str(limit),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    with httpx.Client(timeout=15, headers={"User-Agent": _USER_AGENT}) as client:
        resp = client.get(_BASE_URL, params=params)
        resp.raise_for_status()
        xml_text = resp.text

    return _parse_atom(xml_text)


def _parse_atom(xml_text: str) -> list[Item]:
    """Parse arXiv Atom XML into a list of Items."""
    root = ET.fromstring(xml_text)
    items: list[Item] = []

    for entry in root.findall(f"{{{_NS}}}entry"):
        # Title — strip whitespace/newlines
        title_el = entry.find(f"{{{_NS}}}title")
        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""

        # URL — the <id> element is a canonical abs URL, e.g.
        # http://arxiv.org/abs/2401.12345v1
        id_el = entry.find(f"{{{_NS}}}id")
        url = (id_el.text or "").strip() if id_el is not None else ""

        # Authors — join first three with "et al." if more
        author_els = entry.findall(f"{{{_NS}}}author/{{{_NS}}}name")
        author_names = [el.text.strip() for el in author_els if el.text]
        if len(author_names) > 3:
            author = ", ".join(author_names[:3]) + " et al."
        elif author_names:
            author = ", ".join(author_names)
        else:
            author = ""

        # Published date
        pub_el = entry.find(f"{{{_NS}}}published")
        created_at: Optional[datetime] = None
        if pub_el is not None and pub_el.text:
            try:
                created_at = datetime.fromisoformat(
                    pub_el.text.rstrip("Z").replace("Z", "+00:00")
                )
                # Ensure timezone-aware UTC
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
            except ValueError:
                created_at = None

        # Abstract (summary) — first 300 chars
        summary_el = entry.find(f"{{{_NS}}}summary")
        body = ""
        if summary_el is not None and summary_el.text:
            raw = summary_el.text.strip().replace("\n", " ")
            body = raw[:300] + ("…" if len(raw) > 300 else "")

        items.append(Item(
            title=title,
            url=url,
            author=author,
            created_at=created_at,
            body=body,
        ))

    return items


# --------------------------------------------------------------------------- #
# formatters — DONE. Tested by tests/test_formatter.py. Do not rewrite.
# --------------------------------------------------------------------------- #
def to_text(items: list[Item], source: str = "arxivsnap") -> str:
    if not items:
        return f"# {source}\n\nNo items found."
    lines = [f"# {source}", ""]
    for i, it in enumerate(items, 1):
        meta = []
        if it.score:
            meta.append(f"{it.score} points")
        if it.comments:
            meta.append(f"{it.comments} comments")
        if it.author:
            meta.append(f"by {it.author}")
        if it.created_at:
            meta.append(it.created_at.strftime("%Y-%m-%d"))
        suffix = f"  ({' · '.join(meta)})" if meta else ""
        lines.append(f"{i}. **{it.title}**{suffix}")
        if it.url:
            lines.append(f"   {it.url}")
        if it.body:
            lines.append(f"   {it.body}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def to_json(items: list[Item], source: str = "arxivsnap") -> str:
    payload = {
        "source": source,
        "count": len(items),
        "items": [
            {**asdict(it), "created_at": it._created_iso()} for it in items
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def to_table(items: list[Item], source: str = "arxivsnap") -> str:
    if not items:
        return "No items found."
    header = "| # | Title | Author | Date |"
    sep = "|---|-------|--------|------|"
    rows = [header, sep]
    for i, it in enumerate(items, 1):
        title = it.title.replace("|", "\\|")
        date = it.created_at.strftime("%Y-%m-%d") if it.created_at else ""
        rows.append(f"| {i} | {title} | {it.author} | {date} |")
    return "\n".join(rows)


def to_csv(items: list[Item], source: str = "arxivsnap") -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["title", "url", "author", "score", "comments", "created_at"])
    for it in items:
        w.writerow(
            [it.title, it.url, it.author, it.score, it.comments, it._created_iso()]
        )
    return buf.getvalue()

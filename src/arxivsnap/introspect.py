"""Agent-CLI introspection: `arxivsnap introspect` and `arxivsnap skill`.

Lets any AI agent discover how to drive this tool without a human in the loop.
"""
import json

from . import __version__


def get_introspect_json() -> str:
    return json.dumps(
        {
            "name": "arxivsnap",
            "version": __version__,
            "description": "Fetch arXiv academic papers from the command line — search by topic, formatted as markdown for humans and agents",
            "commands": [
                {
                    "usage": "arxivsnap [TARGET] --limit N --output text|json|table|csv",
                    "description": "Fetch arXiv academic papers from the command line — search by topic, formatted as markdown for humans and agents",
                }
            ],
        },
        indent=2,
    )


def get_skill_md() -> str:
    return (
        "# arxivsnap\n\n"
        "Fetch arXiv academic papers from the command line — search by topic, formatted as markdown for humans and agents\n\n"
        "## Usage\n\n"
        "```\n"
        "arxivsnap [TARGET] --limit 10 --output json\n"
        "```\n\n"
        "Outputs: text (default), json, table, csv.\n"
    )

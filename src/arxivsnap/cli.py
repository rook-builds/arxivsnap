"""arxivsnap CLI — Fetch arXiv academic papers from the command line — search by topic, formatted as markdown for humans and agents"""

import sys

import click

from .core import fetch, to_csv, to_json, to_table, to_text
from .introspect import get_introspect_json, get_skill_md

_ACLI_COMMANDS = {"introspect", "skill", "serve"}


def _handle_acli_command(cmd: str) -> None:
    if cmd == "introspect":
        print(get_introspect_json())
    elif cmd == "skill":
        print(get_skill_md())
    elif cmd == "serve":
        import argparse as _ap

        _parser = _ap.ArgumentParser(
            prog="arxivsnap serve",
            description="Start a stateless MCP HTTP server for arxivsnap.",
            add_help=True,
        )
        _parser.add_argument(
            "--port", "-p", type=int, default=8080, help="Port to listen on (default 8080)."
        )
        _parser.add_argument(
            "--host", default="localhost", help="Host to bind (default localhost)."
        )
        # parse args that come AFTER the 'serve' positional
        _args, _ = _parser.parse_known_args()
        from .mcp_server import serve

        click.echo(
            f"arxivsnap MCP server listening on http://{_args.host}:{_args.port}/mcp",
            err=False,
        )
        serve(host=_args.host, port=_args.port)


@click.command()
@click.argument("query", required=False, default=None)
@click.option("--limit", "-n", default=10, show_default=True, help="How many items to fetch.")
@click.option(
    "--output",
    "-o",
    default="text",
    show_default=True,
    type=click.Choice(["text", "json", "table", "csv"]),
    help="Output format.",
)
def main(query, limit, output):
    """Fetch arXiv academic papers from the command line — search by topic, formatted as markdown for humans and agents

    Special commands: arxivsnap introspect | arxivsnap skill | arxivsnap serve [--port N] [--host HOST]
    """
    if query in _ACLI_COMMANDS:
        _handle_acli_command(query)
        sys.exit(0)

    items = fetch(query, limit=limit)

    if output == "text":
        click.echo(to_text(items))
    elif output == "json":
        click.echo(to_json(items))
    elif output == "table":
        click.echo(to_table(items))
    else:
        click.echo(to_csv(items), nl=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Example: Wrap api-contract-guardian as an MCP server.

This demonstrates how click-to-mcp can turn any Click/typer CLI into an MCP server
that AI coding agents (Claude Code, Cursor, Copilot) can use directly.

Run this example:
    pip install click-to-mcp
    python examples/api_contract_guardian_mcp.py

Then configure your MCP client (e.g. Claude Code):
    # .claude/settings.json
    {
      "mcpServers": {
        "api-contract-guardian": {
          "command": "python",
          "args": ["examples/api_contract_guardian_mcp.py"]
        }
      }
    }
"""

import click

from click_to_mcp import run

# --- Mock api-contract-guardian CLI (replace with real import) ---
# In production, you would do:
#   from api_contract_guardian.cli import app
#   run(app, prefix="acg")

@click.group()
def acg():
    """API Contract Guardian — validate API contracts against live endpoints."""
    pass

@acg.command()
@click.argument("spec_file", type=click.Path(exists=False))
@click.option("--base-url", default="http://localhost:8000", help="Base URL of the API")
@click.option("--strict/--no-strict", default=False, help="Fail on any contract violation")
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["json", "table", "junit"]),
    default="table", help="Output format",
)
def validate(spec_file: str, base_url: str, strict: bool, output_format: str):
    """Validate an OpenAPI spec against a live API."""
    click.echo(f"Validating {spec_file} against {base_url}...")
    click.echo(f"  Format: {output_format}")
    click.echo(f"  Strict: {strict}")
    click.echo("✓ All contracts pass")

@acg.command()
@click.argument("spec_file", type=click.Path(exists=False))
@click.option("--output", "-o", default="contracts.json", help="Output file path")
def extract(spec_file: str, output: str):
    """Extract contracts from an OpenAPI spec file."""
    click.echo(f"Extracting contracts from {spec_file}...")
    click.echo(f"  Output: {output}")
    click.echo("✓ 12 contracts extracted")

@acg.command()
@click.option("--watch/--no-watch", default=False, help="Watch for spec changes")
@click.option("--interval", default=30, type=int, help="Watch interval in seconds")
def monitor(watch: bool, interval: int):
    """Monitor API endpoints for contract drift."""
    click.echo(f"Monitoring contracts... (watch={watch}, interval={interval}s)")
    click.echo("✓ No drift detected")

if __name__ == "__main__":
    run(acg, prefix="acg", name="api-contract-guardian")

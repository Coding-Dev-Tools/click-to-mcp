#!/usr/bin/env python3
"""
Quick Start: Turn any Click CLI into an MCP server in 3 lines.

Usage:
    pip install click-to-mcp
    python examples/quick_start.py
"""

import click

from click_to_mcp import run


@click.group()
def my_cli():
    """My awesome CLI tool."""
    pass


@my_cli.command()
@click.argument("name")
@click.option("--loud", is_flag=True, help="Shout the greeting")
def hello(name: str, loud: bool):
    """Say hello to someone."""
    msg = f"Hello, {name}!"
    if loud:
        msg = msg.upper()
    click.echo(msg)


@my_cli.command()
@click.argument("numbers", nargs=-1, type=float)
@click.option("--operation", type=click.Choice(["sum", "avg", "max", "min"]), default="sum")
def math(numbers: tuple, operation: str):
    """Perform math on a list of numbers."""
    if not numbers:
        click.echo("No numbers provided")
        return
    result = {"sum": sum, "avg": lambda x: sum(x) / len(x), "max": max, "min": min}[operation](numbers)
    click.echo(f"{operation}({numbers}) = {result}")


if __name__ == "__main__":
    # That's it! Your CLI is now an MCP server.
    run(my_cli, prefix="my-cli", name="my-cli-mcp")

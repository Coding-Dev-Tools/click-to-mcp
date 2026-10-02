"""Demo CLI that showcases click-to-mcp wrapping."""

import click


@click.group()
def cli() -> None:
    """Demo CLI — a sample application for click-to-mcp testing."""
    pass


@cli.command()
@click.argument("name")
@click.option("--greeting", "-g", default="Hello", help="Greeting word")
@click.option("--repeat", "-r", default=1, type=int, help="Times to repeat")
def greet(name: str, greeting: str, repeat: int) -> None:
    """Greet someone with a customizable message."""
    for _ in range(repeat):
        click.echo(f"{greeting}, {name}!")


@cli.command()
@click.argument("a", type=float)
@click.argument("b", type=float)
@click.option("--operation", "-o", type=click.Choice(["add", "sub", "mul", "div"]), default="add")
def calculate(a: float, b: float, operation: str) -> None:
    """Perform a basic arithmetic operation."""
    ops = {
        "add": a + b,
        "sub": a - b,
        "mul": a * b,
        "div": a / b if b != 0 else float("inf"),
    }
    result = ops[operation]
    click.echo(f"Result: {result}")


@cli.group()
def config() -> None:
    """Manage configuration."""
    pass


@config.command()
@click.option("--verbose", is_flag=True, help="Show detailed output")
@click.option("--format", "-f", type=click.Choice(["json", "yaml", "toml"]), default="json")
def show(verbose: bool, format: str) -> None:
    """Show current configuration."""
    config_data = {
        "version": "1.0.0",
        "theme": "dark",
        "verbose": verbose,
        "format": format,
    }
    click.echo(f"Configuration ({format}):")
    for key, val in config_data.items():
        click.echo(f"  {key}: {val}")


@config.command()
@click.option("--theme", type=click.Choice(["dark", "light", "auto"]), help="UI theme")
@click.option("--verbose/--no-verbose", default=None, help="Enable verbose output")
def set(theme: str, verbose: bool) -> None:
    """Set configuration values."""
    changes = []
    if theme:
        changes.append(f"theme={theme}")
    if verbose is not None:
        changes.append(f"verbose={verbose}")
    if changes:
        click.echo(f"Updated: {', '.join(changes)}")
    else:
        click.echo("No changes.")


if __name__ == "__main__":
    cli()

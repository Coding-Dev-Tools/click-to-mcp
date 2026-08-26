"""Hidden commands/options must never leak into the MCP tool surface."""
import click
from click_to_mcp.adapter import cli_to_mcp_tools


def test_hidden_command_not_exposed():
    @click.group()
    def cli():
        pass

    @cli.command()
    def visible():
        pass

    @cli.command(hidden=True)
    def debug_dump():
        pass

    tools = {t.name: t for t in cli_to_mcp_tools(cli)}
    assert "visible" in tools
    assert "debug_dump" not in tools


def test_hidden_option_and_argument_not_exposed():
    @click.command()
    @click.option("--name", required=True)
    @click.option("--secret-token", hidden=True, default="x")
    @click.argument("target")
    def cmd(name, secret_token, target):
        pass

    @click.group()
    def cli():
        pass

    cli.add_command(cmd)

    (tool,) = cli_to_mcp_tools(cli)
    assert set(tool.input_schema["properties"]) == {"name", "target"}
    assert tool.input_schema["required"] == ["name", "target"]


def test_hidden_group_nested_skipped():
    @click.group()
    def cli():
        pass

    @cli.command()
    def ok():
        pass

    @cli.group(hidden=True)
    def internals():
        pass

    @internals.command()
    def wipe():
        pass

    names = [t.name for t in cli_to_mcp_tools(cli)]
    assert names == ["ok"]

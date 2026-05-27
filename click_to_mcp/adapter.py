"""
MCP Tool Definitions: Adapter that introspects Click/typer CLIs.
"""

from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Callable
from typing import Any

import click


@dataclasses.dataclass
class CliToolDef:
    """Describes a single CLI command as an MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., str]


def _param_type_name(t: Any) -> str:
    """Safely resolve Click param type class name."""
    return type(t).__name__


def _click_type_to_json_schema(param: click.Parameter) -> dict[str, Any]:
    """Map a Click parameter type to a JSON Schema property definition."""
    base: dict[str, Any] = {}

    t = param.type
    t_name = _param_type_name(t)

    if isinstance(t, click.Choice):
        base["type"] = "string"
        base["enum"] = t.choices
    elif t_name in ("IntParamType", "INT"):
        base["type"] = "integer"
    elif t_name in ("FloatParamType", "FLOAT"):
        base["type"] = "number"
    elif t_name in ("BoolParamType", "BOOLEAN"):
        base["type"] = "boolean"
    else:
        base["type"] = "string"

    base["description"] = getattr(param, 'help', None) or ""
    if not param.required:
        default = param.default if param.default is not None and param.default != () else None
        # Check for Click Sentinel (UNSET) values
        if default is not None:
            default_str = str(default)
            if default_str == "Sentinel.UNSET" or "Sentinel" in default_str:
                default = None
        if default is not None and default is not inspect.Parameter.empty:
            base["default"] = default

    return base


def _build_click_tool_def(cmd: click.Command, prefix: str = "") -> CliToolDef | None:
    """Convert a single Click Command into a CliToolDef.

    Returns None if the command has subcommands (handled recursively).
    """
    full_name = f"{prefix}_{cmd.name}".strip("_") if prefix else (cmd.name or "")

    if isinstance(cmd, click.Group):
        return None

    properties: dict[str, Any] = {}
    required: list[str] = []
    positional_args: list[str] = []  # track positional arg order

    for param in cmd.params:
        if isinstance(param, click.Option):
            # Prefer the long option name (--foo) over short (-f)
            names = [n for n in param.opts if n.startswith("--")]
            key = names[0].lstrip("-").replace("-", "_") if names else (param.name or "")
            if not key or key == "ctx":
                continue
        elif isinstance(param, click.Argument):
            key = param.name or ""
            if not key:
                continue
            positional_args.append(key)
        else:
            continue

        prop = _click_type_to_json_schema(param)
        properties[key] = prop
        if param.required:
            required.append(key)

    def handler(**kwargs: Any) -> str:
        from click.testing import CliRunner

        runner = CliRunner()
        args: list[str] = []

        # Positional args first (in order of definition)
        for pos_key in positional_args:
            if pos_key in kwargs:
                val = kwargs.pop(pos_key)
                if val is not None:
                    args.append(str(val))

        # Then options
        for key, val in kwargs.items():
            if val is None:
                continue
            opt = f"--{key.replace('_', '-')}"
            if isinstance(val, bool):
                if val:
                    args.append(opt)
            else:
                args.extend([opt, str(val)])

        result = runner.invoke(cmd, args, catch_exceptions=False)
        if result.exit_code != 0:
            raise RuntimeError(
                f"Command '{full_name}' failed (exit {result.exit_code}):\n"
                f"{result.output}\n{result.exception}"
            )
        return result.output

    desc = cmd.help or cmd.short_help or f"Execute {full_name}"

    return CliToolDef(
        name=full_name.replace(" ", "_").replace("-", "_"),
        description=desc,
        input_schema={
            "type": "object",
            "properties": properties,
            "required": required,
        },
        handler=handler,
    )


def _get_click_group(cli: Any) -> click.Group:
    """Unwrap a typer.Typer or similar wrapper to a click.Group.

    Uses Typer's own get_command() internally to produce the click Group.
    """
    # Already a click.Group
    if isinstance(cli, click.Group):
        return cli

    # typer.Typer — use Typer's own get_command to produce a click Group
    if hasattr(cli, "registered_commands") and hasattr(cli, "registered_groups"):
        from typer.main import get_command as typer_get_command
        click_cmd = typer_get_command(cli)
        if isinstance(click_cmd, click.Group):
            return click_cmd
        # Single command — wrap in a Group for consistency
        group = click.Group(name=getattr(cli.info, "name", "cli"))
        group.add_command(click_cmd)
        return group

    raise TypeError(
        f"Expected click.Group or typer.Typer, got {type(cli).__name__}"
    )


def cli_to_mcp_tools(cli, prefix: str = "") -> list[CliToolDef]:
    """Recursively introspect a Click Group and return all leaf tools.

    Supports both click.Group and typer.Typer instances.
    """
    cli = _get_click_group(cli)

    tools: list[CliToolDef] = []

    for name, cmd in cli.commands.items():
        if isinstance(cmd, click.Group):
            nested_prefix = f"{prefix}_{name}".strip("_") if prefix else name
            tools.extend(cli_to_mcp_tools(cmd, nested_prefix))
        elif isinstance(cmd, click.Command):
            tool = _build_click_tool_def(cmd, prefix)
            if tool:
                tools.append(tool)

    return tools

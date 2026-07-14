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


def _element_json_schema(param: click.Parameter) -> dict[str, Any]:
    """Map a Click parameter's *element* type to a scalar JSON Schema fragment.

    This is the per-value type, independent of whether the parameter accepts a
    single value or many (see :func:`_is_multi_valued`).
    """
    t = param.type
    t_name = _param_type_name(t)
    element: dict[str, Any] = {}

    if isinstance(t, click.Choice):
        element["type"] = "string"
        element["enum"] = t.choices
    elif t_name in ("IntParamType", "INT"):
        element["type"] = "integer"
    elif t_name in ("FloatParamType", "FLOAT"):
        element["type"] = "number"
    elif t_name in ("BoolParamType", "BOOLEAN"):
        element["type"] = "boolean"
    else:
        element["type"] = "string"

    return element


def _is_multi_valued(param: click.Parameter) -> bool:
    """True if the parameter accepts more than one value.

    Covers ``multiple=True`` options (repeatable flags) as well as variadic
    (``nargs=-1``) and fixed-tuple (``nargs>1``) options/arguments.
    """
    if getattr(param, "multiple", False):
        return True
    nargs = getattr(param, "nargs", 1)
    return nargs == -1 or (isinstance(nargs, int) and nargs > 1)


def _click_type_to_json_schema(param: click.Parameter) -> dict[str, Any]:
    """Map a Click parameter type to a JSON Schema property definition.

    Multi-valued parameters (``multiple=True``, or ``nargs=-1`` / ``nargs>1``)
    are mapped to an ``array`` whose ``items`` carry the element type, instead
    of being silently flattened to a single scalar string. Fixed-length tuple
    parameters (``nargs>1``) additionally constrain the array length.
    """
    element = _element_json_schema(param)

    if _is_multi_valued(param):
        base: dict[str, Any] = {"type": "array", "items": element}
        nargs = getattr(param, "nargs", 1)
        # Fixed-length tuple option/argument (e.g. nargs=2): pin the length.
        if not getattr(param, "multiple", False) and isinstance(nargs, int) and nargs > 1:
            base["minItems"] = nargs
            base["maxItems"] = nargs
    else:
        base = element

    base["description"] = getattr(param, "help", None) or ""

    if not param.required:
        default = param.default if param.default is not None and param.default != () else None
        # Check for Click Sentinel (UNSET) values
        if default is not None:
            default_str = str(default)
            if default_str == "Sentinel.UNSET" or "Sentinel" in default_str:
                default = None
        if default is not None and default is not inspect.Parameter.empty:
            # Click represents multiple/nargs defaults as tuples; JSON wants a list.
            if isinstance(default, tuple):
                default = list(default)
            base["default"] = default

    return base


def _append_option(args: list[str], opt: str, val: Any) -> None:
    """Append a single scalar option value to the CLI arg list."""
    if isinstance(val, bool):
        if val:
            args.append(opt)
    else:
        args.extend([opt, str(val)])


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
    multiple_opts: set[str] = set()  # options with multiple=True (repeat the flag)
    nargs_opts: set[str] = set()  # options with nargs>1 (one flag, many values)

    for param in cmd.params:
        if isinstance(param, click.Option):
            # Prefer the long option name (--foo) over short (-f)
            names = [n for n in param.opts if n.startswith("--")]
            key = names[0].lstrip("-").replace("-", "_") if names else (param.name or "")
            if not key or key == "ctx":
                continue
            if getattr(param, "multiple", False):
                multiple_opts.add(key)
            else:
                nargs = getattr(param, "nargs", 1)
                if isinstance(nargs, int) and nargs > 1:
                    nargs_opts.add(key)
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

        # Positional args first (in order of definition). Variadic positionals
        # (nargs=-1 / nargs>1) arrive as a list/tuple and expand to one arg each.
        for pos_key in positional_args:
            if pos_key in kwargs:
                val = kwargs.pop(pos_key)
                if val is None:
                    continue
                if isinstance(val, (list, tuple)):
                    args.extend(str(v) for v in val)
                else:
                    args.append(str(val))

        # Then options
        for key, val in kwargs.items():
            if val is None:
                continue
            opt = f"--{key.replace('_', '-')}"
            if key in multiple_opts:
                # Repeatable option: emit the flag once per value.
                values = val if isinstance(val, (list, tuple)) else [val]
                for v in values:
                    if isinstance(v, (list, tuple)):
                        # multiple=True combined with nargs>1: flag + N values.
                        args.append(opt)
                        args.extend(str(x) for x in v)
                    else:
                        _append_option(args, opt, v)
            elif key in nargs_opts:
                # Fixed-tuple option: one flag followed by all its values.
                values = val if isinstance(val, (list, tuple)) else [val]
                args.append(opt)
                args.extend(str(v) for v in values)
            else:
                _append_option(args, opt, val)

        result = runner.invoke(cmd, args, catch_exceptions=False)
        if result.exit_code != 0:
            raise RuntimeError(
                f"Command '{full_name}' failed (exit {result.exit_code}):\n{result.output}\n{result.exception}"
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

    raise TypeError(f"Expected click.Group or typer.Typer, got {type(cli).__name__}")


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

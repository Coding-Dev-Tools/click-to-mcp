"""Tests for handler execution paths in _build_click_tool_def.

Covers:
- Handler raises RuntimeError on non-zero exit code
- Handler correctly passes positional arguments
- Handler correctly passes boolean flags
- Handler correctly passes options with values
- Handler with mixed positional and optional args
"""

from __future__ import annotations

import click
import pytest

from click_to_mcp.adapter import _build_click_tool_def, cli_to_mcp_tools

# ---------------------------------------------------------------------------
# Helper CLIs for testing handler execution
# ---------------------------------------------------------------------------


@click.command(name="fail-cmd")
@click.option("--msg", default="oops", help="Error message")
def fail_cmd(msg: str) -> None:
    """A command that always fails."""
    click.echo(f"Error: {msg}")
    raise SystemExit(1)


@click.command(name="echo-args")
@click.argument("filename")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--count", default=1, type=int, help="Repeat count")
def echo_args(filename: str, verbose: bool, count: int) -> None:
    """Echo positional and optional arguments."""
    parts = [f"file={filename}"]
    if verbose:
        parts.append("verbose=True")
    parts.append(f"count={count}")
    click.echo(" ".join(parts))


@click.command(name="flag-only")
@click.option("--dry-run", is_flag=True, help="Dry run mode")
@click.option("--name", required=True, help="Target name")
def flag_only(dry_run: bool, name: str) -> None:
    """Command with flags and required options."""
    click.echo(f"name={name} dry_run={dry_run}")


@click.command(name="multi-arg")
@click.argument("source")
@click.argument("dest")
@click.option("--force", is_flag=True, help="Force overwrite")
def multi_arg(source: str, dest: str, force: bool) -> None:
    """Command with multiple positional args."""
    click.echo(f"src={source} dst={dest} force={force}")


# ---------------------------------------------------------------------------
# Handler failure tests
# ---------------------------------------------------------------------------


class TestHandlerFailure:
    """Test that handlers correctly raise RuntimeError on command failure."""

    def test_handler_raises_on_nonzero_exit(self) -> None:
        """Handler must raise RuntimeError when the invoked command exits non-zero."""
        tool = _build_click_tool_def(fail_cmd)
        assert tool is not None
        with pytest.raises(RuntimeError, match="failed"):
            tool.handler()

    def test_handler_failure_includes_exit_code(self) -> None:
        """RuntimeError message must include the exit code."""
        tool = _build_click_tool_def(fail_cmd)
        assert tool is not None
        with pytest.raises(RuntimeError, match=r"exit 1"):
            tool.handler()

    def test_handler_failure_includes_command_name(self) -> None:
        """RuntimeError message must include the command name."""
        tool = _build_click_tool_def(fail_cmd)
        assert tool is not None
        with pytest.raises(RuntimeError, match="fail-cmd"):
            tool.handler()

    def test_handler_failure_includes_output(self) -> None:
        """RuntimeError message must include the command's output before failure."""
        tool = _build_click_tool_def(fail_cmd)
        assert tool is not None
        with pytest.raises(RuntimeError, match="Error: oops"):
            tool.handler()


# ---------------------------------------------------------------------------
# Handler positional argument passing
# ---------------------------------------------------------------------------


class TestHandlerPositionalArgs:
    """Test that handlers correctly pass positional arguments."""

    def test_single_positional_arg(self) -> None:
        """Handler must pass a single positional argument correctly."""
        tool = _build_click_tool_def(echo_args)
        assert tool is not None
        result = tool.handler(filename="test.txt")
        assert "file=test.txt" in result

    def test_multiple_positional_args(self) -> None:
        """Handler must pass multiple positional args in correct order."""
        tool = _build_click_tool_def(multi_arg)
        assert tool is not None
        result = tool.handler(source="input.csv", dest="output.csv")
        assert "src=input.csv" in result
        assert "dst=output.csv" in result

    def test_positional_arg_required(self) -> None:
        """Handler must list positional args as required in the schema."""
        tool = _build_click_tool_def(echo_args)
        assert tool is not None
        assert "filename" in tool.input_schema["required"]


# ---------------------------------------------------------------------------
# Handler option/flag passing
# ---------------------------------------------------------------------------


class TestHandlerOptions:
    """Test that handlers correctly pass options and flags."""

    def test_boolean_flag_true(self) -> None:
        """Handler must pass is_flag=True as a bare --flag."""
        tool = _build_click_tool_def(echo_args)
        assert tool is not None
        result = tool.handler(filename="data.json", verbose=True)
        assert "verbose=True" in result

    def test_boolean_flag_false(self) -> None:
        """Handler must omit the flag when is_flag=False."""
        tool = _build_click_tool_def(echo_args)
        assert tool is not None
        result = tool.handler(filename="data.json", verbose=False)
        assert "verbose=" not in result

    def test_option_with_value(self) -> None:
        """Handler must pass option values as --key value."""
        tool = _build_click_tool_def(echo_args)
        assert tool is not None
        result = tool.handler(filename="x.yaml", count=5)
        assert "count=5" in result

    def test_dashed_option_becomes_underscore_key(self) -> None:
        """--dry-run option must be accessible as dry_run in kwargs."""
        tool = _build_click_tool_def(flag_only)
        assert tool is not None
        assert "dry_run" in tool.input_schema["properties"]
        result = tool.handler(name="target", dry_run=True)
        assert "dry_run=True" in result

    def test_none_option_omitted(self) -> None:
        """Handler must skip options with None value."""
        tool = _build_click_tool_def(echo_args)
        assert tool is not None
        # count has a default of 1, so passing None should skip it
        # (though Click would use the default)
        result = tool.handler(filename="test.txt", verbose=None, count=None)
        # count=None means it's skipped from args, Click uses default
        assert "file=test.txt" in result


# ---------------------------------------------------------------------------
# Handler via cli_to_mcp_tools integration
# ---------------------------------------------------------------------------


class TestHandlerViaIntegration:
    """Test handler execution through the full cli_to_mcp_tools pipeline."""

    def test_group_with_failing_command(self) -> None:
        """Failing commands in a group must still produce callable handlers."""
        group = click.Group(name="app", commands={"fail": fail_cmd, "echo": echo_args})
        tools = cli_to_mcp_tools(group)
        tool_map = {t.name: t for t in tools}
        assert "fail_cmd" in tool_map
        assert "echo_args" in tool_map

        # Failing command handler raises RuntimeError
        with pytest.raises(RuntimeError, match="exit 1"):
            tool_map["fail_cmd"].handler()

        # Successful command handler works
        result = tool_map["echo_args"].handler(filename="integration.txt")
        assert "file=integration.txt" in result

    def test_handler_output_is_string(self) -> None:
        """Handler return value must always be a string."""
        tool = _build_click_tool_def(echo_args)
        assert tool is not None
        result = tool.handler(filename="out.txt")
        assert isinstance(result, str)

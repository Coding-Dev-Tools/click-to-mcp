"""Tests for adapter edge cases: _get_click_group errors, _build_click_tool_def with Group, BoolParamType defaults."""

from __future__ import annotations

import click
import pytest

from click_to_mcp.adapter import (
    _build_click_tool_def,
    _click_type_to_json_schema,
    _get_click_group,
    cli_to_mcp_tools,
)

# ---------------------------------------------------------------------------
# _get_click_group edge cases
# ---------------------------------------------------------------------------


class TestGetClickGroup:
    """Test _get_click_group unwrapping and error handling."""

    def test_raises_typeerror_for_plain_object(self) -> None:
        """Passing a non-Click, non-Typer object should raise TypeError."""
        with pytest.raises(TypeError, match="Expected click.Group or typer.Typer"):
            _get_click_group("not a cli")

    def test_raises_typeerror_for_dict(self) -> None:
        """Passing a dict should raise TypeError."""
        with pytest.raises(TypeError, match="Expected click.Group or typer.Typer"):
            _get_click_group({})

    def test_raises_typeerror_for_int(self) -> None:
        """Passing an int should raise TypeError."""
        with pytest.raises(TypeError, match="Expected click.Group or typer.Typer"):
            _get_click_group(42)

    def test_passthrough_for_click_group(self) -> None:
        """A click.Group should be returned as-is."""
        group = click.Group(name="test")
        result = _get_click_group(group)
        assert result is group

    def test_single_command_wraps_in_group(self) -> None:
        """A single click.Command (non-Group) should raise TypeError."""
        cmd = click.Command(name="solo")
        with pytest.raises(TypeError, match="Expected click.Group or typer.Typer"):
            _get_click_group(cmd)


# ---------------------------------------------------------------------------
# _build_click_tool_def with click.Group → returns None
# ---------------------------------------------------------------------------


class TestBuildClickToolDef:
    """Test _build_click_tool_def handling of Groups and edge cases."""

    def test_group_returns_none(self) -> None:
        """A click.Group should return None (handled recursively)."""
        group = click.Group(name="subgroup")
        result = _build_click_tool_def(group)
        assert result is None

    def test_command_with_no_params(self) -> None:
        """A command with no parameters should still produce a valid tool def."""
        cmd = click.Command(name="noop", help="Does nothing")
        result = _build_click_tool_def(cmd)
        assert result is not None
        assert result.name == "noop"
        assert result.input_schema["properties"] == {}
        assert result.input_schema["required"] == []

    def test_command_description_fallback(self) -> None:
        """Command without help should use short_help or fallback string."""
        cmd = click.Command(name="nodoc")
        result = _build_click_tool_def(cmd)
        assert result is not None
        # Fallback description is "Execute {name}"
        assert "nodoc" in result.description

    def test_option_with_dash_becomes_underscore(self) -> None:
        """--my-option should become my_option in the schema key."""
        cmd = click.Command(
            name="dash-opt",
            params=[click.Option(["--my-option"], help="test")],
        )
        result = _build_click_tool_def(cmd)
        assert result is not None
        assert "my_option" in result.input_schema["properties"]


# ---------------------------------------------------------------------------
# _click_type_to_json_schema edge cases
# ---------------------------------------------------------------------------


class TestClickTypeToJsonSchema:
    """Test _click_type_to_json_schema for various Click param types."""

    def test_bool_option_with_default_true(self) -> None:
        """Boolean option with default=True should have 'default': True."""
        param = click.Option(["--flag"], is_flag=True, default=True, help="A flag")
        schema = _click_type_to_json_schema(param)
        assert schema["type"] == "boolean"
        assert schema.get("default") is True

    def test_bool_option_with_default_false(self) -> None:
        """Boolean option with default=False should have 'default': False."""
        param = click.Option(["--flag"], is_flag=True, default=False, help="A flag")
        schema = _click_type_to_json_schema(param)
        assert schema["type"] == "boolean"
        assert schema.get("default") is False

    def test_choice_type(self) -> None:
        """click.Choice should produce a string with enum."""
        param = click.Option(["--mode"], type=click.Choice(["fast", "slow"]), help="Speed")
        schema = _click_type_to_json_schema(param)
        assert schema["type"] == "string"
        assert schema["enum"] == ("fast", "slow")

    def test_int_type(self) -> None:
        """Integer option should produce type 'integer'."""
        param = click.Option(["--count"], type=int, help="Count")
        schema = _click_type_to_json_schema(param)
        assert schema["type"] == "integer"

    def test_float_type(self) -> None:
        """Float option should produce type 'number'."""
        param = click.Option(["--ratio"], type=float, help="Ratio")
        schema = _click_type_to_json_schema(param)
        assert schema["type"] == "number"

    def test_string_fallback(self) -> None:
        """Unknown Click types should fall back to 'string'."""
        param = click.Option(["--data"], type=click.Path(), help="A path")
        schema = _click_type_to_json_schema(param)
        assert schema["type"] == "string"

    def test_required_param_no_default(self) -> None:
        """Required parameter should not have a 'default' key."""
        param = click.Option(["--name"], required=True, help="Name")
        schema = _click_type_to_json_schema(param)
        assert "default" not in schema

    def test_optional_param_with_int_default(self) -> None:
        """Optional parameter with int default should include default."""
        param = click.Option(["--retries"], default=3, type=int, help="Retry count")
        schema = _click_type_to_json_schema(param)
        assert schema["default"] == 3

    def test_empty_tuple_default_treated_as_none(self) -> None:
        """Click sometimes uses () as default; should not appear in schema."""
        param = click.Option(["--items"], default=(), help="Items")
        schema = _click_type_to_json_schema(param)
        assert "default" not in schema


# ---------------------------------------------------------------------------
# cli_to_mcp_tools with nested groups
# ---------------------------------------------------------------------------


class TestNestedGroupDiscovery:
    """Test that nested Click groups are discovered recursively."""

    def test_nested_group_tools_discovered(self) -> None:
        """Commands in nested groups should be discovered with prefixed names."""
        inner_cmd = click.Command(name="inner-cmd", help="Inner")
        inner_group = click.Group(name="inner", commands={"inner-cmd": inner_cmd})
        outer_group = click.Group(name="outer", commands={"inner": inner_group})

        tools = cli_to_mcp_tools(outer_group)
        assert len(tools) == 1
        assert tools[0].name == "inner_inner_cmd"

    def test_deeply_nested_group(self) -> None:
        """Three levels of nesting should produce correctly prefixed names."""
        leaf = click.Command(name="leaf", help="Leaf command")
        level2 = click.Group(name="l2", commands={"leaf": leaf})
        level1 = click.Group(name="l1", commands={"l2": level2})
        root = click.Group(name="root", commands={"l1": level1})

        tools = cli_to_mcp_tools(root)
        assert len(tools) == 1
        assert tools[0].name == "l1_l2_leaf"

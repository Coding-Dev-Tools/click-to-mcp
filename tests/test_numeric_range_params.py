"""Tests for numeric range parameters: click.IntRange / click.FloatRange options.

Regression coverage for the bug where such parameters were advertised as a
generic ``"string"`` in the JSON Schema — dropping both the integer/number
type and the ``min``/``max`` bounds. An MCP client was therefore told a
bounded numeric option was a free-form string.
"""

from __future__ import annotations

import click
import pytest

from click_to_mcp.adapter import cli_to_mcp_tools


def _build_cli() -> click.Group:
    @click.group()
    def cli() -> None:  # pragma: no cover - group entry
        pass

    @cli.command()
    @click.option("--score", type=click.IntRange(1, 100), help="closed int range")
    @click.option("--ratio", type=click.FloatRange(0.0, 1.0), help="closed float range")
    @click.option("--level", type=click.IntRange(min=5), help="open lower bound only")
    @click.option("--cap", type=click.IntRange(1, 100, max_open=True), help="open upper bound")
    @click.option("--tags", multiple=True, type=click.IntRange(0, 3), help="repeatable bounded int")
    @click.option("--count", type=int, help="plain int")
    @click.option("--name", default="anon", help="plain string")
    def cmd(score, ratio, level, cap, tags, count, name) -> None:
        click.echo(f"score={score} ratio={ratio} level={level} cap={cap} tags={list(tags)} count={count} name={name}")

    return cli


def _tool(name: str):
    return next(t for t in cli_to_mcp_tools(_build_cli()) if t.name == name)


class TestNumericRangeSchema:
    """The JSON Schema should model IntRange/FloatRange as numeric with bounds."""

    def test_int_range_is_integer_with_closed_bounds(self) -> None:
        props = _tool("cmd").input_schema["properties"]
        assert props["score"]["type"] == "integer"
        assert props["score"]["minimum"] == 1
        assert props["score"]["maximum"] == 100

    def test_float_range_is_number_with_closed_bounds(self) -> None:
        props = _tool("cmd").input_schema["properties"]
        assert props["ratio"]["type"] == "number"
        assert props["ratio"]["minimum"] == 0.0
        assert props["ratio"]["maximum"] == 1.0

    def test_open_ended_lower_bound_only(self) -> None:
        props = _tool("cmd").input_schema["properties"]
        assert props["level"]["type"] == "integer"
        assert props["level"]["minimum"] == 5
        assert "maximum" not in props["level"]
        assert "exclusiveMaximum" not in props["level"]

    def test_open_upper_bound_uses_exclusive_maximum(self) -> None:
        props = _tool("cmd").input_schema["properties"]
        assert props["cap"]["type"] == "integer"
        assert props["cap"]["minimum"] == 1
        assert props["cap"]["exclusiveMaximum"] == 100
        assert "maximum" not in props["cap"]

    def test_multi_valued_range_composes_with_array(self) -> None:
        props = _tool("cmd").input_schema["properties"]
        tags = props["tags"]
        assert tags["type"] == "array"
        assert tags["items"] == {"type": "integer", "minimum": 0, "maximum": 3}

    def test_plain_types_unaffected(self) -> None:
        props = _tool("cmd").input_schema["properties"]
        assert props["count"]["type"] == "integer"
        assert "minimum" not in props["count"]
        assert props["name"]["type"] == "string"


class TestNumericRangeInvocation:
    """The handler should still pass values through and enforce ranges."""

    def test_int_range_handler_passes_value(self) -> None:
        out = _tool("cmd").handler(score=42)
        assert "score=42" in out

    def test_float_range_handler_passes_value(self) -> None:
        out = _tool("cmd").handler(ratio=0.5)
        assert "ratio=0.5" in out

    def test_out_of_range_value_is_rejected(self) -> None:
        # End-to-end: a value outside the IntRange must raise (click enforces
        # the bound; the server maps that to an MCP tool error, not a silent
        # success). The adapter surfaces this as RuntimeError (handler-wrapped
        # non-zero exit) or, if click re-raises, BadParameter.
        with pytest.raises((RuntimeError, click.exceptions.BadParameter)):
            _tool("cmd").handler(score=200)

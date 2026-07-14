"""Tests for multi-valued parameters: multiple=True options, variadic (nargs=-1)
arguments, and fixed-tuple (nargs>1) options.

Regression coverage for the bug where such parameters were advertised as a
single scalar string in the JSON Schema and had their list/tuple value
stringified into one garbage CLI argument (e.g. ``--tag "['a', 'b']"``).
"""

from __future__ import annotations

import click

from click_to_mcp.adapter import cli_to_mcp_tools


def _build_cli() -> click.Group:
    @click.group()
    def cli() -> None:  # pragma: no cover - group entry
        pass

    @cli.command()
    @click.option("--tag", multiple=True, help="repeatable tag")
    @click.option("--coord", nargs=2, type=int, help="an x/y pair")
    @click.option("--name", default="anon")
    @click.option("--verbose", is_flag=True)
    @click.argument("files", nargs=-1)
    def build(tag, coord, name, verbose, files) -> None:
        click.echo(f"tags={list(tag)} coord={coord} name={name} verbose={verbose} files={list(files)}")

    return cli


def _tool(name: str):
    return next(t for t in cli_to_mcp_tools(_build_cli()) if t.name == name)


class TestMultiValuedSchema:
    """The JSON Schema should model multi-valued params as arrays."""

    def test_multiple_option_is_array_of_element_type(self) -> None:
        props = _tool("build").input_schema["properties"]
        assert props["tag"]["type"] == "array"
        assert props["tag"]["items"] == {"type": "string"}

    def test_variadic_argument_is_array(self) -> None:
        props = _tool("build").input_schema["properties"]
        assert props["files"]["type"] == "array"
        assert props["files"]["items"] == {"type": "string"}

    def test_fixed_tuple_option_is_length_constrained_array(self) -> None:
        props = _tool("build").input_schema["properties"]
        coord = props["coord"]
        assert coord["type"] == "array"
        assert coord["items"] == {"type": "integer"}
        assert coord["minItems"] == 2
        assert coord["maxItems"] == 2

    def test_scalar_params_are_unchanged(self) -> None:
        props = _tool("build").input_schema["properties"]
        assert props["name"]["type"] == "string"
        assert props["verbose"]["type"] == "boolean"


class TestMultiValuedInvocation:
    """The handler should expand list/tuple values into real CLI arguments."""

    def test_multiple_option_repeats_flag(self) -> None:
        out = _tool("build").handler(tag=["a", "b"])
        assert "tags=['a', 'b']" in out

    def test_variadic_argument_expands(self) -> None:
        out = _tool("build").handler(files=["x.py", "y.py"])
        assert "files=['x.py', 'y.py']" in out

    def test_fixed_tuple_option_passes_all_values(self) -> None:
        out = _tool("build").handler(coord=[3, 4])
        assert "coord=(3, 4)" in out

    def test_combined_multi_valued_call(self) -> None:
        out = _tool("build").handler(tag=["a", "b"], coord=[1, 2], files=["m", "n"], verbose=True)
        assert "tags=['a', 'b']" in out
        assert "coord=(1, 2)" in out
        assert "files=['m', 'n']" in out
        assert "verbose=True" in out

    def test_scalar_option_still_works(self) -> None:
        out = _tool("build").handler(name="alice")
        assert "name=alice" in out

    def test_single_value_for_multiple_option_is_accepted(self) -> None:
        # Defensive: a caller passing a bare scalar to a repeatable option
        # should still produce a valid single-value invocation.
        out = _tool("build").handler(tag="solo")
        assert "tags=['solo']" in out

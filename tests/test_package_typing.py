"""Tests for PEP 561 typing marker and type-checker visibility."""

from __future__ import annotations

import importlib.resources

import click_to_mcp


class TestPyTypedMarker:
    """Ensure the package advertises itself as typed to type checkers."""

    def test_py_typed_marker_exists(self) -> None:
        """PEP 561 requires a py.typed file in the package root."""
        pkg = click_to_mcp.__spec__.origin
        assert pkg is not None
        pkg_dir = __import__("pathlib").Path(pkg).parent
        marker = pkg_dir / "py.typed"
        assert marker.exists(), "py.typed marker missing — type checkers will treat package as untyped"

    def test_py_typed_is_package_resource(self) -> None:
        """The marker should be importable as a package resource."""
        files = importlib.resources.files("click_to_mcp")
        marker = files / "py.typed"
        assert marker.is_file()

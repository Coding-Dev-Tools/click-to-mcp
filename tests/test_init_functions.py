"""Tests for __init__.py: high-level entry points, _resolve_server_meta, and exports.

Covers the run() high-level entry point and server meta resolution edge cases
that are not already covered by test_click_to_mcp.py's TestInit.
"""

from __future__ import annotations

from unittest.mock import patch

import click
import pytest

# ---------------------------------------------------------------------------
# _resolve_server_meta edge cases
# ---------------------------------------------------------------------------


class TestResolveServerMeta:
    """Additional edge-case coverage for _resolve_server_meta."""

    def _resolve(self, app: click.Group, prefix: str = "", name: str = ""):
        from click_to_mcp import _resolve_server_meta  # type: ignore[attr-defined]
        return _resolve_server_meta(app, prefix, name)

    def test_empty_name_falls_back_to_cli(self) -> None:
        """When app has no name, fallback should be 'cli'."""
        app = click.Group(name="")
        name, desc, prefix = self._resolve(app)
        assert name == "cli"

    def test_none_desc_becomes_empty(self) -> None:
        """When help is None, desc should be empty string."""
        app = click.Group(name="test", help=None)  # type: ignore[arg-type]
        name, desc, prefix = self._resolve(app)
        assert desc == ""

    def test_preserves_provided_name(self) -> None:
        """Explicit name should override app.name."""
        app = click.Group(name="ignored-name")
        name, desc, prefix = self._resolve(app, name="explicit")
        assert name == "explicit"

    def test_preserves_provided_prefix(self) -> None:
        """Prefix should be returned as-is."""
        app = click.Group(name="test")
        name, desc, prefix = self._resolve(app, prefix="custom")
        assert prefix == "custom"

    def test_help_text_extracted_from_app(self) -> None:
        """Help text from app.help should be used as description."""
        app = click.Group(name="myapp", help="My app helps you do things")
        name, desc, prefix = self._resolve(app)
        assert desc == "My app helps you do things"


# ---------------------------------------------------------------------------
# run() — high-level stdio entry point
# ---------------------------------------------------------------------------


class TestRunHighLevel:
    """Tests for the run() high-level entry point (non-blocking)."""

    @pytest.fixture()
    def demo_app(self) -> click.Group:
        from click_to_mcp.demo import cli as demo_cli
        return demo_cli

    def test_run_calls_serve_stdio(self, demo_app: click.Group) -> None:
        """run() should call serve_stdio with resolved server meta."""
        from click_to_mcp import run

        with patch("click_to_mcp.serve_stdio") as mock:
            run(demo_app, name="demo", prefix="test")
        mock.assert_called_once()
        _, kwargs = mock.call_args
        assert kwargs["name"] == "demo"
        assert kwargs["prefix"] == "test"
        assert "description" in kwargs

    def test_run_derives_name_from_app(self, demo_app: click.Group) -> None:
        """run() should derive name from app if not provided."""
        from click_to_mcp import run

        with patch("click_to_mcp.serve_stdio") as mock:
            run(demo_app, prefix="")
        _, kwargs = mock.call_args
        # demo cli has name='cli' (internal Click group name)
        assert isinstance(kwargs["name"], str)
        assert len(kwargs["name"]) > 0

    def test_run_accepts_no_args(self, demo_app: click.Group) -> None:
        """run() with no prefix/name should use app defaults."""
        from click_to_mcp import run

        with patch("click_to_mcp.serve_stdio") as mock:
            run(demo_app)
        mock.assert_called_once()


# ---------------------------------------------------------------------------
# __all__ exports
# ---------------------------------------------------------------------------


class TestModuleExports:
    """Verify __all__ exports match expectations."""

    def test_version_exported(self) -> None:
        import click_to_mcp

        assert hasattr(click_to_mcp, "__version__")
        assert isinstance(click_to_mcp.__version__, str)

    def test_run_exported(self) -> None:
        import click_to_mcp

        assert hasattr(click_to_mcp, "run")
        assert callable(click_to_mcp.run)

    def test_all_contains_expected_names(self) -> None:
        import click_to_mcp

        expected = {
            "__version__", "cli_to_mcp_tools", "CliToolDef", "serve_stdio",
            "run", "run_http", "run_http_streamable",
            "scan_entry_points", "load_cli", "find_our_clis", "DiscoveredCLI",
        }
        assert set(click_to_mcp.__all__) == expected

"""Tests for __main__.py and __init__.py edge cases.

Covers: python -m entry point, non-string help in _resolve_server_meta.
"""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import patch

import click


class TestMainModule:
    """Tests for __main__.py entry point."""

    def test_main_module_runs_help(self):
        """python -m click_to_mcp --help works (covers __main__.py:2-4)."""
        result = subprocess.run(
            [sys.executable, "-m", "click_to_mcp", "--help"],
            capture_output=True, text=False,
        )
        assert result.returncode == 0
        assert b"Usage" in result.stdout


class TestResolveServerMetaEdgeCases:
    """Edge cases for _resolve_server_meta (__init__.py:48)."""

    def _resolve(self, app, prefix="", name=""):
        from click_to_mcp import _resolve_server_meta  # type: ignore[attr-defined]
        return _resolve_server_meta(app, prefix, name)

    def test_non_string_help_becomes_str(self):
        """Non-string help should be converted (__init__.py:48)."""
        app = click.Group(name="test", help=42)
        _, desc, _ = self._resolve(app)
        assert desc == "42"

    def test_run_http_calls_serve_http(self):
        """run_http() calls serve_http with correct prefix."""
        from click_to_mcp import run_http
        from click_to_mcp.demo import cli as demo_app
        with patch("click_to_mcp.http_server.serve_http") as mock:
            run_http(demo_app, prefix="test", name="demo")
        mock.assert_called_once()
        assert mock.call_args.kwargs["prefix"] == "test"

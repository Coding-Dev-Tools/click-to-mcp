"""Tests for module entry point (python -m click_to_mcp)."""

from __future__ import annotations

import subprocess
import sys

from click_to_mcp.cli import cli


class TestMainModule:
    """Exercise click_to_mcp.__main__ to cover the module entry point."""

    def test_module_invocation_runs(self) -> None:
        """python -m click_to_mcp should run without crashing."""
        result = subprocess.run(
            [sys.executable, "-m", "click_to_mcp", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_cli_is_defined(self) -> None:
        """The cli object should be imported and defined."""
        assert cli is not None
        assert len(cli.commands) >= 4

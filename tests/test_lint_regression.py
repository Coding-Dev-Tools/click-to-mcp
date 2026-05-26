"""Lint regression tests: guard against reintroducing resolved lint violations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestW292TrailingNewline:
    """click_to_mcp/__init__.py must end with a trailing newline (W292)."""

    def test_init_py_has_trailing_newline(self) -> None:
        target = REPO_ROOT / "click_to_mcp" / "__init__.py"
        assert target.exists(), f"Target file not found: {target}"

        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--select=W292",
             "--output-format=concise", str(target)],
            capture_output=True, text=True,
        )

        assert result.returncode == 0, (
            f"W292 (missing trailing newline) violations in {target}:\n"
            f"{result.stdout}\n{result.stderr}"
        )

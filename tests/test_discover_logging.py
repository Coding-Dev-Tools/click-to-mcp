"""Tests for observability in discover.py — silent exception handlers should log."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from click_to_mcp.discover import (
    find_our_clis,
    import_cli,
    load_cli,
    scan_entry_points,
)


class TestDiscoverLogging:
    """Verify that silent exception paths emit diagnostic log messages."""

    def test_scan_entry_points_logs_load_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """scan_entry_points should log when an entry point fails to load."""
        fake_ep = MagicMock()
        fake_ep.name = "broken-cli"
        fake_ep.module = "nonexistent.module"
        fake_ep.attr = "cli"
        fake_ep.dist = None
        fake_ep.load.side_effect = ImportError("no module named 'nonexistent'")

        with patch("click_to_mcp.discover.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [fake_ep]
            with caplog.at_level(logging.DEBUG, logger="click_to_mcp.discover"):
                result = scan_entry_points()

        assert result == []
        assert any("broken-cli" in r.message for r in caplog.records)

    def test_load_cli_logs_entry_point_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """load_cli should log when an entry point load raises."""
        fake_ep = MagicMock()
        fake_ep.name = "my-broken-tool"
        fake_ep.load.side_effect = RuntimeError("entry point crashed")

        with patch("click_to_mcp.discover.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [fake_ep]
            with caplog.at_level(logging.DEBUG, logger="click_to_mcp.discover"):
                result = load_cli("my-broken-tool")

        assert result is None
        assert any("my-broken-tool" in r.message for r in caplog.records)

    def test_import_cli_logs_import_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """import_cli should log when module import fails."""
        with caplog.at_level(logging.DEBUG, logger="click_to_mcp.discover"):
            result = import_cli("totally.fake.module.xyz", "app")

        assert result is None
        assert any("totally.fake.module.xyz" in r.message for r in caplog.records)

    def test_find_our_clis_logs_load_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """find_our_clis should log when a known-module entry point fails to load."""
        fake_ep = MagicMock()
        fake_ep.name = "json2sql"
        fake_ep.module = "json2sql.cli"
        fake_ep.load.side_effect = AttributeError("missing attr")

        with patch("click_to_mcp.discover.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [fake_ep]
            with caplog.at_level(logging.DEBUG, logger="click_to_mcp.discover"):
                result = find_our_clis()

        assert result == {}
        assert any("json2sql" in r.message for r in caplog.records)

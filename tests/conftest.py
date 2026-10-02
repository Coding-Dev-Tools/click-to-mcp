"""Pytest configuration for click-to-mcp tests."""

import os

# Bypass license/rate-limit check in tests.
# Without this, tests fail when the daily rate limit (50 checks) is exceeded.
os.environ.setdefault("CLICK_TO_MCP_NO_LICENSE", "1")

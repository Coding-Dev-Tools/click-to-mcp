# click-to-mcp — AGENTS.md

Auto-wrap any Click/typer CLI as an MCP (Model Context Protocol) server. Part of the Revenue Holdings developer tool ecosystem.

## Quick Start

```bash
pip install -e ".[dev,http]"
python -m pytest tests/ -v
click-to-mcp demo                    # starts MCP stdio server for demo CLI
click-to-mcp demo-http               # starts MCP HTTP+SSE server on port 8000
```

## Key Components

| Module | Purpose |
|--------|---------|
| `click_to_mcp/cli.py` | CLI entry points: `discover`, `serve`, `serve-http`, `list-tools`, `config`, `demo`, `demo-http` |
| `click_to_mcp/adapter.py` | Click/typer introspection → MCP tool schema mapping |
| `click_to_mcp/server.py` | MCP stdio server implementation |
| `click_to_mcp/http_server.py` | MCP HTTP+SSE server (Starlette/Uvicorn) |
| `click_to_mcp/streamable_http.py` | Streamable HTTP transport (MCP 2025-06-18 spec) |
| `click_to_mcp/discover.py` | Auto-discovery of installed Click/typer CLIs via entry points |
| `click_to_mcp/demo.py` | Built-in demo CLI for testing |

## CI/CD

4 GitHub Actions workflows:
- `ci.yml` — lint (ruff) + test matrix (Python 3.10-3.13) + package build check
- `publish.yml` — PyPI publish on tag push
- `pages.yml` — GitHub Pages deployment
- `auto-code-review.yml` — automated code review

Run locally:
```bash
python -m ruff check .
python -m pytest tests/ -v
python -m build && twine check dist/*
```

## Dependencies

- Core: `click>=8.0`
- HTTP extra: `starlette>=0.27`, `uvicorn>=0.20`, `sse-starlette>=1.0`
- Dev: `pytest>=7.0`, `httpx>=0.24`, `ruff>=0.9.0,<1.0`
- Python: >=3.10

## Testing

```bash
# All tests (167 tests)
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_adapter.py -v
```

## Release Process

1. Update version in `pyproject.toml` and `click_to_mcp/_version.py`
2. Update `CHANGELOG.md`
3. Tag: `git tag v<version>`
4. Push tag: `git push origin v<version>` → triggers `publish.yml`

## Constraints

- Never commit secrets or `.env` files
- Keep CLI backward compatible — MCP clients depend on stable tool names
- HTTP extra is optional; stdio transport must work without it
- All 4 transports (stdio, SSE, HTTP, Streamable HTTP) must pass tests
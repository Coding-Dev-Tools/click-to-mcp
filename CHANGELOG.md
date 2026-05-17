# Changelog

All notable changes to click-to-mcp will be documented in this file.

## [0.4.0] — 2026-05-15

### Added

- **Streamable HTTP transport** — New transport mode using a single POST `/message` endpoint. No SSE (Server-Sent Events) required, compatible with more MCP clients.
  - `click-to-mcp serve-http-streamable <name>` — Serve any discovered CLI
  - `click-to-mcp demo-http-streamable` — Run the built-in demo
  - `run_http_streamable()` — Library API (from `click_to_mcp` import)
  - `serve_http_streamable()` — Low-level API (from `click_to_mcp.streamable_http`)
  - Default port 8001 (different from HTTP+SSE's 8000)
- **Batch message support** — Streamable HTTP transport accepts both single JSON-RPC messages and arrays (batch).
- 13 new tests covering Streamable HTTP transport (health, initialize, tools/list, tools/call, notifications, batch, edge cases)

### Changed

- Version bumped to 0.4.0
- `initialize` response now includes `"streamableHttp": {}` capability

## [0.3.0] — 2026-05-15

### Added

- HTTP+SSE transport support (`click-to-mcp serve-http`, `click-to-mcp demo-http`)
- `run_http()` library API for HTTP+SSE transport
- Optional `[http]` extra for Flask/requests dependencies

### Changed

- Version bumped to 0.3.0

## [0.2.1] — 2026-05-15

### Added

- Comprehensive pytest test suite (12 tests): TestAdapter, TestServer, TestDiscover
- MCP integration examples: `examples/api_contract_guardian_mcp.py`, `examples/quick_start.py`
- Blog-style README with MCP workflow sections for Claude Code, Cursor, and Cline/VS Code
- Install-from-GitHub instructions as primary path (PyPI blocked by hCaptcha)
- "How It Works" table mapping Click concepts to MCP equivalents

### Changed

- Replaced script-style tests with proper pytest test functions
- README restructured with agent integration workflows as primary value proposition

## [0.1.0] — 2026-05-14

### Added

- Initial release
- Auto-discover installed Click/typer CLIs via `console_scripts` entry points (`click-to-mcp discover`)
- Serve any discovered CLI as an MCP server over stdio (`click-to-mcp serve <name>`)
- Built-in demo server (`click-to-mcp demo`)
- `serve_stdio()` — library API to wrap a Click/typer app as an MCP server
- `run()` — high-level library API with auto-detection
- Full MCP protocol: `initialize`, `tools/list`, `tools/call`
- Parameter introspection: maps Click options, arguments, types, enums, defaults, and help text to JSON Schema
- Nested command group support with prefixed tool names
- Dual Click and Typer framework compatibility

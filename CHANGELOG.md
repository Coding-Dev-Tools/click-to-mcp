# Changelog

All notable changes to click-to-mcp will be documented in this file.

## [0.1.0] - 2026-05-17

### Added
- Initial release
- Auto-discover Click and typer CLIs in the environment (`click-to-mcp discover`)
- Serve any CLI as an MCP server via stdio (`click-to-mcp serve`)
- Serve any CLI as an MCP server via HTTP+SSE (`click-to-mcp serve-http`)
- Library API for embedding MCP wrapping in Python code
- Support for nested Click command groups
- Automatic schema generation from CLI help text
- MCP client compatibility with Claude Desktop, Cursor, Claude Code, and Codex

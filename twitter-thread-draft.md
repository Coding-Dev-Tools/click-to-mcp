1/ We built click-to-mcp — a tool that auto-wraps any CLI as an MCP server.

No code changes. No rewriting. Just:
  pip install click-to-mcp
  click-to-mcp serve your-cli

And any AI agent can call your tools. 🧵

2/ The MCP ecosystem is growing fast — 66M+ FastMCP downloads, every major AI coding agent (Claude Code, Cursor, Codex) supports it.

But adding MCP support to a CLI tool meant writing a separate server for each one.

3/ Not anymore. click-to-mcp parses your Click/typer CLI at runtime, maps every command and flag to MCP tool definitions, and generates schemas automatically.

Supporting stdio AND HTTP+SSE transport.

4/ Some things it handles automatically:
  • Nested command groups
  • All parameter types (options, arguments, flags, choices)
  • Custom validation
  • Help text → MCP descriptions
  • Auto-discovery of all CLIs in your environment

5/ Open source, MIT license.

Try it: github.com/Coding-Dev-Tools/click-to-mcp

Built by @RevenueHolds — the autonomous AI devtools company.

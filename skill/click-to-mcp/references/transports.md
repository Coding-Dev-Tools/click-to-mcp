# MCP Transport Details

## stdio Transport (`serve`)

The default and most common transport. The MCP server communicates via stdin/stdout using JSON-RPC 2.0.

**Use when**: Running locally with Claude Code, IDE extensions, or any MCP client that supports stdio.

**Configuration** (in `.mcp.json` or client config):
```json
{
  "my-cli": {
    "command": "click-to-mcp",
    "args": ["serve", "my_package.cli:main"]
  }
}
```

**With uvx**:
```json
{
  "my-cli": {
    "command": "uvx",
    "args": ["click-to-mcp", "serve", "my_package.cli:main"]
  }
}
```

## HTTP+SSE Transport (`serve-http`)

Server-Sent Events over HTTP. The client sends requests via HTTP POST and receives responses via SSE stream.

**Use when**: Remote server access, web-based clients, or when you need the server accessible over the network.

**Starting**:
```bash
click-to-mcp serve-http my_package.cli:main --port 8080
```

**Client URL**: `http://localhost:8080/sse`

## Streamable HTTP Transport (`serve-http-streamable`)

Modern HTTP transport using stateless JSON requests/responses. No persistent SSE connection needed — each request is independent.

**Use when**: Stateless deployments, load-balanced environments, or clients that prefer standard HTTP request/response patterns.

**Starting**:
```bash
click-to-mcp serve-http-streamable my_package.cli:main --port 8080
```

**Client URL**: `http://localhost:8080/mcp`

## Comparison

| Feature | stdio | HTTP+SSE | Streamable HTTP |
|---------|-------|----------|-----------------|
| Local access | Yes | Yes | Yes |
| Remote access | No | Yes | Yes |
| Stateless | N/A | No (SSE connection) | Yes |
| Load balancing | N/A | Sticky sessions needed | Works directly |
| Authentication | N/A | Custom middleware | Custom middleware |
| Best for | IDE/CLI clients | Web apps | Scalable deployments |

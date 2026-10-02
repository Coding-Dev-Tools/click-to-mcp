FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir ".[http]"

# Expose HTTP SSE transport for Glama/Docker checks
# The demo server starts a Click CLI wrapped as an MCP server on port 8001
EXPOSE 8001
ENTRYPOINT ["click-to-mcp"]
CMD ["demo-http-streamable", "--host", "0.0.0.0", "--port", "8001"]

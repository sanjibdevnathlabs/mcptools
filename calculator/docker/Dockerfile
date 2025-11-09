# Calculator MCP Server Docker Image
# Inherits from mcp-base with all shared dependencies

ARG BASE_TAG=latest
FROM sanjibdevnath/mcp-base:${BASE_TAG}

# Metadata
LABEL org.opencontainers.image.title="Calculator MCP Server"
LABEL org.opencontainers.image.description="MCP server for calculator operations (add, subtract, multiply, divide)"
LABEL org.opencontainers.image.vendor="sanjibdevnath"
LABEL org.opencontainers.image.source="https://github.com/sanjibdevnathlabs/mcptools"
LABEL mcp.name="calculator"
LABEL mcp.version="1.0.0"
LABEL mcp.transports="sse,streamable-http"

WORKDIR /app

# Copy shared modules (required by calculator)
COPY shared/ ./shared/

# Copy calculator-specific code
COPY calculator/ ./calculator/

# Expose ports for SSE and HTTP transports
# Actual port used depends on TRANSPORT_MODE environment variable
EXPOSE 8080 8081

# Environment defaults
# Use docker environment configuration (environment/docker.toml)
# TRANSPORT_MODE will be set by docker-compose per service (sse or streamable-http)
ENV APP_ENV=docker \
    TRANSPORT_MODE=sse \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8080 \
    LOG_LEVEL=INFO

# Entry point - runs the calculator server
# Config system will load environment/docker.toml when APP_ENV=docker
ENTRYPOINT ["python", "-m", "calculator"]

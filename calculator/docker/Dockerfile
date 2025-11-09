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
LABEL mcp.transports="stdio,sse,http"

# Copy only calculator-specific code
COPY calculator/ /app/calculator/
COPY tests/__init__.py tests/conftest.py tests/test_e2e_calculator.py /app/tests/

# Set working directory
WORKDIR /app

# Expose ports: 8080 (SSE), 8081 (HTTP), 9090 (Health/Metrics)
EXPOSE 8080 8081 9090

# Health check via ops port
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9090/health || exit 1

# Environment defaults
ENV MCP_NAME=calculator \
    TRANSPORT_MODE=stdio \
    LOG_LEVEL=INFO \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8080

# Entry point
ENTRYPOINT ["python", "-m", "calculator"]

# Default command (shows help)
CMD ["--help"]


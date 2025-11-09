# Database MCP Server Docker Image
# Inherits from mcp-base with all shared dependencies

ARG BASE_TAG=latest
FROM sanjibdevnath/mcp-base:${BASE_TAG}

# Metadata
LABEL org.opencontainers.image.title="Database MCP Server"
LABEL org.opencontainers.image.description="MCP server for database operations (MySQL/MariaDB query execution and schema management)"
LABEL org.opencontainers.image.vendor="sanjibdevnath"
LABEL org.opencontainers.image.source="https://github.com/sanjibdevnathlabs/mcptools"
LABEL mcp.name="database"
LABEL mcp.version="1.0.0"
LABEL mcp.transports="sse,streamable-http"
LABEL mcp.requires="mysql"

# Copy shared modules (for logging and config)
COPY shared/ /app/shared/

# Copy database-specific code and E2E tests
COPY database/ /app/database/
COPY tests/__init__.py tests/conftest.py tests/test_e2e_database.py /app/tests/

# Switch to non-root user (user already created in base image)
USER appuser

# Create logs directory with proper permissions
RUN mkdir -p /app/logs

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=docker \
    TRANSPORT_MODE=sse \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8086 \
    LOG_FORMAT=json \
    LOG_LEVEL=INFO \
    DB_HOST=mysql \
    DB_PORT=3306 \
    DB_USER=mcp_user \
    DB_DATABASE=mcp_db

# Expose ports for SSE and HTTP
EXPOSE 8086 8087

# Entry point
ENTRYPOINT ["python", "-m", "database"]


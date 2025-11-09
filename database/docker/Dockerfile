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

# Copy database-specific code
COPY database/ /app/database/

# Set working directory
WORKDIR /app

# Expose ports for SSE and HTTP transports
EXPOSE 8086 8087

# Environment defaults
ENV APP_ENV=docker \
    TRANSPORT_MODE=sse \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8086 \
    LOG_LEVEL=INFO \
    DB_HOST=mysql-mcp \
    DB_PORT=3306 \
    DB_USER=root \
    DB_PASSWORD=root_password \
    DB_DATABASE=mcp_db

# Entry point
ENTRYPOINT ["python", "-m", "database"]

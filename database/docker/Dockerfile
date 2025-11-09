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
LABEL mcp.transports="stdio,sse,http"
LABEL mcp.requires="mysql"

# Copy only database-specific code
COPY database/ /app/database/
COPY tests/__init__.py tests/conftest.py tests/test_e2e_database.py /app/tests/

# Set working directory
WORKDIR /app

# Expose port for SSE and HTTP modes
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys; from database.config.app import AppConfig; sys.exit(0)"

# Environment defaults
ENV MCP_NAME=database \
    TRANSPORT_MODE=stdio \
    LOG_LEVEL=INFO \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8081 \
    DATABASE_HOST=localhost \
    DATABASE_PORT=3306 \
    DATABASE_USER=root \
    DATABASE_NAME=mcp_db

# Entry point
ENTRYPOINT ["python", "-m", "database"]

# Default command (shows help)
CMD ["--help"]


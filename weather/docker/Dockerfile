# Weather MCP Server Docker Image
# Inherits from mcp-base with all shared dependencies

ARG BASE_TAG=latest
FROM sanjibdevnath/mcp-base:${BASE_TAG}

# Metadata
LABEL org.opencontainers.image.title="Weather MCP Server"
LABEL org.opencontainers.image.description="MCP server for weather information using OpenWeather API"
LABEL org.opencontainers.image.vendor="sanjibdevnath"
LABEL org.opencontainers.image.source="https://github.com/sanjibdevnathlabs/mcptools"
LABEL mcp.name="weather"
LABEL mcp.version="1.0.0"
LABEL mcp.transports="sse,streamable-http"

# Copy shared modules (required by weather)
COPY shared/ /app/shared/

# Copy weather-specific code
COPY weather/ /app/weather/
COPY tests/__init__.py tests/conftest.py tests/test_e2e_weather.py /app/tests/

# Set working directory
WORKDIR /app

# Expose ports for SSE and HTTP transports
# Actual port used depends on TRANSPORT_MODE environment variable
EXPOSE 8082 8083

# Environment defaults
# Use docker environment configuration (environment/docker.toml)
# TRANSPORT_MODE will be set by docker-compose per service (sse or streamable-http)
ENV APP_ENV=docker \
    TRANSPORT_MODE=sse \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8082 \
    LOG_LEVEL=INFO

# Entry point - runs the weather server
# Config system will load environment/docker.toml when APP_ENV=docker
ENTRYPOINT ["python", "-m", "weather"]


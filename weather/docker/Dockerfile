# Weather MCP Server Docker Image
# Inherits from mcp-base with all shared dependencies

ARG BASE_TAG=latest
FROM sanjibdevnath/mcp-base:${BASE_TAG}

# Metadata
LABEL org.opencontainers.image.title="Weather MCP Server"
LABEL org.opencontainers.image.description="MCP server for weather forecasting via Open-Meteo API"
LABEL org.opencontainers.image.vendor="sanjibdevnath"
LABEL org.opencontainers.image.source="https://github.com/sanjibdevnathlabs/mcptools"
LABEL mcp.name="weather"
LABEL mcp.version="1.0.0"
LABEL mcp.transports="stdio,sse,http"
LABEL mcp.requires="internet"

# Copy only weather-specific code
COPY weather/ /app/weather/
COPY tests/__init__.py tests/conftest.py tests/test_e2e_weather.py /app/tests/

# Set working directory
WORKDIR /app

# Expose port for SSE and HTTP modes
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys; from weather.config.app import AppConfig; sys.exit(0)"

# Environment defaults
ENV MCP_NAME=weather \
    TRANSPORT_MODE=stdio \
    LOG_LEVEL=INFO \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8082 \
    WEATHER_API_ENABLED=true \
    WEATHER_CACHE_TTL=3600

# Entry point
ENTRYPOINT ["python", "-m", "weather"]

# Default command (shows help)
CMD ["--help"]


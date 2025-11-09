#!/usr/bin/env python3
"""
Database MCP Server - Main Entry Point

A production-grade Model Context Protocol (MCP) server for MySQL database interactions.
Supports stdio, sse, and streamable-http transport modes.
"""

from database.config import Config
from database.src.server import DatabaseMCPServer
from shared.logging import setup_logging

# Initialize config
config = Config()

# Setup logging using shared logging module
# Pass transport_mode so stdio can be forced to file logging
logger = setup_logging(config, "database", transport_mode=config.server.transport_mode)

# Create DatabaseMCPServer instance (with FastMCP inside)
server_instance = DatabaseMCPServer()

# Get the FastMCP instance from the server
mcp = server_instance.get_fastmcp()


def main():
    """Main entry point for database server."""
    # Validate transport mode
    valid_transports = ["stdio", "sse", "streamable-http"]
    if config.server.transport_mode not in valid_transports:
        logger.error(
            f"Invalid transport mode: {config.server.transport_mode}. "
            f"Must be one of: {valid_transports}"
        )
        return

    logger.info(
        f"Starting database MCP server: transport={config.server.transport_mode}, "
        f"host={config.server.host}, port={config.server.port}"
    )

    # Run server with configured transport (FastMCP reads host/port from environment variables)
    mcp.run(transport=config.server.transport_mode)


if __name__ == "__main__":
    main()

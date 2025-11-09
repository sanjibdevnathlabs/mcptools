"""
Shared logging module for MCP servers.

Provides consistent logging setup across all MCP servers with:
- JSON and text formatting
- Configurable log levels and destinations
- Structured logging support
"""

from shared.logging.setup import JSONFormatter, TextFormatter, setup_logging

__all__ = ["JSONFormatter", "TextFormatter", "setup_logging"]

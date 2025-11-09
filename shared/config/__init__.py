"""
Shared configuration module for MCP servers.

Provides generic configuration loading from TOML files with:
- Environment variable interpolation (${VAR} and ${VAR:-default})
- Multi-environment support (dev, test, docker, prod)
- Automatic merging of default and environment-specific configs
"""

from shared.config.loader import ConfigLoader
from shared.config.logger import LoggerConfig

__all__ = ["ConfigLoader", "LoggerConfig"]


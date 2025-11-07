"""
Configuration module for Database MCP Server.

Loads settings from TOML files with OS environment variable interpolation.
Follows the ragtrial/opexsummary pattern for configuration management.
"""

import os
import sys

# Handle tomllib import (Python 3.11+ has built-in, 3.10 needs tomli)
import tomllib
from pathlib import Path

from database.config.app import AppConfig
from database.config.database import DatabaseConfig
from database.config.mcp import MCPConfig
from database.config.security import SecurityConfig
from database.config.server import ServerConfig


class Config:
    """
    Singleton config loaded from TOML files.

    Matches ragtrial/opexsummary pattern for configuration management.
    """

    app: AppConfig
    database: DatabaseConfig
    server: ServerConfig
    mcp: MCPConfig
    security: SecurityConfig

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Load configuration from TOML files."""
        # Initialize config objects
        self.app = AppConfig()
        self.database = DatabaseConfig()
        self.server = ServerConfig()
        self.mcp = MCPConfig()
        self.security = SecurityConfig()

        # Load and merge TOML files
        settings = self._load_config_files()

        # Apply settings to config objects
        self._apply_config_values(settings)

        # Validate required fields
        self._validate_config()

    def _load_config_files(self) -> dict:
        """Load and merge TOML configuration files."""
        config_dir = Path(__file__).parent.parent / "environment"
        default_path = config_dir / "default.toml"

        # Load default config
        if not default_path.exists():
            raise FileNotFoundError(
                f"Default config not found: {default_path}\n"
                "Create environment/default.toml with base configuration."
            )

        settings = self._load_toml(default_path)

        # Default to 'dev' environment if APP_ENV not set
        env = os.environ.get("APP_ENV", "dev")

        # Load environment-specific config
        env_path = config_dir / f"{env}.toml"
        if env_path.exists():
            env_config = self._load_toml(env_path)
            self._merge_dicts(settings, env_config)

        # Interpolate environment variables
        return self._interpolate(settings)

    def _load_toml(self, path: Path) -> dict:
        """Load TOML file."""
        with open(path, "rb") as f:
            return tomllib.load(f)

    def _merge_dicts(self, base: dict, override: dict):
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value

    def _interpolate(self, item):
        """
        Recursively replace $VAR or ${VAR} with os.environ values.
        """
        if isinstance(item, dict):
            return {k: self._interpolate(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [self._interpolate(v) for v in item]
        elif isinstance(item, str):
            return os.path.expandvars(item)
        return item

    def _apply_config_values(self, settings: dict):
        """Apply loaded settings to config objects."""
        # Apply app settings
        app_settings = settings.get("app", {})
        for key, value in app_settings.items():
            if hasattr(self.app, key):
                setattr(self.app, key, value)

        # Apply database settings
        database_settings = settings.get("database", {})
        for key, value in database_settings.items():
            if hasattr(self.database, key):
                setattr(self.database, key, value)

        # Apply server settings
        server_settings = settings.get("server", {})
        for key, value in server_settings.items():
            if hasattr(self.server, key):
                setattr(self.server, key, value)

        # Apply MCP settings
        mcp_settings = settings.get("mcp", {})
        for key, value in mcp_settings.items():
            if hasattr(self.mcp, key):
                setattr(self.mcp, key, value)

        # Apply security settings
        security_settings = settings.get("security", {})
        for key, value in security_settings.items():
            if hasattr(self.security, key):
                setattr(self.security, key, value)

        # CRITICAL: Force file-based logging for STDIO transport
        # STDIO transport requires stdout to be clean for JSON-RPC messages
        # All logs MUST go to file or stderr, never stdout
        if self.server.transport_mode == "stdio":
            if self.server.log_destination in ("stdout", "both"):
                self.server.log_destination = "file"

    def get_database_dsn(self, mask_password: bool = True) -> str:
        """
        Get database DSN (Data Source Name) string.

        Args:
            mask_password: If True, mask password in DSN (for logging)

        Returns:
            DSN string in format: mysql://user:password@host:port/database
        """
        password = "***" if mask_password else self.database.password
        database = self.database.database or ""

        return (
            f"mysql://{self.database.user}:{password}@"
            f"{self.database.host}:{self.database.port}/{database}"
        )

    def get_connection_params(self) -> dict:
        """
        Get connection parameters for aiomysql.create_pool().

        Returns:
            Dictionary of connection parameters
        """
        params = {
            "host": self.database.host,
            "port": self.database.port,
            "user": self.database.user,
            "password": self.database.password,
            "charset": self.database.charset,
            "minsize": self.database.pool_size,
            "maxsize": self.database.pool_size,
            "pool_recycle": self.database.pool_recycle,
        }

        # Add database if specified
        if self.database.database:
            params["db"] = self.database.database

        # Add SSL configuration if enabled
        if self.database.use_ssl:
            params["ssl"] = True

        return params

    def _validate_config(self):
        """Validate required configuration values."""
        if not self.database.user:
            raise ValueError(
                "Database user not set.\n"
                "Set environment variable: export DB_USER=your_user"
            )

        if not self.database.password:
            raise ValueError(
                "Database password not set.\n"
                "Set environment variable: export DB_PASSWORD=your_password"
            )

        if not self.app.name:
            raise ValueError("app.name not configured in TOML")

        # Validate transport mode
        valid_transports = ["stdio", "sse", "streamable-http", "auto"]
        if self.server.transport_mode not in valid_transports:
            raise ValueError(
                f"Invalid transport_mode: {self.server.transport_mode}. "
                f"Must be one of: {valid_transports}"
            )

        # Validate SSL settings
        if self.security.enable_ssl:
            if not self.security.ssl_ca:
                raise ValueError("ssl_ca path required when enable_ssl is True")
            if not Path(self.security.ssl_ca).exists():
                raise FileNotFoundError(
                    f"SSL CA file not found: {self.security.ssl_ca}"
                )

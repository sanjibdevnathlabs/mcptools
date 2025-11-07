"""
Configuration module for Weather MCP Server.

Loads settings from TOML files with OS environment variable interpolation.
"""

import os
import sys

# Handle tomllib import (Python 3.11+ has built-in, 3.10 needs tomli)
import tomllib
from pathlib import Path

from weather.config.api import APIConfig
from weather.config.app import AppConfig
from weather.config.server import ServerConfig


class Config:
    """
    Singleton config loaded from TOML files.

    Matches the database server pattern for configuration management.
    """

    app: AppConfig
    api: APIConfig
    server: ServerConfig

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
        self.api = APIConfig()
        self.server = ServerConfig()

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

        # Apply API settings
        api_settings = settings.get("api", {})
        for key, value in api_settings.items():
            if hasattr(self.api, key):
                setattr(self.api, key, value)

        # Apply server settings
        server_settings = settings.get("server", {})
        for key, value in server_settings.items():
            if hasattr(self.server, key):
                setattr(self.server, key, value)

    def _validate_config(self):
        """Validate required configuration values."""
        if not self.api.openweather_api_key:
            raise ValueError(
                "OpenWeather API key not set.\n"
                "Set environment variable: export OPENWEATHER_API_KEY=your_key"
            )

        if not self.app.name:
            raise ValueError("app.name not configured in TOML")

        # Validate transport mode
        valid_transports = ["stdio", "sse", "streamable-http"]
        if self.server.transport_mode not in valid_transports:
            raise ValueError(
                f"Invalid transport_mode: {self.server.transport_mode}. "
                f"Must be one of: {valid_transports}"
            )

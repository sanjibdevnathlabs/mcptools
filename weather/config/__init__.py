"""
Configuration module for Weather MCP Server.

Uses shared configuration loader with weather-specific config classes.
"""

import os
from pathlib import Path

from shared.config import ConfigLoader, LoggerConfig

from weather.config.api import APIConfig
from weather.config.app import AppConfig
from weather.config.server import ServerConfig


class Config:
    """
    Singleton config loaded from TOML files.
    
    Uses shared ConfigLoader for loading and interpolation,
    with weather-specific config classes.
    """

    app: AppConfig
    api: APIConfig
    server: ServerConfig
    logger: LoggerConfig

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Load configuration using shared loader."""
        # Initialize config objects
        self.app = AppConfig()
        self.api = APIConfig()
        self.server = ServerConfig()
        self.logger = LoggerConfig()

        # Get config directory
        config_dir = Path(__file__).parent.parent / "environment"
        
        # Load configuration using shared loader
        loader = ConfigLoader(config_dir)
        settings = loader.load()

        # Apply settings to config objects
        self._apply_config_values(settings)

        # Validate required fields
        self._validate_config()

    def _apply_config_values(self, settings: dict):
        """Apply loaded settings to config objects with type conversion."""
        # Apply app settings
        app_settings = settings.get("app", {})
        for key, value in app_settings.items():
            if hasattr(self.app, key):
                setattr(self.app, key, value)

        # Apply API settings (weather-specific)
        api_settings = settings.get("api", {})
        for key, value in api_settings.items():
            if hasattr(self.api, key):
                setattr(self.api, key, value)

        # Apply server settings with type conversion
        server_settings = settings.get("server", {})
        for key, value in server_settings.items():
            if hasattr(self.server, key):
                # Convert port from string to int if needed (from env var interpolation)
                if key == "port" and isinstance(value, str):
                    value = int(value)
                setattr(self.server, key, value)

        # Apply logger settings
        logger_settings = settings.get("logger", {})
        for key, value in logger_settings.items():
            if hasattr(self.logger, key):
                setattr(self.logger, key, value)

    def _validate_config(self):
        """Validate required configuration values."""
        # Skip API key validation in test environment - allow empty key for mock API
        if not self.api.openweather_api_key and os.environ.get("APP_ENV") != "test":
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

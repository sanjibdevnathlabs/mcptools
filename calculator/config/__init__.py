"""
Configuration module for Calculator MCP Server.

Uses shared configuration loader with calculator-specific config classes.
"""

from pathlib import Path

from shared.config import ConfigLoader

from calculator.config.app import AppConfig
from calculator.config.logger import LoggerConfig
from calculator.config.server import ServerConfig


class Config:
    """
    Singleton config loaded from TOML files.
    
    Uses shared ConfigLoader for loading and interpolation,
    with calculator-specific config classes.
    """

    app: AppConfig
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
        self.server = ServerConfig()
        self.logger = LoggerConfig()

        # Get config directory
        config_dir = Path(__file__).parent.parent / "environment"
        
        # Load configuration using shared loader
        loader = ConfigLoader(config_dir)
        settings = loader.load()

        # Apply settings to config objects
        self._apply_config_values(settings)

    def _apply_config_values(self, settings: dict):
        """Apply loaded settings to config objects with type conversion."""
        # Apply app settings
        app_settings = settings.get("app", {})
        for key, value in app_settings.items():
            if hasattr(self.app, key):
                setattr(self.app, key, value)

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

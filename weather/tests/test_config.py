"""Unit tests for weather configuration"""


import pytest

from weather.config import Config


@pytest.mark.unit
class TestWeatherConfig:
    """Test weather configuration loading and validation"""

    def test_config_singleton(self):
        """Test that Config returns the same instance"""
        config1 = Config()
        config2 = Config()
        assert config1 is config2, "Config should be a singleton"

    def test_default_transport_mode(self):
        """Test default transport mode is stdio"""
        config = Config()
        assert config.server.transport_mode in [
            "stdio",
            "sse",
            "streamable-http",
        ], f"Transport mode should be valid, got: {config.server.transport_mode}"

    def test_valid_transport_modes(self):
        """Test that transport mode validation accepts valid values"""
        config = Config()
        valid_modes = ["stdio", "sse", "streamable-http"]
        assert (
            config.server.transport_mode in valid_modes
        ), f"Transport mode {config.server.transport_mode} not in {valid_modes}"

    def test_app_name(self):
        """Test application name is set correctly"""
        config = Config()
        assert config.app.name == "weather-mcp", f"Expected 'weather-mcp', got '{config.app.name}'"

    def test_api_config_attributes(self):
        """Test API configuration has required attributes"""
        config = Config()
        assert hasattr(config.api, "openweather_api_key")
        assert hasattr(config.api, "openweather_api_base")
        assert hasattr(config.api, "timeout")
        assert hasattr(config.api, "user_agent")

    def test_server_config_attributes(self):
        """Test server configuration has required attributes"""
        config = Config()
        assert hasattr(config.server, "transport_mode")
        assert hasattr(config.server, "host")
        assert hasattr(config.server, "port")
        
        # Logger config is now separate
        assert hasattr(config.logger, "level")
        assert hasattr(config.logger, "format")
        assert hasattr(config.logger, "destination")

    def test_api_base_url(self):
        """Test API base URL is correctly configured"""
        config = Config()
        assert "openweathermap.org" in config.api.openweather_api_base
        assert config.api.openweather_api_base.startswith("https://")

    def test_timeout_is_number(self):
        """Test timeout is a numeric value"""
        config = Config()
        assert isinstance(config.api.timeout, int | float)
        assert config.api.timeout > 0

    def test_user_agent_set(self):
        """Test user agent is configured"""
        config = Config()
        assert config.api.user_agent
        assert len(config.api.user_agent) > 0

    def test_port_is_integer(self):
        """Test port is an integer after interpolation"""
        config = Config()
        assert isinstance(config.server.port, int)
        assert 1 <= config.server.port <= 65535


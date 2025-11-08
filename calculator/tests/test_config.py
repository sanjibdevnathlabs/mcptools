"""Unit tests for calculator configuration"""

import pytest

from calculator.config import Config


@pytest.mark.unit
class TestCalculatorConfig:
    """Test calculator configuration loading and validation"""

    def test_config_singleton(self):
        """Test that Config returns the same instance"""
        config1 = Config()
        config2 = Config()
        assert config1 is config2, "Config should be a singleton"

    def test_default_transport_mode(self):
        """Test default transport mode is stdio"""
        config = Config()
        assert config.server.transport_mode == "stdio"

    def test_valid_transport_modes(self):
        """Test that transport mode validation accepts valid values"""
        config = Config()
        valid_modes = ["stdio", "sse", "streamable-http"]
        assert config.server.transport_mode in valid_modes

    def test_app_name(self):
        """Test application name is set correctly"""
        config = Config()
        assert config.app.name == "calculator"

"""Unit tests for database configuration"""

import pytest

from database.config import Config


@pytest.mark.unit
class TestDatabaseConfig:
    """Test database configuration loading and validation"""

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
        assert (
            config.server.transport_mode in valid_modes
        ), f"Transport mode {config.server.transport_mode} not in {valid_modes}"

    def test_app_name(self):
        """Test application name is set correctly"""
        config = Config()
        assert (
            config.app.name == "database-mcp"
        ), f"Expected 'database-mcp', got '{config.app.name}'"

    def test_database_config_attributes(self):
        """Test database configuration has required attributes"""
        config = Config()
        assert hasattr(config.database, "host")
        assert hasattr(config.database, "port")
        assert hasattr(config.database, "user")
        assert hasattr(config.database, "database")
        assert hasattr(config.database, "pool_size")
        assert hasattr(config.database, "query_timeout")

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

    def test_mcp_config_attributes(self):
        """Test MCP configuration has required attributes"""
        config = Config()
        assert hasattr(config.mcp, "server_name")
        assert hasattr(config.mcp, "readonly_mode")
        assert hasattr(config.mcp, "allowed_query_types")

    def test_security_config_attributes(self):
        """Test security configuration has required attributes"""
        config = Config()
        assert hasattr(config.security, "enable_sql_analysis")
        assert hasattr(config.security, "max_rows_returned")
        assert hasattr(config.security, "enable_ssl")

    def test_database_port_is_integer(self):
        """Test that database port is an integer"""
        config = Config()
        assert isinstance(config.database.port, int)

    def test_server_port_is_integer(self):
        """Test that server port is an integer"""
        config = Config()
        assert isinstance(config.server.port, int)

    def test_readonly_mode_is_boolean(self):
        """Test that readonly mode is a boolean"""
        config = Config()
        assert isinstance(config.mcp.readonly_mode, bool)

    def test_query_timeout_is_number(self):
        """Test that query timeout is a number"""
        config = Config()
        assert isinstance(config.database.query_timeout, int | float)

    def test_pool_size_is_integer(self):
        """Test that pool size is an integer"""
        config = Config()
        assert isinstance(config.database.pool_size, int)

    def test_max_rows_is_integer(self):
        """Test that max rows returned is an integer"""
        config = Config()
        assert isinstance(config.security.max_rows_returned, int)

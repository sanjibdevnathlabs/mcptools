import os
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConfig(BaseSettings):
    """Database configuration with validation and defaults."""
    
    # Database connection settings
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=3306, ge=1, le=65535, description="Database port")
    user: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    database: Optional[str] = Field(default=None, description="Default database name")
    charset: str = Field(default="utf8mb4", description="Database charset")
    
    # Connection pool settings
    pool_minsize: int = Field(default=1, ge=1, description="Minimum pool connections")
    pool_maxsize: int = Field(default=10, ge=1, description="Maximum pool connections")
    pool_recycle: int = Field(default=3600, ge=-1, description="Pool connection recycle time (-1 for no recycle)")
    
    # Connection timeouts
    connect_timeout: float = Field(default=10.0, gt=0, description="Connection timeout in seconds")
    read_timeout: float = Field(default=30.0, gt=0, description="Read timeout in seconds")
    write_timeout: float = Field(default=30.0, gt=0, description="Write timeout in seconds")
    
    # Security settings
    use_ssl: bool = Field(default=False, description="Use SSL connection")
    ssl_ca: Optional[str] = Field(default=None, description="SSL CA certificate path")
    ssl_cert: Optional[str] = Field(default=None, description="SSL client certificate path")
    ssl_key: Optional[str] = Field(default=None, description="SSL client key path")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    
    # Query execution limits
    max_query_length: int = Field(default=1048576, ge=1, description="Maximum query length (1MB default)")
    query_timeout: float = Field(default=60.0, gt=0, description="Query execution timeout")
    max_rows_limit: int = Field(default=10000, ge=1, description="Maximum rows to return")
    
    @field_validator('password')
    def password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Database password cannot be empty')
        return v
    
    @field_validator('user')
    def user_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Database username cannot be empty')
        return v
    
    @field_validator('host')
    def host_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Database host cannot be empty')
        return v
    
    class Config:
        env_prefix = "DATABASE_"
        case_sensitive = False
        validate_assignment = True

class ServerConfig(BaseSettings):
    """Server configuration for both stdio and SSE modes."""
    
    # Server settings
    host: str = Field(default="localhost", description="Server host for SSE mode")
    port: int = Field(default=8080, ge=1, le=65535, description="Server port for SSE mode")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Transport mode
    transport_mode: str = Field(default="stdio", description="Transport mode: stdio, sse, streamable-http, or auto")
    
    # SSE specific settings
    sse_path: str = Field(default="/sse", description="SSE endpoint path")
    sse_messages_path: str = Field(default="/messages", description="SSE messages endpoint path")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: 'json' or 'text'")
    log_destination: str = Field(default="file", description="Log destination: 'file', 'stdout', 'stderr', or 'both'")
    log_file_path: str = Field(default="./logs/database_mcp.log", description="Log file path (when using file destination)")
    log_max_file_size: str = Field(default="100MB", description="Maximum log file size before rotation")
    log_backup_count: int = Field(default=5, ge=1, description="Number of backup log files to keep")
    log_include_timestamp: bool = Field(default=True, description="Include timestamp in logs")
    log_include_trace_id: bool = Field(default=True, description="Include trace ID in logs")
    
    # Security settings
    enable_cors: bool = Field(default=True, description="Enable CORS for SSE mode")
    allowed_origins: list = Field(default=["*"], description="Allowed CORS origins")
    
    # Health check settings
    enable_health_check: bool = Field(default=True, description="Enable health check endpoint")
    health_check_path: str = Field(default="/health", description="Health check endpoint path")
    
    @field_validator('transport_mode')
    def validate_transport_mode(cls, v):
        allowed_modes = {"stdio", "sse", "streamable-http", "auto"}
        if v.lower() not in allowed_modes:
            raise ValueError(f'Transport mode must be one of: {allowed_modes}')
        return v.lower()
    
    @field_validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    @field_validator('log_format')
    def validate_log_format(cls, v):
        allowed_formats = {"json", "text"}
        if v.lower() not in allowed_formats:
            raise ValueError(f'Log format must be one of: {allowed_formats}')
        return v.lower()
    
    @field_validator('log_destination')
    def validate_log_destination(cls, v):
        allowed_destinations = {"file", "stdout", "stderr", "both"}
        if v.lower() not in allowed_destinations:
            raise ValueError(f'Log destination must be one of: {allowed_destinations}')
        return v.lower()
    
    class Config:
        env_prefix = "SERVER_"
        case_sensitive = False

class MCPConfig(BaseSettings):
    """MCP server specific configuration."""
    
    # MCP settings
    server_name: str = Field(default="database-mcp", description="MCP server name")
    server_version: str = Field(default="1.0.0", description="MCP server version")
    
    # Feature toggles
    enable_query_execution: bool = Field(default=True, description="Enable SQL query execution")
    enable_schema_introspection: bool = Field(default=True, description="Enable database schema introspection")
    enable_query_explain: bool = Field(default=True, description="Enable query EXPLAIN functionality")
    
    # Tool configuration
    tool_mode: str = Field(default="lite", description="Tool set mode: 'lite' (8 core tools) or 'full' (22 tools)")
    
    # Safety settings
    readonly_mode: bool = Field(default=False, description="Enable read-only mode (SELECT queries only)")
    allowed_query_types: list = Field(
        default=["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "UPDATE"],
        description="Allowed query types (case-insensitive)"
    )
    
    # Rate limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable query rate limiting")
    max_queries_per_minute: int = Field(default=100, ge=1, description="Maximum queries per minute")
    
    @field_validator('tool_mode')
    def validate_tool_mode(cls, v):
        allowed_modes = {"lite", "full"}
        if v.lower() not in allowed_modes:
            raise ValueError(f'Tool mode must be one of: {allowed_modes}')
        return v.lower()
    
    class Config:
        env_prefix = "MCP_"
        case_sensitive = False

class AppConfig:
    """Main application configuration container."""
    
    def __init__(self):
        """Initialize all configuration sections."""
        try:
            self.database = DatabaseConfig()
            self.server = ServerConfig()
            self.mcp = MCPConfig()
            self._validate_config()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _validate_config(self):
        """Cross-validate configuration settings."""
        # Validate SSL settings
        if self.database.use_ssl:
            if self.database.ssl_ca and not os.path.exists(self.database.ssl_ca):
                raise ValueError(f"SSL CA file not found: {self.database.ssl_ca}")
            if self.database.ssl_cert and not os.path.exists(self.database.ssl_cert):
                raise ValueError(f"SSL certificate file not found: {self.database.ssl_cert}")
            if self.database.ssl_key and not os.path.exists(self.database.ssl_key):
                raise ValueError(f"SSL key file not found: {self.database.ssl_key}")
        
        # Validate readonly mode restrictions
        if self.mcp.readonly_mode:
            safe_queries = {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN"}
            self.mcp.allowed_query_types = [
                q for q in self.mcp.allowed_query_types 
                if q.upper() in safe_queries
            ]
    
    def get_database_dsn(self) -> str:
        """Get database DSN string for logging purposes (without password)."""
        return f"mysql://{self.database.user}@{self.database.host}:{self.database.port}/{self.database.database or 'default'}"
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters for aiomysql."""
        params = {
            'host': self.database.host,
            'port': self.database.port,
            'user': self.database.user,
            'password': self.database.password,
            'charset': self.database.charset,
            'minsize': self.database.pool_minsize,
            'maxsize': self.database.pool_maxsize,
            'pool_recycle': self.database.pool_recycle if self.database.pool_recycle > 0 else None,
            'connect_timeout': self.database.connect_timeout,
            'autocommit': False,  # Explicit transaction control
        }
        
        # Add database name if specified
        if self.database.database:
            params['db'] = self.database.database
        
        # Add SSL parameters if enabled
        if self.database.use_ssl:
            ssl_params = {}
            if self.database.ssl_ca:
                ssl_params['ca'] = self.database.ssl_ca
            if self.database.ssl_cert:
                ssl_params['cert'] = self.database.ssl_cert
            if self.database.ssl_key:
                ssl_params['key'] = self.database.ssl_key
            ssl_params['check_hostname'] = self.database.verify_ssl
            params['ssl'] = ssl_params
        
        return params
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'database': {
                **self.database.dict(),
                'password': '***REDACTED***'  # Hide password in logs
            },
            'server': self.server.dict(),
            'mcp': self.mcp.dict()
        }

# Global configuration instance
config: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """Get or create the global configuration instance."""
    global config
    if config is None:
        config = AppConfig()
    return config

def reload_config() -> AppConfig:
    """Reload the configuration from environment variables."""
    global config
    config = AppConfig()
    return config

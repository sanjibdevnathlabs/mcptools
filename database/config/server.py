"""Server configuration classes."""

from typing import Optional


class ServerConfig:
    """Server configuration from [server] section"""

    host: str = "localhost"
    port: int = 8080
    transport_mode: str = "stdio"
    debug: bool = False
    enable_cors: bool = False
    allowed_origins: Optional[str] = None
    enable_health_check: bool = True
    health_check_path: str = "/health"
    sse_path: str = "/sse"
    sse_messages_path: str = "/messages"
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/database_mcp.log"
    log_destination: str = "file"  # file, stderr, stdout, both
    log_format: str = "json"  # json or text
    log_include_timestamp: bool = True
    log_include_trace_id: bool = True
    log_max_file_size: str = "10MB"
    log_backup_count: int = 5
    log_file_path: str = "logs/database_mcp.log"  # Alias for log_file

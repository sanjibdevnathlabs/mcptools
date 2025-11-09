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

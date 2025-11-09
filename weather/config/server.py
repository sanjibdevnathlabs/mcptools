"""Server configuration classes."""


class ServerConfig:
    """Server configuration from [server] section"""

    transport_mode: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000

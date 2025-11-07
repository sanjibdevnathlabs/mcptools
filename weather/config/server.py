"""Server configuration classes."""


class ServerConfig:
    """Server configuration from [server] section"""
    
    transport_mode: str = "stdio"
    log_level: str = "INFO"


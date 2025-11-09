"""Logger configuration for Calculator MCP Server"""


class LoggerConfig:
    """Logger configuration from [logger] section"""

    level: str = "INFO"
    format: str = "text"  # text or json
    destination: str = "stdout"  # stdout, stderr, file, both
    file_path: str = "logs/calculator.log"


"""Logger configuration class - shared across all MCPs."""


class LoggerConfig:
    """Logger configuration from [logger] section"""

    level: str = "INFO"
    format: str = "text"  # text or json
    destination: str = "stdout"  # stdout, stderr, file, both
    file_path: str = "logs/app.log"

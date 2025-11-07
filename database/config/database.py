"""Database configuration classes."""

from typing import Optional


class DatabaseConfig:
    """Database connection configuration from [database] section"""

    host: str = "localhost"
    port: int = 3306
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    charset: str = "utf8mb4"
    use_ssl: bool = False
    pool_size: int = 10
    pool_recycle: int = 3600
    query_timeout: int = 30
    max_query_length: int = 1048576  # 1MB
    max_rows_limit: int = 1000  # Maximum rows returned per query

"""Security configuration classes."""

from typing import Optional


class SecurityConfig:
    """Security settings from [security] section"""

    enable_sql_analysis: bool = True
    max_rows_returned: int = 1000
    enable_ssl: bool = False
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None

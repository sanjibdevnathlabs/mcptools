"""Application configuration classes."""

from typing import Optional


class AppConfig:
    """Holds application metadata from the [app] TOML section"""
    
    name: Optional[str] = None
    environment: Optional[str] = None
    version: Optional[str] = None


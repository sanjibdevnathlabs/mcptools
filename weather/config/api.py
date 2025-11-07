"""API configuration classes."""

from typing import Optional


class APIConfig:
    """API configuration from [api] section"""
    
    openweather_api_key: Optional[str] = None
    openweather_api_base: str = "https://api.openweathermap.org/data/2.5"
    timeout: int = 30
    user_agent: str = "weather-app/1.0"


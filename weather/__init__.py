"""
Weather MCP Server

A Model Context Protocol (MCP) server for weather information using OpenWeatherMap API.
"""

__version__ = "1.0.0"
__author__ = "Weather MCP Team"

from weather.config import APIConfig, AppConfig, Config, ServerConfig

__all__ = [
    "Config",
    "AppConfig",
    "APIConfig",
    "ServerConfig",
]

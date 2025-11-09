"""
Generic configuration loader for MCP servers.

Loads configuration from TOML files with environment variable interpolation
and multi-environment support.
"""

import os
import re
import tomllib
from pathlib import Path
from typing import Any, Dict


class ConfigLoader:
    """
    Generic configuration loader that reads TOML files and interpolates environment variables.
    
    Usage:
        config_loader = ConfigLoader(config_dir=Path("environment"))
        settings = config_loader.load()
        
        # Apply to your config objects
        config.app.name = settings["app"]["name"]
        config.server.port = int(settings["server"]["port"])
    """
    
    def __init__(self, config_dir: Path):
        """
        Initialize config loader.
        
        Args:
            config_dir: Directory containing TOML configuration files
        """
        self.config_dir = config_dir
    
    def load(self) -> Dict[str, Any]:
        """
        Load and merge TOML configuration files.
        
        Returns:
            Dictionary containing merged and interpolated configuration
            
        Raises:
            FileNotFoundError: If default.toml is not found
        """
        default_path = self.config_dir / "default.toml"
        
        # Load default config
        if not default_path.exists():
            raise FileNotFoundError(
                f"Default config not found: {default_path}\n"
                f"Create {self.config_dir}/default.toml with base configuration."
            )
        
        settings = self._load_toml(default_path)
        
        # Default to 'dev' environment if APP_ENV not set
        env = os.environ.get("APP_ENV", "dev")
        
        # Load environment-specific config
        env_path = self.config_dir / f"{env}.toml"
        if env_path.exists():
            env_config = self._load_toml(env_path)
            self._merge_dicts(settings, env_config)
        
        # Interpolate environment variables
        return self._interpolate(settings)
    
    def _load_toml(self, path: Path) -> Dict[str, Any]:
        """
        Load TOML file.
        
        Args:
            path: Path to TOML file
            
        Returns:
            Dictionary of configuration values
        """
        with open(path, "rb") as f:
            return tomllib.load(f)
    
    def _merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Recursively merge override dict into base dict.
        
        Args:
            base: Base dictionary to merge into (modified in-place)
            override: Dictionary with override values
        """
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value
    
    def _interpolate(self, item: Any) -> Any:
        """
        Recursively replace $VAR or ${VAR} with os.environ values.
        Supports default values: ${VAR:-default}
        
        Examples:
            ${HOST:-127.0.0.1}  → "127.0.0.1" if HOST not set
            ${PORT:-8000}       → "8000" if PORT not set
            ${MODE:-stdio}      → "stdio" if MODE not set
            
        Args:
            item: Value to interpolate (can be dict, list, str, or other)
            
        Returns:
            Interpolated value
        """
        if isinstance(item, dict):
            return {k: self._interpolate(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [self._interpolate(v) for v in item]
        elif isinstance(item, str):
            return self._expand_with_defaults(item)
        return item
    
    def _expand_with_defaults(self, value: str) -> str:
        """
        Expand environment variables with shell-style default values.
        
        Supports:
            ${VAR}          → Replace with env var (empty if not set)
            ${VAR:-default} → Replace with env var or default if not set
            
        Args:
            value: String potentially containing environment variable references
            
        Returns:
            String with environment variables expanded
        """
        # Pattern: ${VAR:-default} or ${VAR}
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'
        
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) or ""  # Default to empty string if no default
            return os.environ.get(var_name, default_value)
        
        # First handle ${VAR:-default} syntax
        result = re.sub(pattern, replace_var, value)
        
        # Then handle simple $VAR syntax (for backwards compatibility)
        result = os.path.expandvars(result)
        
        return result


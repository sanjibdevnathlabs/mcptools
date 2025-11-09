# Shared Utilities for MCP Servers

This directory contains common utilities and modules shared across all MCP servers in the mcptools repository.

## 📦 Modules

### `shared.config` - Configuration Loading

Generic configuration loader and shared config classes.

**Features:**
- Load from `environment/*.toml` files
- Environment variable interpolation (`${VAR}` and `${VAR:-default}`)
- Multi-environment support (dev, test, docker, prod)
- Automatic merging of default and environment-specific configs
- Shared `LoggerConfig` class for consistent logging configuration

**Usage:**

```python
from pathlib import Path
from shared.config import ConfigLoader, LoggerConfig

# In your MCP's config/__init__.py
config_dir = Path(__file__).parent.parent / "environment"
loader = ConfigLoader(config_dir)
settings = loader.load()

# Apply to your config objects
config.app.name = settings["app"]["name"]
config.server.port = int(settings["server"]["port"])

# Use shared LoggerConfig
config.logger = LoggerConfig()
for key, value in settings.get("logger", {}).items():
    if hasattr(config.logger, key):
        setattr(config.logger, key, value)
```

**Example TOML:**

```toml
# environment/default.toml
[app]
name = "my-mcp"
environment = "${APP_ENV:-dev}"

[server]
host = "${FASTMCP_HOST:-127.0.0.1}"
port = "${FASTMCP_PORT:-8000}"
```

### `shared.logging` - Logging Setup

Consistent logging configuration across all MCP servers.

**Features:**
- JSON and text formatting
- Configurable log levels
- Multiple output destinations (stdout, stderr)
- Structured logging support

**Usage:**

```python
from shared.logging import setup_logging
from myapp.config import Config

config = Config()
logger = setup_logging(config, "myapp")

logger.info("Application started")
logger.error("Error occurred", exc_info=True)
```

**Required Config Attributes:**

Your config object must have these attributes:

```python
class ServerConfig:
    log_level: str = "INFO"        # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "text"       # text or json
    log_destination: str = "stdout" # stdout, stderr, both
```

## 🏗️ Structure

```
shared/
├── __init__.py
├── README.md
├── config/
│   ├── __init__.py
│   ├── loader.py       # ConfigLoader class
│   └── logger.py       # LoggerConfig class (shared across all MCPs)
└── logging/
    ├── __init__.py
    └── setup.py        # setup_logging, JSONFormatter, TextFormatter
```

## 🔧 Adding to New MCP

To use shared modules in a new MCP server:

1. **Config Setup:**

```python
# myapp/config/__init__.py
from pathlib import Path
from shared.config import ConfigLoader
from myapp.config.app import AppConfig
from myapp.config.server import ServerConfig

class Config:
    app: AppConfig
    server: ServerConfig
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.app = AppConfig()
        self.server = ServerConfig()
        
        config_dir = Path(__file__).parent.parent / "environment"
        loader = ConfigLoader(config_dir)
        settings = loader.load()
        
        self._apply_config_values(settings)

    def _apply_config_values(self, settings: dict):
        # Apply settings to your config objects
        for key, value in settings.get("app", {}).items():
            if hasattr(self.app, key):
                setattr(self.app, key, value)
        
        for key, value in settings.get("server", {}).items():
            if hasattr(self.server, key):
                if key == "port" and isinstance(value, str):
                    value = int(value)
                setattr(self.server, key, value)
```

2. **Logging Setup:**

```python
# myapp/main.py
from shared.logging import setup_logging
from myapp.config import Config

config = Config()
logger = setup_logging(config, "myapp")

logger.info("Starting MyApp MCP Server")
```

3. **TOML Files:**

```toml
# environment/default.toml
[app]
name = "myapp"
environment = "${APP_ENV:-dev}"

[server]
transport_mode = "${TRANSPORT_MODE:-stdio}"
host = "${FASTMCP_HOST:-127.0.0.1}"
port = "${FASTMCP_PORT:-8000}"
log_level = "${LOG_LEVEL:-INFO}"
log_format = "text"
log_destination = "stdout"
```

```toml
# environment/docker.toml
[app]
environment = "docker"

[server]
log_format = "json"  # JSON for container logging
```

## ✅ Benefits

- **DRY**: Write config and logging logic once, use everywhere
- **Consistency**: All MCPs use same patterns
- **Maintainability**: Bug fixes in one place benefit all
- **Type Safety**: Each MCP defines its own strongly-typed config classes
- **Flexibility**: Easy to add MCP-specific config sections

## 📝 Conventions

1. Config classes are **specific to each MCP**
2. Config **loading logic** is shared
3. Logging **setup and formatters** are shared
4. Each MCP uses `APP_ENV` to select environment
5. Docker containers use `APP_ENV=docker` with `environment/docker.toml`


# MCP Tools Project Brief

## Project Overview

**Name:** mcptools  
**Type:** Model Context Protocol (MCP) Server Collection  
**Language:** Python 3.13  
**Status:** Production Ready (Post-Conflict Resolution & Testing)

## Purpose

Collection of production-grade MCP servers providing database access, weather information, and calculator functionality through a unified configuration system.

## Architecture

### Core Principles
- **TOML-Based Configuration:** Hierarchical config system with `default.toml` → `dev.toml`/`prod.toml` merging
- **Config Singleton:** Single `Config()` instance per application with environment variable interpolation
- **Isolated Environments:** Each server has its own `config/` and `environment/` folders
- **Multi-Transport Support:** stdio, SSE, and streamable-http transports
- **Structured Logging:** JSON/text logging with file/stderr/stdout destinations

### Server Structure

```
mcptools/
├── database/           # Database MCP Server (MySQL/MariaDB)
│   ├── config/         # Configuration classes
│   ├── environment/    # TOML config files
│   ├── src/            # Source code modules
│   └── main.py         # Entry point
├── weather/            # Weather MCP Server (OpenWeatherMap API)
│   ├── config/         # Configuration classes
│   ├── environment/    # TOML config files
│   └── main.py         # Entry point
├── calculator/         # Calculator MCP Server
│   ├── config/         # Configuration classes
│   ├── environment/    # TOML config files
│   └── main.py         # Entry point
└── requirements.txt    # Shared dependencies
```

## Key Technologies

- **MCP Framework:** FastMCP (Python implementation)
- **Configuration:** TOML with tomllib/tomli
- **Database:** aiomysql, pymysql
- **Weather API:** OpenWeatherMap REST API
- **Dev Tools:** black, ruff, mypy, Makefile
- **Testing:** MCP Inspector (browser-based), Playwright automation

## Key Features

### Database Server
- SQL query execution with security validation
- Pre-execution query analysis
- Fine-grained whitelisting (e.g., `DROP TABLE` allowed, `DROP DATABASE` blocked)
- SQL injection detection
- Connection pooling and timeout management

### Weather Server
- Current weather for Indian cities
- 5-day forecast with coordinates/city support
- OpenWeatherMap API integration

### Calculator Server
- 13 mathematical operations
- Basic: add, subtract, multiply, divide
- Advanced: power, sqrt, cbrt, factorial, log, remainder
- Trigonometry: sin, cos, tan

## Configuration Management

- Environment isolation via TOML files
- Environment variable interpolation (`$VAR`, `${VAR}`)
- Transport-aware logging (stdio forces file-based logs)
- Security-first defaults

## Development Tools

- `make check` - Run all linters and type checkers
- `make format` - Auto-format code with black
- `make lint-fix` - Auto-fix linting issues
- Dynamic MCP server discovery (no manual updates needed)

## Current Status

✅ All servers production-ready  
✅ Comprehensive testing completed  
✅ Security validation verified  
✅ PR #2 conflicts resolved  
✅ Documentation updated

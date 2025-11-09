# MCP Tools

A collection of production-grade Model Context Protocol (MCP) servers built with modern TOML-based configuration and isolated environments.

## 📁 Project Structure

This repository contains three self-contained MCP server applications, each with isolated configuration and environments:

```
mcptools/
├── calculator/           # Calculator MCP Server
│   ├── config/          # Configuration classes
│   ├── environment/     # TOML config files (default.toml, dev.toml, docker.toml)
│   ├── docker/          # Docker image definition
│   ├── deployment/      # Docker Compose for local dev
│   ├── tests/           # Unit and integration tests
│   └── main.py         # Entry point
├── database/            # Database MCP Server
│   ├── config/         # Configuration classes
│   ├── environment/    # TOML config files
│   ├── src/           # Source code modules
│   ├── docker/        # Docker image definition
│   ├── deployment/    # Docker Compose + MySQL
│   ├── tests/         # Unit and integration tests
│   └── main.py       # Entry point
├── weather/            # Weather MCP Server
│   ├── config/        # Configuration classes
│   ├── environment/   # TOML config files
│   ├── docker/        # Docker image definition
│   ├── deployment/    # Docker Compose for local dev
│   ├── tests/         # Unit and integration tests
│   └── main.py       # Entry point
├── shared/             # Shared utilities (common across all MCPs)
│   ├── config/        # Config loading logic & LoggerConfig
│   ├── logging/       # Logging setup, formatters, and stdio handling
│   └── docker/        # Base Docker image (mcp-base)
├── tests/              # E2E tests organized by MCP
│   ├── calculator/    # Calculator E2E tests
│   ├── database/      # Database E2E tests
│   ├── weather/       # Weather E2E tests
│   ├── conftest.py    # Shared pytest configuration
│   └── __init__.py    # Makes tests a package
└── requirements.txt    # Shared dependencies
```

## 🚀 **Core Architecture**

All MCP servers follow a consistent architecture:
- **TOML-Based Configuration**: Hierarchical config with `default.toml` → `dev.toml`/`prod.toml` merging
- **Config Singleton**: Single `Config()` instance per application with environment variable interpolation
- **Isolated Environments**: Each server has its own `config/` and `environment/` folders
- **Multi-Transport Support**: stdio, SSE, and streamable-http transports
- **Structured Logging**: JSON/text logging with file/stderr/stdout destinations

---

## 🗃️ Database MCP Server (`database/`)

A production-grade MCP server for MySQL database interactions with enterprise-level security, monitoring, and schema management capabilities.

**Features:**
- ✅ Secure SQL execution with query validation **before** database execution
- ✅ Fine-grained query whitelisting (e.g., `DROP TABLE` allowed but `DROP DATABASE` blocked)
- ✅ Multi-transport support: stdio, SSE, streamable-http
- ✅ Advanced security with SQL injection prevention and threat monitoring
- ✅ Production monitoring with health checks, metrics, and error tracking
- ✅ Intelligent error handling with retry logic and circuit breakers
- ✅ Advanced schema management with introspection and analysis
- ✅ TOML-based configuration with environment-specific overrides

**Quick Start:**
```bash
cd /path/to/mcptools

# Option 1: Using virtualenv Python (recommended for local development)
/path/to/mcptools/venv/bin/python -m database

# Option 2: Using system Python (ensure dependencies installed)
python -m database

# Run in SSE mode
python -m database --transport sse --port 8080

# Run in HTTP mode (for MCP Inspector)
python -m database --transport streamable-http --port 8080
```

**Configuration:**
- `database/environment/default.toml` - Base configuration
- `database/environment/dev.toml` - Development overrides (gitignored)
- `database/environment/prod.toml` - Production overrides

📖 **[Read the Database MCP Server Documentation →](database/README.md)**

---

## 🌤️ Weather MCP Server (`weather/`)

A fast and lightweight MCP server for fetching weather data from OpenWeatherMap API for Indian locations.

**Features:**
- ✅ Current weather and 5-day forecast for Indian cities
- ✅ Support for city name or latitude/longitude coordinates
- ✅ TOML-based configuration with API key management
- ✅ Multi-transport support: stdio, SSE, streamable-http
- ✅ Structured error handling and logging

**Quick Start:**
```bash
# Set OpenWeatherMap API key in environment
export OPENWEATHER_API_KEY="your_api_key_here"

# Run the server
python -m weather

# Or specify transport
python -m weather  # Uses config from environment/default.toml
```

**Configuration:**
- `weather/environment/default.toml` - Base configuration
- `weather/environment/dev.toml` - Development overrides (gitignored)
- Set `OPENWEATHER_API_KEY` environment variable

---

## 🧮 Calculator MCP Server (`calculator/`)

A simple MCP server providing basic and advanced mathematical operations with **96% test coverage**.

**Features:**
- ✅ Basic operations: add, subtract, multiply, divide
- ✅ Advanced operations: power, square root, logarithm, trigonometry
- ✅ TOML-based configuration with shell-style defaults
- ✅ Multi-transport support: stdio, SSE, streamable-http
- ✅ Comprehensive test suite: 112 tests (unit, integration, E2E)
- ✅ 96% code coverage
- ✅ Production-ready with full E2E testing across all protocols

**Quick Start:**
```bash
# Run the server
python -m calculator

# Run tests
make test-calc          # Run all calculator tests with coverage
make test              # Run all project tests

# Test with MCP Inspector
# Transport: STDIO
# Command: /path/to/venv/bin/python
# Arguments: -m calculator
```

**Configuration:**
- `calculator/environment/default.toml` - Base configuration with shell-style defaults
- `calculator/environment/dev.toml` - Development overrides (gitignored)
- `calculator/environment/test.toml` - Test environment configuration
- Supports `${VAR:-default}` syntax for environment variable fallbacks

---

## 🚀 Getting Started

### Quick Start with Docker (Recommended)

Each MCP has its own Docker setup for local development with **automatic test execution**:

```bash
# Build base image (required first time)
make docker-build-base

# Run specific MCP with docker-compose
# Each command automatically:
#  1. Builds the MCP image(s)
#  2. Runs quality checks (black, ruff, mypy)
#  3. Executes all tests (unit + integration + E2E)
#  4. Starts service containers (SSE + HTTP transports)
make docker-compose-up-calculator   # Calculator on ports 8080 (SSE) + 8081 (HTTP)
make docker-compose-up-weather      # Weather on ports 8082 (SSE) + 8083 (HTTP)
make docker-compose-up-database     # Database on ports 8086 (SSE) + 8087 (HTTP) + MySQL 3306

# View logs (including test results)
make logs-calculator
make logs-weather
make logs-database

# Stop services
make docker-compose-down-calculator
make docker-compose-down-weather
make docker-compose-down-database

# Check test results
docker ps -a --filter "name=calculator-test"   # Exit code 0 = success ✅
docker ps -a --filter "name=weather-test"      # Exit code 0 = success ✅
docker ps -a --filter "name=database-test"     # Exit code 0 = success ✅
```

**Test Containers:** Each MCP includes a test service that:
- Runs automatically with `docker-compose up`
- Executes quality checks + all tests
- Exits with status code (0 = pass, non-zero = fail)
- Provides immediate feedback on code quality

**Per-MCP Documentation:**
- 📖 [Calculator Docker Guide](calculator/docker/README.md) - Build & configuration details
- 📖 [Calculator Deployment Guide](calculator/deployment/local/README.md) - Local development with docker-compose
- 📖 [Database Docker Guide](database/docker/README.md) - Build & configuration details
- 📖 [Database Deployment Guide](database/deployment/local/README.md) - Local development with MySQL
- 📖 [Weather Docker Guide](weather/docker/README.md) - Build & configuration details
- 📖 [Weather Deployment Guide](weather/deployment/local/README.md) - Local development with API key

### Installation from Source

```bash
# Clone the repository
git clone <repository-url>
cd mcptools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Each server uses **TOML-based configuration** with hierarchical merging:

1. **`environment/default.toml`** - Base configuration (committed to git)
2. **`environment/dev.toml`** - Development overrides (gitignored, create locally)
3. **`environment/prod.toml`** - Production overrides (committed to git)

**Example: Database Server Configuration**

```toml
# database/environment/dev.toml
[database]
host = "localhost"
user = "root"
password = "root"
database = ""  # Empty = connect to any database

[server]
transport_mode = "stdio"

[mcp]
allowed_query_types = "SHOW, DESCRIBE"  # Comma-separated
```

**Environment Variable Interpolation with Shell-Style Defaults:**

```toml
# Use ${VAR:-default} for environment variables with fallback defaults
[database]
host = "${DB_HOST:-localhost}"
password = "${DB_PASSWORD:-}"

[server]
transport_mode = "${TRANSPORT_MODE:-stdio}"
host = "${FASTMCP_HOST:-127.0.0.1}"
port = "${FASTMCP_PORT:-8000}"
```

### Running Servers

```bash
# Database Server
python -m database

# Weather Server
export OPENWEATHER_API_KEY="your_key"
python -m weather

# Calculator Server
python -m calculator
```

### Testing with MCP Inspector

```bash
# Start MCP Inspector
npx @modelcontextprotocol/inspector

# Configure in Inspector:
# Transport: STDIO
# Command: /absolute/path/to/mcptools/venv/bin/python
# Arguments: -m database  (or weather, calculator)
# Working Directory: /absolute/path/to/mcptools
```

---

## 🛠️ Development

Each MCP server follows a consistent architecture:

### Folder Structure

```
server/
├── config/
│   ├── __init__.py      # Config singleton with TOML loading
│   ├── app.py          # Application config
│   ├── server.py       # Server config
│   └── ...             # Server-specific config
├── environment/
│   ├── default.toml    # Base configuration
│   ├── dev.toml        # Dev overrides (gitignored)
│   └── prod.toml       # Production overrides
├── src/                # Source code (database only)
│   └── ...
├── main.py            # Entry point
├── __init__.py
└── __main__.py        # Enables python -m server
```

### Config Singleton Pattern

```python
from database.config import Config

# Initialize (loads and merges TOML files)
config = Config()

# Access configuration
print(config.database.host)
print(config.server.transport_mode)
print(config.mcp.allowed_query_types)
```

### Design Principles

- **Isolated Environments**: Each server has its own config and dependencies
- **TOML Over .env**: Type-safe, hierarchical configuration
- **Config Singleton**: Single source of truth per application
- **Multi-Transport**: Support stdio, SSE, streamable-http
- **Structured Logging**: JSON/text logging with flexible destinations
- **Security First**: Validation before execution (database server)

---

## 🧪 Testing

### Test Suite Overview

The project includes comprehensive testing with **354 total tests passing**:

**Calculator MCP: ✅ Production-Ready (96% coverage)**
- **112 tests** (unit + integration + E2E)
- E2E tests for all 3 protocols (STDIO, SSE, Streamable-HTTP)
- Validated across all transport modes
- ✅ All tests passing

**Weather MCP: ✅ Production-Ready**
- **51 tests** (unit + integration + E2E)
- E2E tests for all 3 protocols (STDIO, SSE, Streamable-HTTP)
- Comprehensive integration testing
- ✅ All tests passing

**Database MCP: ✅ Production-Ready**
- **191 tests** (unit + integration + E2E)
- E2E tests for all 3 protocols (STDIO, SSE, Streamable-HTTP)
- Full MySQL integration testing
- Security and monitoring coverage
- ✅ All tests passing

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests with coverage
make test

# Run server-specific tests (fast iteration)
make test-calc          # Calculator only (112 tests)
make test-weather       # Weather only (51 tests)
make test-db            # Database only (191 tests)

# Run code quality checks
make check              # Format + lint + type-check (black, ruff, mypy)
make fix                # Auto-fix all issues
```

### Docker-Based Testing

All MCPs include **automatic test execution** in Docker containers:

```bash
# Tests run automatically with docker-compose up
make docker-compose-up-calculator   # Builds, runs, and tests calculator
make docker-compose-up-weather      # Builds, runs, and tests weather
make docker-compose-up-database     # Builds, runs, and tests database

# Or run tests explicitly in Docker
make docker-test-calculator   # Run quality checks + tests in Docker
make docker-test-weather      # Run quality checks + tests in Docker
make docker-test-database     # Run quality checks + tests in Docker
make docker-test-all          # Run all Docker tests

# Test containers exit with proper status codes:
# - Exit 0: All tests passed ✅
# - Non-zero: Tests failed ❌
```

**What's Tested in Docker:**
- ✅ Code quality (black, ruff, mypy)
- ✅ Unit tests with coverage
- ✅ Integration tests
- ✅ E2E tests for all transport protocols

### Makefile Commands

**Essential Commands:**

```bash
# Development
make help               # Show all available commands
make install            # Install all dependencies
make check              # Run all quality checks
make fix                # Auto-fix code issues
make clean              # Clean build artifacts

# Testing (Local)
make test               # Run all tests with coverage (354 tests)
make test-calc          # Test calculator only (112 tests, fast)
make test-weather       # Test weather only (51 tests, fast)
make test-db            # Test database only (191 tests, fast)

# Testing (Docker)
make docker-test-calculator # Run quality checks + tests in Docker
make docker-test-weather    # Run quality checks + tests in Docker
make docker-test-database   # Run quality checks + tests in Docker
make docker-test-all        # Run all Docker tests

# Running Locally (Python)
make run-calculator     # Run calculator server
make run-weather        # Run weather server
make run-database       # Run database server

# Docker - Building Images
make docker-build-base       # Build shared base image (~1GB, reused by all MCPs)
make docker-build-all        # Build all MCP images
make docker-build-calculator # Build calculator image
make docker-build-database   # Build database image
make docker-build-weather    # Build weather image

# Docker - Local Development
make docker-compose-up-calculator   # Start calculator (SSE + HTTP)
make docker-compose-up-database     # Start database + MySQL (SSE + HTTP)
make docker-compose-up-weather      # Start weather (SSE + HTTP)

make docker-compose-down-calculator # Stop calculator
make docker-compose-down-database   # Stop database + MySQL
make docker-compose-down-weather    # Stop weather

make logs-calculator   # View calculator logs
make logs-database     # View database logs
make logs-weather      # View weather logs
```

### Test Coverage

```bash
# After running tests, view coverage report
open htmlcov/index.html  # Opens in browser

# Coverage reports are also generated in terminal
make test                # Shows coverage in terminal + HTML
```

---

## 📋 Requirements

- **Python 3.11+** (3.10+ with `tomli` for TOML parsing)
- **Virtual environment** (strongly recommended)
- **FastMCP** framework
- **pytest** and plugins for testing (see `requirements-test.txt`)
- Server-specific dependencies (see `requirements.txt`)

---

## 🚀 CI/CD Pipeline

This project uses **GitHub Actions** for automated CI/CD with comprehensive optimizations:

### **Key Features:**

- ✅ **Auto-discovery** - Automatically detects all MCP servers
- ✅ **Parallel execution** - Matrix strategy for concurrent testing and building
- ✅ **Comprehensive caching** - Pip, pytest, and Docker layer caching (**40-60% faster**)
- ✅ **Smart triggers** - CI only on master commits and PRs (saves CI minutes)
- ✅ **Makefile integration** - Local dev and CI use identical commands
- ✅ **Security scanning** - Bandit, Safety, Pip-audit, and Trivy

### **Trigger Strategy:**

```yaml
on:
  push:
    branches: [master]  # ✅ Every commit to master
  pull_request:         # ✅ All PRs (any branch → any branch)
```

**Benefits:**
- Master is always validated
- Feature branches only trigger CI on PR (no wasted CI on WIP commits)
- Fast feedback with parallel execution

### **Pipeline Stages:**

1. **Auto-Discover MCPs** - Dynamically finds all MCP servers
2. **Detect Changes** - Skips unnecessary builds
3. **Compute Tags** - PR = branch hash, Master = commit SHA
4. **Build Base Image** - Multi-platform (amd64, arm64) with caching
5. **Quality Checks** - black, ruff, mypy (3-4x faster with caching)
6. **Security Scan** - Bandit, Safety, Pip-audit
7. **Test MCPs** - Parallel matrix testing with per-MCP caching (2-3x faster)
8. **Build MCP Images** - Production images (master only)
9. **Security Scans** - Trivy image scanning (master only)

### **Performance:**

| Job | Before | After | Improvement |
|-----|---------|-------|-------------|
| quality-checks | 2-3 min | 30-60 sec | **3-4x faster** |
| test-mcps (each) | 3-5 min | 1-2 min | **2-3x faster** |
| build-base (cache hit) | 5-10 min | 30-60 sec | **10x faster** |

**Total:** 40-60% faster on subsequent runs 🎉

### **Local Testing:**

Test exactly what CI will run:

```bash
make install    # Install dependencies
make check      # Quality checks (black, ruff, mypy)
make test-calc  # Run calculator tests
make test-weather  # Run weather tests
make test-db    # Run database tests
```

📖 **[Read the complete CI/CD Guide →](.github/CI_CD_GUIDE.md)**

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch for the specific MCP server you're working on
3. Make your changes in the appropriate directory
4. Follow the existing code style and documentation patterns
5. Run `make check` and `make test` locally before creating a PR
6. Submit a pull request (CI will automatically run)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Each MCP server is a complete, production-ready solution. Start with the one that matches your use case!**

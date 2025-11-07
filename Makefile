.PHONY: help install lint lint-fix format format-check type-check check fix clean run-database run-weather run-calculator

# Automatically discover MCP server directories (directories with main.py and config/ subdirectory)
MCP_DIRS := $(shell find . -maxdepth 1 -type d ! -name '.' ! -name '.git' ! -name 'venv' ! -name '__pycache__' ! -name '.pytest_cache' ! -name '.mypy_cache' ! -name '.ruff_cache' -exec test -f {}/main.py -a -d {}/config \; -print | sed 's|^\./||')

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install         - Install all dependencies (production + dev)"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  make lint            - Run linters (ruff)"
	@echo "  make lint-fix        - Auto-fix linting issues"
	@echo "  make format          - Format code with black"
	@echo "  make format-check    - Check code formatting without modifying"
	@echo "  make type-check      - Run type checker (mypy)"
	@echo ""
	@echo "✅ Combined:"
	@echo "  make check           - Run all checks (format-check + lint + type-check)"
	@echo "  make fix             - Auto-fix formatting and linting issues"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean           - Clean build artifacts and cache"
	@echo ""
	@echo "🚀 Run Servers:"
	@echo "  make run-database    - Run database MCP server"
	@echo "  make run-weather     - Run weather MCP server"
	@echo "  make run-calculator  - Run calculator MCP server"
	@echo ""
	@echo "📋 Detected MCP servers: $(MCP_DIRS)"

# Virtual environment
venv:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Install all dependencies (production + dev)
# Why separate requirements-dev.txt?
# - Keeps production images lean (no black, ruff, mypy in prod)
# - Faster CI/CD pipelines (production installs only what's needed)
# - Clear separation between runtime and development tools
install:
	@echo "📦 Installing all dependencies (production + development)..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "✅ Installation complete!"

# Linting with ruff (dynamically discovers MCP servers)
lint:
	@echo "🔍 Running ruff linter on: $(MCP_DIRS)"
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		ruff check $(MCP_DIRS); \
	fi

# Auto-fix linting issues
lint-fix:
	@echo "🔧 Auto-fixing linting issues with ruff..."
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		ruff check --fix $(MCP_DIRS); \
	fi

# Format code with black
format:
	@echo "✨ Formatting code with black on: $(MCP_DIRS)"
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		black $(MCP_DIRS); \
	fi

# Check formatting without modifying
format-check:
	@echo "🔍 Checking code formatting with black..."
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		black --check $(MCP_DIRS); \
	fi

# Type checking with mypy (dynamically discovers MCP servers)
type-check:
	@echo "🔍 Running type checker (mypy) on: $(MCP_DIRS)"
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		for dir in $(MCP_DIRS); do \
			echo "Checking $$dir..."; \
			if [ -d "$$dir/src" ]; then \
				mypy $$dir/src/ $$dir/config/ $$dir/main.py 2>&1 || echo "⚠️  Type checking found issues in $$dir"; \
			else \
				mypy $$dir/config/ $$dir/main.py 2>&1 || echo "⚠️  Type checking found issues in $$dir"; \
			fi; \
		done \
	fi

# Run all checks
check: format-check lint type-check
	@echo "✅ All checks completed!"

# Auto-fix everything possible
fix: format lint-fix
	@echo "✅ Auto-fixes applied!"

# Clean build artifacts and cache
clean:
	@echo "🧹 Cleaning build artifacts and cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete!"

# Run MCP servers
run-database:
	@echo "🚀 Starting database MCP server..."
	python -m database

run-weather:
	@echo "🌤️  Starting weather MCP server..."
	python -m weather

run-calculator:
	@echo "🧮 Starting calculator MCP server..."
	python -m calculator


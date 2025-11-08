.PHONY: help install check fix clean test test-calc test-weather test-db run-database run-weather run-calculator

# Automatically discover MCP server directories (directories with main.py and config/ subdirectory)
MCP_DIRS := $(shell find . -maxdepth 1 -type d ! -name '.' ! -name '.git' ! -name 'venv' ! -name '__pycache__' ! -name '.pytest_cache' ! -name '.mypy_cache' ! -name '.ruff_cache' -exec test -f {}/main.py -a -d {}/config \; -print | sed 's|^\./||')

# Default target
help:
	@echo "═══════════════════════════════════════════════════════════════════"
	@echo "📦 MCP Servers Toolkit - Essential Commands"
	@echo "═══════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "📦 Setup:"
	@echo "  make install    - Install all dependencies"
	@echo ""
	@echo "✅ Code Quality:"
	@echo "  make check      - Run all checks (format + lint + type-check)"
	@echo "  make fix        - Auto-fix all issues (format + lint)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test       - Run all tests with coverage report"
	@echo "  make test-calc  - Test calculator only (fast iteration)"
	@echo "  make test-weather   - Test weather only (fast iteration)"
	@echo "  make test-db    - Test database only (fast iteration)"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean      - Clean build artifacts and cache"
	@echo ""
	@echo "🚀 Run Servers:"
	@echo "  make run-database   - Run database MCP server"
	@echo "  make run-weather    - Run weather MCP server"
	@echo "  make run-calculator - Run calculator MCP server"
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════════"
	@echo "📋 Detected MCP servers: $(MCP_DIRS)"
	@echo "═══════════════════════════════════════════════════════════════════"

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
	@echo "📦 Installing all dependencies (production + dev + test)..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -r requirements-test.txt
	@echo "✅ Installation complete!"

# ============================================================================
# Code Quality Commands
# ============================================================================

# Run all checks (format + lint + type-check)
check:
	@echo "✅ Running all code quality checks..."
	@echo ""
	@echo "1️⃣ Checking code formatting with black..."
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		black --check $(MCP_DIRS) || (echo "❌ Format check failed. Run 'make fix' to auto-fix." && exit 1); \
	fi
	@echo ""
	@echo "2️⃣ Running ruff linter..."
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		ruff check $(MCP_DIRS) || (echo "❌ Lint check failed. Run 'make fix' to auto-fix." && exit 1); \
	fi
	@echo ""
	@echo "3️⃣ Running type checker (mypy)..."
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
	@echo ""
	@echo "✅ All checks completed successfully!"

# Auto-fix all issues (format + lint)
fix:
	@echo "🔧 Auto-fixing all code quality issues..."
	@echo ""
	@echo "1️⃣ Formatting code with black..."
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		black $(MCP_DIRS); \
	fi
	@echo ""
	@echo "2️⃣ Auto-fixing linting issues with ruff..."
	@if [ -z "$(MCP_DIRS)" ]; then \
		echo "⚠️  No MCP servers found"; \
	else \
		ruff check --fix $(MCP_DIRS); \
	fi
	@echo ""
	@echo "✅ Auto-fixes applied successfully!"

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
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✅ Clean complete!"

# ============================================================================
# Testing Commands
# ============================================================================

# Main test command - runs all tests with coverage
test:
	@echo "🧪 Running all tests with coverage report..."
	@echo ""
	pytest -v \
		--cov=database --cov=weather --cov=calculator \
		--cov-report=html --cov-report=term-missing
	@echo ""
	@echo "✅ Tests complete! Coverage report: htmlcov/index.html"

# Server-specific tests (for fast iteration during development)
test-calc:
	@echo "🧮 Testing calculator only (with coverage)..."
	pytest calculator/tests/ tests/test_e2e_calculator.py -v \
		--cov=calculator --cov-report=term-missing

test-weather:
	@echo "🌤️  Testing weather only (with coverage)..."
	APP_ENV=test pytest weather/tests/ tests/test_e2e_weather.py -v \
		--cov=weather --cov-report=term-missing

test-db:
	@echo "🗄️  Testing database only (with coverage)..."
	pytest database/tests/ tests/test_e2e_database.py -v \
		--cov=database --cov-report=term-missing

# ============================================================================
# Run MCP Servers
# ============================================================================

run-database:
	@echo "🚀 Starting database MCP server..."
	python -m database

run-weather:
	@echo "🌤️  Starting weather MCP server..."
	python -m weather

run-calculator:
	@echo "🧮 Starting calculator MCP server..."
	python -m calculator


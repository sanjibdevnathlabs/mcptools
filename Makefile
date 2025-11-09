.PHONY: help install check fix clean test test-calc test-weather test-db run-database run-weather run-calculator \
	docker-build-base docker-build-calculator docker-build-database docker-build-weather docker-build-all \
	docker-compose-up-calculator docker-compose-up-database docker-compose-up-weather \
	docker-compose-down-calculator docker-compose-down-database docker-compose-down-weather docker-compose-down-all \
	docker-push-base docker-push-calculator docker-push-database docker-push-weather docker-push-all

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
	@echo "🐳 Docker Build:"
	@echo "  make docker-build-base       - Build shared base image"
	@echo "  make docker-build-calculator - Build calculator image"
	@echo "  make docker-build-database   - Build database image"
	@echo "  make docker-build-weather    - Build weather image"
	@echo "  make docker-build-all        - Build all images (auto-discovered)"
	@echo ""
	@echo "🐳 Docker Compose (Local Dev):"
	@echo "  make docker-compose-up-calculator   - Start calculator services"
	@echo "  make docker-compose-up-database     - Start database + MySQL"
	@echo "  make docker-compose-up-weather      - Start weather services"
	@echo "  make docker-compose-down-calculator - Stop calculator services"
	@echo "  make docker-compose-down-database   - Stop database services"
	@echo "  make docker-compose-down-weather    - Stop weather services"
	@echo "  make docker-compose-down-all        - Stop all services"
	@echo ""
	@echo "📤 Docker Push (CI/CD):"
	@echo "  make docker-push-all         - Push all images to Docker Hub"
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
	find . -type f -name ".coverage.*" -delete
	@echo "✅ Clean complete!"

# ============================================================================
# Testing Commands
# ============================================================================

# Main test command - runs all tests with coverage (parallelized)
test:
	@echo "🧪 Running all tests with coverage report (parallelized)..."
	@echo ""
	pytest -v -n auto \
		--cov=database --cov=weather --cov=calculator \
		--cov-report=html --cov-report=term-missing
	@find . -type f -name ".coverage.*" -delete 2>/dev/null || true
	@echo ""
	@echo "✅ Tests complete! Coverage report: htmlcov/index.html"

# Server-specific tests (for fast iteration during development)
test-calc:
	@echo "🧮 Testing calculator only (with coverage and parallelization)..."
	pytest calculator/tests/ tests/test_e2e_calculator.py -v -n auto \
		--cov=calculator --cov-report=term-missing
	@find . -type f -name ".coverage.*" -delete 2>/dev/null || true

test-weather:
	@echo "🌤️  Testing weather only (with coverage and parallelization)..."
	APP_ENV=test pytest weather/tests/ tests/test_e2e_weather.py -v -n auto \
		--cov=weather --cov-report=term-missing
	@find . -type f -name ".coverage.*" -delete 2>/dev/null || true

test-db:
	@echo "🗄️  Testing database only (with coverage and parallelization)..."
	APP_ENV=test pytest database/tests/ tests/test_e2e_database.py -v -n auto \
		--cov=database --cov-report=term-missing
	@find . -type f -name ".coverage.*" -delete 2>/dev/null || true

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

# ============================================================================
# Docker Commands
# ============================================================================

# Auto-discover MCPs with docker/ folders
MCPS := $(shell .github/scripts/detect-mcps.sh space)

# Docker image settings
DOCKER_USER ?= sanjibdevnath
BASE_TAG ?= local-dev
VERSION ?= latest

# Build base image (shared dependencies)
docker-build-base:
	@echo "🏗️  Building base image with all shared dependencies..."
	docker build -f shared/docker/Dockerfile.base \
		-t $(DOCKER_USER)/mcp-base:$(BASE_TAG) \
		-t $(DOCKER_USER)/mcp-base:latest \
		.
	@echo "✅ Base image built: $(DOCKER_USER)/mcp-base:$(BASE_TAG)"

# Build individual MCP images
docker-build-calculator: docker-build-base
	@echo "🧮 Building calculator MCP image..."
	docker build -f calculator/docker/Dockerfile \
		--build-arg BASE_TAG=$(BASE_TAG) \
		-t $(DOCKER_USER)/mcp-calculator:$(VERSION) \
		-t $(DOCKER_USER)/mcp-calculator:latest \
		.
	@echo "✅ Calculator image built!"

docker-build-database: docker-build-base
	@echo "🗄️  Building database MCP image..."
	docker build -f database/docker/Dockerfile \
		--build-arg BASE_TAG=$(BASE_TAG) \
		-t $(DOCKER_USER)/mcp-database:$(VERSION) \
		-t $(DOCKER_USER)/mcp-database:latest \
		.
	@echo "✅ Database image built!"

docker-build-weather: docker-build-base
	@echo "🌤️  Building weather MCP image..."
	docker build -f weather/docker/Dockerfile \
		--build-arg BASE_TAG=$(BASE_TAG) \
		-t $(DOCKER_USER)/mcp-weather:$(VERSION) \
		-t $(DOCKER_USER)/mcp-weather:latest \
		.
	@echo "✅ Weather image built!"

# Build all images (auto-discovered)
docker-build-all: docker-build-base
	@echo "🏗️  Building all MCP images..."
	@for mcp in $(MCPS); do \
		echo ""; \
		echo "Building $$mcp MCP..."; \
		docker build -f $$mcp/docker/Dockerfile \
			--build-arg BASE_TAG=$(BASE_TAG) \
			-t $(DOCKER_USER)/mcp-$$mcp:$(VERSION) \
			-t $(DOCKER_USER)/mcp-$$mcp:latest \
			.; \
	done
	@echo ""
	@echo "✅ All images built successfully!"
	@echo "📦 Built images:"
	@docker images | grep "mcp-"

# ============================================================================
# Docker Compose Commands (Local Development)
# ============================================================================

docker-compose-up-calculator:
	@echo "🧮 Starting calculator services (will rebuild if needed)..."
	cd calculator/deployment/local && docker-compose up -d --build
	@echo "✅ Calculator services started!"
	@echo "   - SSE:    http://localhost:8080"
	@echo "   - HTTP:   http://localhost:8081/mcp"
	@echo "   - Health: http://localhost:9090/health"
	@echo "   - Logs:   docker logs -f calculator"

docker-compose-up-database:
	@echo "🗄️  Starting database services (includes MySQL, will rebuild if needed)..."
	cd database/deployment/local && docker-compose up -d --build
	@echo "✅ Database services started!"
	@echo "   - MySQL: localhost:3306 (root/testpassword)"
	@echo "   - SSE:   http://localhost:8086 (docker-compose -f database/deployment/local/docker-compose.yml logs -f database-sse)"
	@echo "   - HTTP:  http://localhost:8087 (docker-compose -f database/deployment/local/docker-compose.yml logs -f database-http)"

docker-compose-up-weather:
	@echo "🌤️  Starting weather services (will rebuild if needed)..."
	cd weather/deployment/local && docker-compose up -d --build
	@echo "✅ Weather services started!"
	@echo "   - SSE:   http://localhost:8082 (docker-compose -f weather/deployment/local/docker-compose.yml logs -f weather-sse)"
	@echo "   - HTTP:  http://localhost:8083 (docker-compose -f weather/deployment/local/docker-compose.yml logs -f weather-http)"

docker-compose-down-calculator:
	@echo "🛑 Stopping calculator services..."
	cd calculator/deployment/local && docker-compose down
	@echo "✅ Calculator services stopped!"

docker-compose-down-database:
	@echo "🛑 Stopping database services..."
	cd database/deployment/local && docker-compose down
	@echo "✅ Database services stopped!"

docker-compose-down-weather:
	@echo "🛑 Stopping weather services..."
	cd weather/deployment/local && docker-compose down
	@echo "✅ Weather services stopped!"

docker-compose-down-all:
	@echo "🛑 Stopping all Docker Compose services..."
	@for mcp in $(MCPS); do \
		if [ -f $$mcp/deployment/local/docker-compose.yml ]; then \
			echo "Stopping $$mcp services..."; \
			cd $$mcp/deployment/local && docker-compose down && cd ../../..; \
		fi; \
	done
	@echo "✅ All services stopped!"

# ============================================================================
# Docker Push Commands (CI/CD)
# ============================================================================

docker-push-base:
	@echo "📤 Pushing base image to Docker Hub..."
	docker push $(DOCKER_USER)/mcp-base:$(VERSION)
	docker push $(DOCKER_USER)/mcp-base:latest
	@echo "✅ Base image pushed!"

docker-push-calculator:
	@echo "📤 Pushing calculator image to Docker Hub..."
	docker push $(DOCKER_USER)/mcp-calculator:$(VERSION)
	docker push $(DOCKER_USER)/mcp-calculator:latest
	@echo "✅ Calculator image pushed!"

docker-push-database:
	@echo "📤 Pushing database image to Docker Hub..."
	docker push $(DOCKER_USER)/mcp-database:$(VERSION)
	docker push $(DOCKER_USER)/mcp-database:latest
	@echo "✅ Database image pushed!"

docker-push-weather:
	@echo "📤 Pushing weather image to Docker Hub..."
	docker push $(DOCKER_USER)/mcp-weather:$(VERSION)
	docker push $(DOCKER_USER)/mcp-weather:latest
	@echo "✅ Weather image pushed!"

docker-push-all: docker-push-base
	@echo "📤 Pushing all MCP images to Docker Hub..."
	@for mcp in $(MCPS); do \
		echo "Pushing $$mcp..."; \
		docker push $(DOCKER_USER)/mcp-$$mcp:$(VERSION); \
		docker push $(DOCKER_USER)/mcp-$$mcp:latest; \
	done
	@echo "✅ All images pushed successfully!"


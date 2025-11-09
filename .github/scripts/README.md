# GitHub Scripts

Automation scripts for CI/CD and development workflows.

## 📜 detect-mcps.sh

Auto-discovery script that finds all MCPs in the repository.

### Usage

```bash
# JSON format (for GitHub Actions matrix)
./.github/scripts/detect-mcps.sh json
# Output: {"mcp":["calculator","database","weather"]}

# Space-separated (for bash loops)
./.github/scripts/detect-mcps.sh space
# Output: calculator database weather

# Newline-separated
./.github/scripts/detect-mcps.sh newline
# Output: calculator
#         database
#         weather

# Count only
./.github/scripts/detect-mcps.sh count
# Output: 3
```

### How It Works

1. Scans repository for directories containing `docker/` subfolder
2. Excludes `shared/`, hidden directories, and common build directories
3. Returns sorted, unique list of MCP names

### Adding New MCPs

When you add a new MCP:
1. Create `new-mcp/docker/Dockerfile`
2. The script automatically detects it
3. CI/CD workflows automatically build it
4. No code changes needed! ✅

### Use in GitHub Actions

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      mcps: ${{ steps.detect.outputs.mcps }}
    steps:
      - uses: actions/checkout@v4
      - id: detect
        run: |
          MCPS=$(.github/scripts/detect-mcps.sh json)
          echo "mcps=$MCPS" >> $GITHUB_OUTPUT

  build:
    needs: detect
    strategy:
      matrix:
        mcp: ${{ fromJson(needs.detect.outputs.mcps) }}
    runs-on: ubuntu-latest
    steps:
      - name: Build ${{ matrix.mcp }}
        run: docker build -f ${{ matrix.mcp }}/docker/Dockerfile .
```

### Use in Makefile

```makefile
MCPS := $(shell .github/scripts/detect-mcps.sh space)

docker-build-all:
	@for mcp in $(MCPS); do \
		echo "Building $$mcp..."; \
		docker build -f $$mcp/docker/Dockerfile -t mcp-$$mcp:local .; \
	done
```


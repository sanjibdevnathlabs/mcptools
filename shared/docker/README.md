# Shared Base Docker Image

This directory contains the base Docker image that all MCP servers inherit from.

## 📦 What's Included

- **Python 3.13-slim** - Base Python runtime
- **All shared dependencies** - From `requirements.txt` and `requirements-test.txt`
- **System packages** - gcc, g++, make, curl, git
- **Non-root user** - `appuser` (UID 1000) for security
- **Optimized** - Minimal layers, no cache

## 🏗️ Image Tagging

### Pull Requests
```bash
sanjibdevnath/mcp-base:br-abc123def45  # Branch hash (12 chars)
```
All commits in the same PR reuse this image tag.

### Master Branch
```bash
sanjibdevnath/mcp-base:a1b2c3d4...     # Full commit SHA (40 chars)
sanjibdevnath/mcp-base:latest          # Rolling latest
```

## 🔨 Building Locally

```bash
# From repo root
docker build -f shared/docker/Dockerfile.base -t mcp-base:local-dev .

# Or using Make
make docker-build-base
```

## 📊 Image Size

- **Base image**: ~400-500MB (with all dependencies)
- **Per-MCP images**: ~50-100MB each (only code, inherits from base)

## 🔄 When to Rebuild

The base image is rebuilt when:
- `requirements.txt` changes
- `requirements-test.txt` changes
- `Dockerfile.base` changes

CI/CD automatically detects these changes and rebuilds.

## 🎯 Used By

All MCP-specific Dockerfiles inherit from this base:
- `calculator/docker/Dockerfile`
- `database/docker/Dockerfile`
- `weather/docker/Dockerfile`
- Any future MCPs...


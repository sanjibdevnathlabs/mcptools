# GitHub Secrets Setup

This document explains how to set up required GitHub secrets for the CI/CD pipeline.

## 📋 Required Secrets

The CI/CD pipeline requires the following secrets:

| Secret Name | Description | Required For |
|-------------|-------------|--------------|
| `DOCKERHUB_USERNAME` | Docker Hub username | ✅ Building & pushing images |
| `DOCKERHUB_TOKEN` | Docker Hub access token | ✅ Building & pushing images |
| `CODECOV_TOKEN` | Codecov upload token | ⚪ Code coverage reporting (optional) |

---

## 🔧 Setup Methods

### Method 1: Using GitHub CLI (Recommended)

```bash
# 1. Install GitHub CLI (if not already installed)
# macOS: brew install gh
# Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
# Windows: https://github.com/cli/cli/releases

# 2. Authenticate with GitHub
gh auth login

# 3. Set secrets for mcptools repository
gh secret set DOCKERHUB_USERNAME --body "your_dockerhub_username" --repo sanjibdevnathlabs/mcptools
gh secret set DOCKERHUB_TOKEN --body "your_dockerhub_token" --repo sanjibdevnathlabs/mcptools

# Optional: Set Codecov token
gh secret set CODECOV_TOKEN --body "your_codecov_token" --repo sanjibdevnathlabs/mcptools
```

### Method 2: Via GitHub Web UI

1. **Navigate to repository settings:**
   ```
   https://github.com/sanjibdevnathlabs/mcptools/settings/secrets/actions
   ```

2. **Click "New repository secret"**

3. **Add each secret:**
   - Name: `DOCKERHUB_USERNAME`
   - Value: Your Docker Hub username
   - Click "Add secret"

4. **Repeat for other secrets**

---

## 🐳 Docker Hub Setup

### Step 1: Create Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Click on your username (top right) → "Account Settings"
3. Navigate to "Security" → "Personal Access Tokens"
4. Click "New Access Token"
5. **Access Token Description**: `GitHub Actions - MCPTools`
6. **Access permissions**: `Read, Write, Delete`
7. Click "Generate"
8. **⚠️ Copy the token immediately** (it won't be shown again!)

### Step 2: Verify Docker Hub Username

```bash
# Your Docker Hub username (case-sensitive)
# Example: sanjibdevnath
```

Make sure this matches exactly what's shown in Docker Hub (case-sensitive).

---

## 📊 Codecov Setup (Optional)

### Step 1: Sign up for Codecov

1. Visit [Codecov](https://codecov.io/)
2. Sign in with GitHub
3. Authorize Codecov to access your repositories

### Step 2: Get Upload Token

1. Navigate to your repository on Codecov:
   ```
   https://codecov.io/gh/sanjibdevnathlabs/mcptools
   ```

2. Go to "Settings" → "General"
3. Copy the "Upload Token"
4. Add as `CODECOV_TOKEN` secret in GitHub

**Note**: Codecov is **optional**. If not configured, the CI workflow will continue without code coverage reporting.

---

## ✅ Verification

### Verify Secrets Are Set

```bash
# List secrets (values are hidden)
gh secret list --repo sanjibdevnathlabs/mcptools
```

Expected output:
```
CODECOV_TOKEN       Updated YYYY-MM-DD
DOCKERHUB_TOKEN     Updated YYYY-MM-DD
DOCKERHUB_USERNAME  Updated YYYY-MM-DD
```

### Test CI Pipeline

1. **Push to a feature branch:**
   ```bash
   git checkout -b test/ci-pipeline
   git push origin test/ci-pipeline
   ```

2. **Create a Pull Request**

3. **Check GitHub Actions:**
   ```
   https://github.com/sanjibdevnathlabs/mcptools/actions
   ```

4. **Expected behavior:**
   - ✅ Auto-discover MCPs (calculator, database, weather)
   - ✅ Detect file changes
   - ✅ Build base image (if requirements changed)
   - ✅ Run linters and security scans
   - ✅ Run tests for each MCP in parallel
   - ⚪ Build MCP images (only on push to `main`)

---

## 🔒 Security Best Practices

### 1. Access Token Permissions

**Docker Hub Token:**
- ✅ Use "Read, Write, Delete" for full CI/CD
- ❌ Don't use account password (use token instead)
- 🔄 Rotate tokens every 90 days

### 2. Secret Rotation

```bash
# Rotate Docker Hub token
# 1. Generate new token in Docker Hub
# 2. Update GitHub secret
gh secret set DOCKERHUB_TOKEN --body "new_token_here" --repo sanjibdevnathlabs/mcptools

# 3. Verify old token is revoked in Docker Hub
```

### 3. Audit Secret Usage

```bash
# View secret usage in workflow runs
gh run list --repo sanjibdevnathlabs/mcptools
gh run view RUN_ID --repo sanjibdevnathlabs/mcptools
```

---

## 🚨 Troubleshooting

### Issue: "Error: unauthorized: incorrect username or password"

**Cause**: Invalid Docker Hub credentials

**Solution**:
1. Verify `DOCKERHUB_USERNAME` is correct (case-sensitive)
2. Regenerate `DOCKERHUB_TOKEN` from Docker Hub
3. Update GitHub secret with new token
4. Ensure token has "Read, Write" permissions

### Issue: "Error: denied: requested access to the resource is denied"

**Cause**: Token doesn't have write permissions

**Solution**:
1. Go to Docker Hub → Account Settings → Security
2. Delete old token
3. Generate new token with "Read, Write, Delete" permissions
4. Update GitHub secret

### Issue: Codecov upload fails

**Cause**: Missing or invalid `CODECOV_TOKEN`

**Solution**:
- Coverage upload is **optional** - workflow will continue
- To fix: Get valid token from Codecov dashboard
- Or: Remove Codecov steps from workflow (set `continue-on-error: true`)

### Issue: "Resource not accessible by integration"

**Cause**: Workflow doesn't have required permissions

**Solution**:
1. Go to repository Settings → Actions → General
2. Set "Workflow permissions" to "Read and write permissions"
3. Check "Allow GitHub Actions to create and approve pull requests"

---

## 📝 Secret Updates Log

Track when secrets were last updated:

| Secret | Updated | By | Notes |
|--------|---------|-----|-------|
| `DOCKERHUB_TOKEN` | YYYY-MM-DD | @username | Initial setup |
| `DOCKERHUB_USERNAME` | YYYY-MM-DD | @username | Initial setup |
| `CODECOV_TOKEN` | YYYY-MM-DD | @username | Initial setup |

---

## 🔗 Useful Links

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Docker Hub Access Tokens](https://docs.docker.com/docker-hub/access-tokens/)
- [Codecov Documentation](https://docs.codecov.io/)
- [GitHub CLI](https://cli.github.com/)

---

**Need Help?** Contact the DevOps team or repository maintainers.


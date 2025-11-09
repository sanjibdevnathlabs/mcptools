#!/bin/bash
# Auto-discover MCPs by scanning for docker/Dockerfile pattern
# Returns JSON array of MCP names for GitHub Actions matrix

set -euo pipefail

echo "🔍 Auto-discovering MCPs..."

# Find all directories with docker/Dockerfile (excluding shared/)
mcps=()
for dockerfile in */docker/Dockerfile; do
    if [ -f "$dockerfile" ]; then
        # Extract MCP name (directory before /docker/Dockerfile)
        mcp=$(dirname $(dirname "$dockerfile"))
        
        # Skip shared directory (it's the base image)
        if [ "$mcp" != "shared" ]; then
            mcps+=("$mcp")
            echo "  ✅ Found MCP: $mcp"
        fi
    fi
done

# Check if any MCPs were found
if [ ${#mcps[@]} -eq 0 ]; then
    echo "❌ Error: No MCPs discovered!"
    echo "   Each MCP should have: <mcp>/docker/Dockerfile"
    exit 1
fi

# Convert to JSON array for GitHub Actions
json_array=$(printf '%s\n' "${mcps[@]}" | jq -R -s -c 'split("\n") | map(select(length > 0))')

echo ""
echo "📋 Discovered ${#mcps[@]} MCP(s):"
echo "$json_array" | jq -r '.[]' | while read mcp; do
    echo "  - $mcp"
done

# Output for GitHub Actions
echo ""
echo "mcps=$json_array" >> $GITHUB_OUTPUT

# Also export for local testing
echo "export DISCOVERED_MCPS='$json_array'"

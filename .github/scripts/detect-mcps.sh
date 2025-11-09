#!/bin/bash
# Auto-discovery script for MCPs in the repository
# Detects all MCP directories by finding docker/ folders
# Usage: ./detect-mcps.sh [output_format]
#   output_format: json (default), space, newline, array

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_FORMAT="${1:-json}"

# Find all directories containing a docker/ subdirectory
# Exclude shared/ and hidden directories
find_mcps() {
    find "$REPO_ROOT" -type d -name "docker" \
        ! -path "*/shared/*" \
        ! -path "*/.*" \
        ! -path "*/node_modules/*" \
        ! -path "*/venv/*" \
        -print0 | while IFS= read -r -d '' docker_dir; do
        # Get parent directory name (the MCP name)
        mcp_name="$(basename "$(dirname "$docker_dir")")"
        echo "$mcp_name"
    done | sort -u
}

# Get list of MCPs
MCPS=()
while IFS= read -r mcp; do
    MCPS+=("$mcp")
done < <(find_mcps)

# Output based on format
case "$OUTPUT_FORMAT" in
    json)
        # JSON array format for GitHub Actions matrix
        printf '{"mcp":['
        first=true
        for mcp in "${MCPS[@]}"; do
            if [ "$first" = true ]; then
                first=false
            else
                printf ','
            fi
            printf '"%s"' "$mcp"
        done
        printf ']}'
        ;;
    
    space)
        # Space-separated for bash loops
        printf '%s' "${MCPS[*]}"
        ;;
    
    newline)
        # Newline-separated for bash loops
        printf '%s\n' "${MCPS[@]}"
        ;;
    
    array)
        # Bash array format
        printf '(%s)' "${MCPS[*]}"
        ;;
    
    count)
        # Just the count
        printf '%d' "${#MCPS[@]}"
        ;;
    
    *)
        echo "Error: Unknown output format: $OUTPUT_FORMAT" >&2
        echo "Supported formats: json, space, newline, array, count" >&2
        exit 1
        ;;
esac


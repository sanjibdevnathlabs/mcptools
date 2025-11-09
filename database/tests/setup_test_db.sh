#!/bin/bash
# Setup Test Database for Integration Tests
# This script initializes the test database with schema and test data

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 Setting up test database...${NC}"

# Get database credentials from environment or use defaults
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-root}
DB_PASSWORD=${DB_PASSWORD:-root}

# Path to SQL init script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SQL="$SCRIPT_DIR/fixtures/init_test_db.sql"

# Check if MySQL is available
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}❌ Error: mysql client not found${NC}"
    echo "Please install MySQL client or ensure it's in PATH"
    exit 1
fi

# Check if init script exists
if [ ! -f "$INIT_SQL" ]; then
    echo -e "${RED}❌ Error: Init script not found: $INIT_SQL${NC}"
    exit 1
fi

# Try to connect and run init script
echo "📡 Connecting to MySQL at $DB_HOST:$DB_PORT..."
if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" < "$INIT_SQL" 2>&1 | grep -v "Warning"; then
    echo -e "${GREEN}✅ Test database initialized successfully!${NC}"
    exit 0
else
    echo -e "${RED}❌ Failed to initialize test database${NC}"
    echo "Please check:"
    echo "  - MySQL is running"
    echo "  - Credentials are correct (DB_HOST=$DB_HOST, DB_USER=$DB_USER)"
    echo "  - User has sufficient privileges"
    exit 1
fi


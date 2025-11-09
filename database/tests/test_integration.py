"""Integration tests for database MCP with real MySQL"""

import os

# Set test environment before imports
os.environ["APP_ENV"] = "test"
os.environ["TEST_DB_DATABASE"] = "test_mcp_db"
os.environ["TEST_DB_USER"] = "mcp_test"
os.environ["TEST_DB_PASSWORD"] = "test123"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from database.src.database_manager import DatabaseManager  # noqa: E402


@pytest_asyncio.fixture
async def db_manager():
    """Create database manager for integration tests"""
    manager = DatabaseManager()
    await manager.initialize_pool()
    yield manager
    await manager.close_pool()


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations with real MySQL"""

    def test_connect_to_database(self, db_manager):
        """Test successful database connection"""
        assert db_manager is not None
        # Connection pool should be initialized
        assert hasattr(db_manager, "pool")
        assert db_manager.pool is not None

    @pytest.mark.asyncio
    async def test_double_initialize_pool(self):
        """Test that double initialization is handled gracefully"""
        manager = DatabaseManager()
        await manager.initialize_pool()
        # Try to initialize again - should log warning but not fail
        await manager.initialize_pool()
        assert manager.pool is not None
        await manager.close_pool()

    @pytest.mark.asyncio
    async def test_close_pool_without_initialization(self):
        """Test closing pool when not initialized"""
        manager = DatabaseManager()
        # Should not raise error
        await manager.close_pool()

    @pytest.mark.asyncio
    async def test_execute_query_with_lazy_initialization(self):
        """Test that pool is automatically initialized on first query (lazy initialization)"""
        manager = DatabaseManager()
        # Pool should not be initialized yet
        assert manager.pool is None

        # Execute a query - should automatically initialize pool
        result = await manager.execute_query("SELECT 1 as value")

        # Pool should now be initialized
        assert manager.pool is not None
        assert result["success"] is True

        # Clean up
        await manager.close_pool()

    @pytest.mark.asyncio
    async def test_execute_query_too_long(self, db_manager):
        """Test executing query that exceeds max length"""
        # Create a very long query that exceeds 1MB
        long_query = "SELECT 1 " + ("x" * 1100000)  # 1.1MB query
        result = await db_manager.execute_query(long_query)
        assert result["success"] is False
        assert "Query length exceeds maximum" in result["error"]
        assert result["error_code"] == "QUERY_TOO_LONG"

    @pytest.mark.asyncio
    async def test_execute_invalid_sql(self, db_manager):
        """Test executing invalid SQL"""
        result = await db_manager.execute_query("INVALID SQL SYNTAX")
        assert result["success"] is False
        assert "error" in result
        assert "error_code" in result

    @pytest.mark.asyncio
    async def test_execute_select_query(self, db_manager):
        """Test executing SELECT query"""
        result = await db_manager.execute_query("SELECT 1 as test")
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert len(data) > 0
        assert data[0]["test"] == 1

    @pytest.mark.asyncio
    async def test_get_database_list(self, db_manager):
        """Test listing databases"""
        result = await db_manager.execute_query("SHOW DATABASES")
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert len(data) > 0
        # Should include our test database
        db_names = [row["Database"] for row in data]
        assert "test_mcp_db" in db_names

    @pytest.mark.asyncio
    async def test_get_tables_list(self, db_manager):
        """Test listing tables in test database"""
        result = await db_manager.execute_query("SHOW TABLES FROM test_mcp_db")
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert len(data) > 0
        # Should include our users table
        table_names = [list(row.values())[0] for row in data]
        assert "users" in table_names

    @pytest.mark.asyncio
    async def test_query_users_table(self, db_manager):
        """Test querying users table"""
        result = await db_manager.execute_query(
            "SELECT id, name, email, status FROM test_mcp_db.users ORDER BY id"
        )
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert len(data) >= 3  # We inserted 3 users

        # Verify data structure
        assert "id" in data[0]
        assert "name" in data[0]
        assert "email" in data[0]
        assert "status" in data[0]

    @pytest.mark.asyncio
    async def test_query_with_where_clause(self, db_manager):
        """Test query with WHERE clause"""
        result = await db_manager.execute_query(
            "SELECT name, status FROM test_mcp_db.users WHERE status = 'active'"
        )
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        # All returned users should be active
        for row in data:
            assert row["status"] == "active"

    @pytest.mark.asyncio
    async def test_query_with_limit(self, db_manager):
        """Test query with LIMIT clause"""
        result = await db_manager.execute_query(
            "SELECT id, name FROM test_mcp_db.users LIMIT 2"
        )
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_describe_table(self, db_manager):
        """Test DESCRIBE table command"""
        result = await db_manager.execute_query("DESCRIBE test_mcp_db.users")
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert len(data) > 0

        # Should include our columns
        fields = [row["Field"] for row in data]
        assert "id" in fields
        assert "name" in fields
        assert "email" in fields
        assert "status" in fields

    @pytest.mark.asyncio
    async def test_show_table_status(self, db_manager):
        """Test SHOW TABLE STATUS command"""
        result = await db_manager.execute_query(
            "SHOW TABLE STATUS FROM test_mcp_db LIKE 'users'"
        )
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert len(data) > 0
        assert data[0]["Name"] == "users"

    @pytest.mark.asyncio
    async def test_query_with_count(self, db_manager):
        """Test query with COUNT aggregate function"""
        result = await db_manager.execute_query(
            "SELECT COUNT(*) as total FROM test_mcp_db.users"
        )
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert data[0]["total"] >= 3

    @pytest.mark.asyncio
    async def test_query_with_join_preparation(self, db_manager):
        """Test table structure that could be used for joins"""
        # Just verify we can query table structure for potential joins
        result = await db_manager.execute_query(
            "SELECT COLUMN_NAME, COLUMN_KEY "
            "FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = 'test_mcp_db' AND TABLE_NAME = 'users'"
        )
        assert result is not None
        assert result["success"] is True
        data = result["data"]
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_connection_recovery(self, db_manager):
        """Test that database manager can handle reconnection"""
        # Execute a simple query to ensure connection is established
        result1 = await db_manager.execute_query("SELECT 1 as value")
        assert result1 is not None
        assert result1["success"] is True

        # Execute another query (should reuse connection from pool)
        result2 = await db_manager.execute_query("SELECT 2 as value")
        assert result2 is not None
        assert result2["success"] is True
        assert result2["data"][0]["value"] == 2

    # ==============================================================================
    # Schema Manager Tests
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_schema_manager_get_databases(self, db_manager):
        """Test SchemaManager.get_databases()"""
        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)
        databases = await schema_manager.get_databases()

        assert databases is not None
        assert isinstance(databases, list)
        assert len(databases) > 0

        # Should contain test database
        db_names = [db.name for db in databases]
        assert "test_mcp_db" in db_names

        # Check DatabaseInfo structure
        test_db = next(db for db in databases if db.name == "test_mcp_db")
        assert hasattr(test_db, "name")
        assert hasattr(test_db, "character_set")
        assert hasattr(test_db, "collation")

    @pytest.mark.asyncio
    async def test_schema_manager_get_tables(self, db_manager):
        """Test SchemaManager.get_tables()"""
        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)
        tables = await schema_manager.get_tables("test_mcp_db")

        assert tables is not None
        assert isinstance(tables, list)
        assert len(tables) > 0

        # Should contain users table
        table_names = [t.name for t in tables]
        assert "users" in table_names

        # Check TableInfo structure
        users_table = next(t for t in tables if t.name == "users")
        assert hasattr(users_table, "name")
        assert hasattr(users_table, "table_type")
        assert hasattr(users_table, "table_rows")

    @pytest.mark.asyncio
    async def test_schema_manager_get_table_details(self, db_manager):
        """Test SchemaManager.get_table_details()"""
        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)
        details = await schema_manager.get_table_details("users", "test_mcp_db")

        assert details is not None
        assert details.name == "users"
        assert details.database_name == "test_mcp_db"

        # Check columns
        assert len(details.columns) > 0
        column_names = [c.name for c in details.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "email" in column_names
        assert "status" in column_names

        # Check column details
        id_column = next(c for c in details.columns if c.name == "id")
        assert id_column.is_primary_key is True

    @pytest.mark.asyncio
    async def test_schema_manager_create_snapshot(self, db_manager):
        """Test SchemaManager.create_schema_snapshot()"""
        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)
        snapshot = await schema_manager.create_schema_snapshot(["test_mcp_db"])

        assert snapshot is not None
        assert hasattr(snapshot, "timestamp")
        assert hasattr(snapshot, "databases")
        assert len(snapshot.databases) > 0
        assert "test_mcp_db" in snapshot.databases

        # Check tables in snapshot
        assert hasattr(snapshot, "tables")
        assert len(snapshot.tables) > 0
        # Tables are keyed as "database.table"
        table_keys = list(snapshot.tables.keys())
        assert any("users" in key for key in table_keys)

    @pytest.mark.asyncio
    async def test_schema_manager_analyze_schema(self, db_manager):
        """Test SchemaManager.analyze_schema()"""
        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)
        analysis = await schema_manager.analyze_schema(["test_mcp_db"])

        assert analysis is not None
        assert isinstance(analysis, dict)

        # Check that analysis contains expected keys
        # (exact structure depends on SchemaAnalyzer implementation)
        assert "summary" in analysis or "databases" in analysis or len(analysis) > 0

    @pytest.mark.asyncio
    async def test_schema_manager_compare_schemas(self, db_manager):
        """Test SchemaManager.compare_schemas()"""
        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)

        # Create snapshot
        snapshot = await schema_manager.create_schema_snapshot(["test_mcp_db"])

        # Compare snapshot with itself (should have no differences)
        comparison = await schema_manager.compare_schemas(snapshot, snapshot)

        assert comparison is not None
        assert isinstance(comparison, dict)

        # Check that comparison result is a dict
        # (exact structure depends on SchemaComparator implementation)
        assert len(comparison) > 0

        # If changes_detected key exists, it should be False when comparing with itself
        if "changes_detected" in comparison:
            assert comparison["changes_detected"] is False

    @pytest.mark.asyncio
    async def test_schema_manager_export_json(self, db_manager):
        """Test SchemaManager.export_schema_snapshot() with JSON format"""
        import json

        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)

        # Create snapshot
        snapshot = await schema_manager.create_schema_snapshot(["test_mcp_db"])

        # Export as JSON
        json_export = schema_manager.export_schema_snapshot(
            snapshot, format_type="json"
        )

        assert json_export is not None
        assert isinstance(json_export, str)

        # Verify it's valid JSON
        parsed = json.loads(json_export)
        assert "schema_snapshot" in parsed
        snapshot_data = parsed["schema_snapshot"]
        assert "databases" in snapshot_data
        assert "test_mcp_db" in snapshot_data["databases"]

    @pytest.mark.asyncio
    async def test_schema_manager_export_sql(self, db_manager):
        """Test SchemaManager.export_schema_snapshot() with SQL format"""
        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)

        # Create snapshot
        snapshot = await schema_manager.create_schema_snapshot(["test_mcp_db"])

        # Export as SQL
        sql_export = schema_manager.export_schema_snapshot(snapshot, format_type="sql")

        assert sql_export is not None
        assert isinstance(sql_export, str)

        # Verify it contains SQL DDL statements
        assert "CREATE DATABASE" in sql_export or "CREATE TABLE" in sql_export
        assert "test_mcp_db" in sql_export

    @pytest.mark.asyncio
    async def test_schema_manager_export_default_format(self, db_manager):
        """Test SchemaManager.export_schema_snapshot() with default format"""
        from database.src.schema_manager import SchemaManager

        schema_manager = SchemaManager(db_manager)

        # Create snapshot
        snapshot = await schema_manager.create_schema_snapshot(["test_mcp_db"])

        # Export with default format (should be JSON)
        default_export = schema_manager.export_schema_snapshot(snapshot)

        assert default_export is not None
        assert isinstance(default_export, str)

    @pytest.mark.asyncio
    async def test_execute_query_with_max_rows(self, db_manager):
        """Test execute_query with max_rows limit"""
        import time

        # Use unique suffix to avoid duplicate key errors
        suffix = int(time.time() * 1000)

        # First, insert multiple rows
        await db_manager.execute_query(
            f"INSERT INTO users (name, email, status) VALUES "
            f"('User1', 'user1_{suffix}@test.com', 'active'), "
            f"('User2', 'user2_{suffix}@test.com', 'active'), "
            f"('User3', 'user3_{suffix}@test.com', 'active')"
        )

        # Query with max_rows limit of 2
        result = await db_manager.execute_query(
            "SELECT * FROM users WHERE status = 'active'", max_rows=2
        )

        assert result["success"] is True
        assert len(result["data"]) <= 2

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, db_manager):
        """Test execute_query with parameterized query"""
        import time

        # Use unique email to avoid duplicate key errors
        unique_email = f"param{int(time.time() * 1000)}@test.com"

        # Insert test data
        await db_manager.execute_query(
            f"INSERT INTO users (name, email, status) VALUES "
            f"('ParamUser', '{unique_email}', 'active')"
        )

        # Query with parameters
        result = await db_manager.execute_query(
            "SELECT * FROM users WHERE status = %s", params=["active"]
        )

        assert result["success"] is True
        assert len(result["data"]) > 0

    @pytest.mark.asyncio
    async def test_execute_query_fetch_results_false(self, db_manager):
        """Test execute_query with fetch_results=False"""
        import time

        # Use unique email to avoid duplicate key errors
        unique_email = f"nofetch{int(time.time() * 1000)}@test.com"
        result = await db_manager.execute_query(
            f"INSERT INTO users (name, email, status) VALUES ('NoFetch', '{unique_email}', 'active')",
            fetch_results=False,
        )

        assert result["success"] is True
        # Should have affected_rows instead of data
        assert "affected_rows" in result or "data" in result

    @pytest.mark.asyncio
    async def test_execute_query_update_operation(self, db_manager):
        """Test execute_query with UPDATE operation"""
        import time

        # Use unique email to avoid duplicate key errors
        unique_email = f"update{int(time.time() * 1000)}@test.com"

        # First insert a user
        await db_manager.execute_query(
            f"INSERT INTO users (name, email, status) VALUES ('UpdateMe', '{unique_email}', 'pending')"
        )

        # Update the user
        result = await db_manager.execute_query(
            f"UPDATE users SET status = 'active' WHERE email = '{unique_email}'"
        )

        assert result["success"] is True
        assert "affected_rows" in result or result.get("data") == []

    @pytest.mark.asyncio
    async def test_execute_query_delete_operation(self, db_manager):
        """Test execute_query with DELETE operation"""
        import time

        # Use unique email to avoid duplicate key errors
        unique_email = f"delete{int(time.time() * 1000)}@test.com"

        # First insert a user
        await db_manager.execute_query(
            f"INSERT INTO users (name, email, status) VALUES ('DeleteMe', '{unique_email}', 'active')"
        )

        # Delete the user
        result = await db_manager.execute_query(
            f"DELETE FROM users WHERE email = '{unique_email}'"
        )

        assert result["success"] is True
        assert "affected_rows" in result or result.get("data") == []

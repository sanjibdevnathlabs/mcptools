"""E2E tests for database MCP server across all protocols"""
import asyncio
import contextlib
import os
import signal
import subprocess
import sys
import time
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="class")
def event_loop():
    """Create an event loop for the test class"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


def find_free_port():
    """Find a free port for SSE/HTTP servers"""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

# ==============================================================================
# STDIO Protocol Tests
# ==============================================================================


@pytest_asyncio.fixture(scope="class")
async def database_stdio_client() -> AsyncGenerator[ClientSession, None]:
    """Fixture for database MCP client using STDIO protocol (shared across test class)"""
    # Configure environment for test
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["TEST_DB_DATABASE"] = "test_mcp_db"
    env["TEST_DB_USER"] = "mcp_test"
    env["TEST_DB_PASSWORD"] = "test123"
    env["TRANSPORT_MODE"] = "stdio"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "database"],
        env=env,
    )

    stdio_ctx = stdio_client(server_params)
    read, write = await stdio_ctx.__aenter__()

    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()

    await session.initialize()

    yield session

    # Cleanup
    with contextlib.suppress(Exception):
        await session_ctx.__aexit__(None, None, None)
    with contextlib.suppress(Exception):
        await stdio_ctx.__aexit__(None, None, None)

    await asyncio.sleep(0.1)


@pytest.mark.e2e
class TestDatabaseSTDIO:
    """E2E tests for database server using STDIO protocol"""

    @pytest.mark.asyncio
    async def test_stdio_list_tools(self, database_stdio_client):
        """Test listing available tools via STDIO"""
        result = await database_stdio_client.list_tools()

        assert len(result.tools) > 0, "Should have at least one tool"

        # Verify key tools exist
        tool_names = [tool.name for tool in result.tools]
        assert "execute_query" in tool_names

    @pytest.mark.asyncio
    async def test_stdio_execute_select_query(self, database_stdio_client):
        """Test executing SELECT query via STDIO"""
        result = await database_stdio_client.call_tool(
            "execute_query", {"sql": "SELECT 1 as test_value"}
        )

        assert len(result.content) > 0
        content_text = result.content[0].text
        assert "test_value" in content_text
        assert "1" in content_text

    @pytest.mark.asyncio
    async def test_stdio_show_databases(self, database_stdio_client):
        """Test SHOW DATABASES via STDIO"""
        result = await database_stdio_client.call_tool(
            "execute_query", {"sql": "SHOW DATABASES"}
        )

        assert len(result.content) > 0
        content_text = result.content[0].text
        assert "test_mcp_db" in content_text

    @pytest.mark.asyncio
    async def test_stdio_query_test_table(self, database_stdio_client):
        """Test querying test data via STDIO"""
        result = await database_stdio_client.call_tool(
            "execute_query",
            {"sql": "SELECT name, email FROM test_mcp_db.users WHERE status = 'active' LIMIT 2"},
        )

        assert len(result.content) > 0
        content_text = result.content[0].text
        # Should contain column names and data
        assert "name" in content_text or "email" in content_text

    @pytest.mark.asyncio
    async def test_stdio_invalid_query_handling(self, database_stdio_client):
        """Test invalid SQL query handling via STDIO"""
        result = await database_stdio_client.call_tool(
            "execute_query", {"sql": "SELECT * FROM nonexistent_table_xyz"}
        )

        assert len(result.content) > 0
        content_text = result.content[0].text.lower()
        # Should contain error message
        assert "error" in content_text or "not exist" in content_text or "doesn't exist" in content_text


    @pytest.mark.asyncio
    async def test_stdio_get_table_details(self, database_stdio_client):
        """Test get_table_details tool"""
        result = await database_stdio_client.call_tool("get_table_details", {
            "database": "test_mcp_db",
            "table": "users"
        })
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_health_check_tool(self, database_stdio_client):
        """Test health_check tool"""
        result = await database_stdio_client.call_tool("health_check", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_connection_stats(self, database_stdio_client):
        """Test connection_stats tool"""
        result = await database_stdio_client.call_tool("connection_stats", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_security_status(self, database_stdio_client):
        """Test security_status tool"""
        result = await database_stdio_client.call_tool("security_status", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_monitoring_status(self, database_stdio_client):
        """Test monitoring_status tool"""
        result = await database_stdio_client.call_tool("monitoring_status", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_get_databases_tool(self, database_stdio_client):
        """Test get_databases tool"""
        result = await database_stdio_client.call_tool("get_databases", {})
        assert len(result.content) > 0
        content = result.content[0].text
        assert "test_mcp_db" in content

    @pytest.mark.asyncio
    async def test_stdio_get_tables_tool(self, database_stdio_client):
        """Test get_tables tool"""
        result = await database_stdio_client.call_tool("get_tables", {"database": "test_mcp_db"})
        assert len(result.content) > 0
        content = result.content[0].text
        assert "users" in content

    @pytest.mark.asyncio
    async def test_stdio_schema_info(self, database_stdio_client):
        """Test schema_info tool"""
        result = await database_stdio_client.call_tool("schema_info", {"database": "test_mcp_db"})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_table_info(self, database_stdio_client):
        """Test table_info tool"""
        result = await database_stdio_client.call_tool("table_info", {
            "database": "test_mcp_db",
            "table": "users"
        })
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_performance_metrics(self, database_stdio_client):
        """Test performance_metrics tool"""
        result = await database_stdio_client.call_tool("performance_metrics", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_system_metrics(self, database_stdio_client):
        """Test system_metrics tool"""
        result = await database_stdio_client.call_tool("system_metrics", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_error_summary(self, database_stdio_client):
        """Test error_summary tool"""
        result = await database_stdio_client.call_tool("error_summary", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_explain_query(self, database_stdio_client):
        """Test explain_query tool"""
        result = await database_stdio_client.call_tool("explain_query", {
            "sql": "SELECT * FROM test_mcp_db.users WHERE status = 'active'"
        })
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_create_schema_snapshot(self, database_stdio_client):
        """Test create_schema_snapshot tool"""
        result = await database_stdio_client.call_tool("create_schema_snapshot", {
            "database": "test_mcp_db"
        })
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_export_schema(self, database_stdio_client):
        """Test export_schema tool"""
        result = await database_stdio_client.call_tool("export_schema", {
            "database": "test_mcp_db",
            "format": "json"
        })
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_analyze_schema(self, database_stdio_client):
        """Test analyze_schema tool"""
        result = await database_stdio_client.call_tool("analyze_schema", {
            "database": "test_mcp_db"
        })
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_export_metrics(self, database_stdio_client):
        """Test export_metrics tool"""
        result = await database_stdio_client.call_tool("export_metrics", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_error_handling_status(self, database_stdio_client):
        """Test error_handling_status tool"""
        result = await database_stdio_client.call_tool("error_handling_status", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_circuit_breaker_status(self, database_stdio_client):
        """Test circuit_breaker_status tool"""
        result = await database_stdio_client.call_tool("circuit_breaker_status", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_stdio_service_degradation_status(self, database_stdio_client):
        """Test service_degradation_status tool"""
        result = await database_stdio_client.call_tool("service_degradation_status", {})
        assert len(result.content) > 0


# ==============================================================================
# SSE Protocol Tests
# ==============================================================================


@pytest_asyncio.fixture(scope="class")
async def database_sse_server():
    """Fixture to start database server in SSE mode (shared across test class)"""
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/sse"

    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["TEST_DB_DATABASE"] = "test_mcp_db"
    env["TEST_DB_USER"] = "mcp_test"
    env["TEST_DB_PASSWORD"] = "test123"
    env["TRANSPORT_MODE"] = "sse"
    env["FASTMCP_HOST"] = "127.0.0.1"
    env["FASTMCP_PORT"] = str(port)

    process = subprocess.Popen(
        [sys.executable, "-m", "database", "--transport", "sse", "--host", "127.0.0.1", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
    )

    # Wait for server to start (check if port is listening)
    max_retries = 50
    server_ready = False

    for _ in range(max_retries):
        try:
            # Use socket check for SSE server
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                server_ready = True
                break
        except Exception:
            pass
        
        if process.poll() is not None:
            # Server crashed
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Database SSE server failed to start!\n"
                f"Exit code: {process.returncode}\n"
                f"STDOUT: {stdout.decode()}\n"
                f"STDERR: {stderr.decode()}"
            )
        time.sleep(0.1)

    if not server_ready:
        process.terminate()
        raise TimeoutError("Database SSE server failed to start in time")

    yield url

    # Cleanup
    try:
        if hasattr(os, "killpg"):
            with contextlib.suppress(ProcessLookupError):
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        else:
            process.terminate()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    finally:
        await asyncio.sleep(0.1)


@pytest_asyncio.fixture(scope="class")
async def database_sse_client(database_sse_server) -> AsyncGenerator[ClientSession, None]:
    """Fixture to create SSE client for database server (shared across test class)"""
    sse_ctx = sse_client(database_sse_server)
    read, write = await sse_ctx.__aenter__()

    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()

    await session.initialize()

    yield session

    with contextlib.suppress(Exception):
        await session_ctx.__aexit__(None, None, None)
    with contextlib.suppress(Exception):
        await sse_ctx.__aexit__(None, None, None)

    await asyncio.sleep(0.1)


@pytest.mark.e2e
class TestDatabaseSSE:
    """E2E tests for database server using SSE protocol"""

    @pytest.mark.asyncio
    async def test_sse_list_tools(self, database_sse_client):
        """Test listing tools via SSE"""
        result = await database_sse_client.list_tools()
        assert len(result.tools) > 0
        tool_names = [tool.name for tool in result.tools]
        assert "execute_query" in tool_names

    @pytest.mark.asyncio
    async def test_sse_execute_query(self, database_sse_client):
        """Test query execution via SSE"""
        result = await database_sse_client.call_tool(
            "execute_query", {"sql": "SELECT 1 as value"}
        )
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_sse_show_tables(self, database_sse_client):
        """Test SHOW TABLES via SSE"""
        result = await database_sse_client.call_tool(
            "execute_query", {"sql": "SHOW TABLES FROM test_mcp_db"}
        )
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_sse_security_status(self, database_sse_client):
        """Test security_status tool via SSE"""
        result = await database_sse_client.call_tool("security_status", {})
        assert len(result.content) > 0
        content_text = result.content[0].text.lower()
        assert "security" in content_text

    @pytest.mark.asyncio
    async def test_sse_sql_injection_detection(self, database_sse_client):
        """Test SQL injection detection via SSE"""
        # This query contains SQL injection patterns
        malicious_query = "SELECT * FROM users UNION SELECT 1,2,3--"
        result = await database_sse_client.call_tool("execute_query", {"sql": malicious_query})
        assert len(result.content) > 0
        content_text = result.content[0].text.lower()
        # Security system should detect and block/warn
        assert "error" in content_text or "blocked" in content_text or "not allowed" in content_text or "syntax" in content_text


# ==============================================================================
# HTTP Protocol Tests
# ==============================================================================


@pytest_asyncio.fixture(scope="class")
async def database_http_server():
    """Fixture to start database server in HTTP mode (shared across test class)"""
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["TEST_DB_DATABASE"] = "test_mcp_db"
    env["TEST_DB_USER"] = "mcp_test"
    env["TEST_DB_PASSWORD"] = "test123"
    env["TRANSPORT_MODE"] = "streamable-http"
    env["FASTMCP_HOST"] = "127.0.0.1"
    env["FASTMCP_PORT"] = str(port)

    process = subprocess.Popen(
        [sys.executable, "-m", "database", "--transport", "streamable-http", "--host", "127.0.0.1", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
    )

    # Wait for server to start (check if port is listening)
    max_retries = 50
    server_ready = False

    for _ in range(max_retries):
        try:
            # Use socket check for HTTP server
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                server_ready = True
                break
        except Exception:
            pass
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Database HTTP server failed to start!\n"
                f"stdout: {stdout.decode()}\nstderr: {stderr.decode()}"
            )
        
        await asyncio.sleep(0.1)

    if not server_ready:
        process.kill()
        stdout, stderr = process.communicate()
        raise TimeoutError(
            f"Database HTTP server failed to start within timeout!\n"
            f"stdout: {stdout.decode()}\nstderr: {stderr.decode()}"
        )

    yield url

    try:
        if hasattr(os, "killpg"):
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=5)
    except Exception:
        process.kill()
    
    await asyncio.sleep(0.1)


@pytest_asyncio.fixture(scope="class")
async def database_http_client(database_http_server):
    """Fixture to create HTTP client for database server (shared across test class)"""
    url = f"{database_http_server}/mcp"
    
    from mcp.client.streamable_http import streamablehttp_client
    from mcp import ClientSession
    
    http_ctx = streamablehttp_client(url)
    read, write, get_session_id = await http_ctx.__aenter__()
    
    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()
    
    await session.initialize()
    
    yield session
    
    with contextlib.suppress(Exception):
        await session_ctx.__aexit__(None, None, None)
    with contextlib.suppress(Exception):
        await http_ctx.__aexit__(None, None, None)
    
    await asyncio.sleep(0.1)


@pytest.mark.e2e
class TestDatabaseHTTP:
    """E2E tests for database server using HTTP protocol"""

    @pytest.mark.asyncio
    async def test_http_list_tools(self, database_http_client):
        """Test listing tools via HTTP"""
        result = await database_http_client.list_tools()
        assert len(result.tools) > 0
        tool_names = [tool.name for tool in result.tools]
        assert "execute_query" in tool_names
        assert len(tool_names) >= 21  # All tools registered

    @pytest.mark.asyncio
    async def test_http_execute_query(self, database_http_client):
        """Test query execution via HTTP"""
        result = await database_http_client.call_tool(
            "execute_query", {"sql": "SELECT 1 as value"}
        )
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_http_show_tables(self, database_http_client):
        """Test SHOW TABLES via HTTP"""
        result = await database_http_client.call_tool(
            "execute_query", {"sql": "SHOW TABLES FROM test_mcp_db"}
        )
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_http_get_databases(self, database_http_client):
        """Test get_databases tool via HTTP"""
        result = await database_http_client.call_tool("get_databases", {})
        assert len(result.content) > 0
        content_text = result.content[0].text
        assert "test_mcp_db" in content_text

    @pytest.mark.asyncio
    async def test_http_get_tables(self, database_http_client):
        """Test get_tables tool via HTTP"""
        result = await database_http_client.call_tool("get_tables", {"database": "test_mcp_db"})
        assert len(result.content) > 0
        content_text = result.content[0].text
        assert "users" in content_text

    @pytest.mark.asyncio
    async def test_http_security_status(self, database_http_client):
        """Test security_status tool via HTTP"""
        result = await database_http_client.call_tool("security_status", {})
        assert len(result.content) > 0
        content_text = result.content[0].text.lower()
        assert "security" in content_text

    @pytest.mark.asyncio
    async def test_http_monitoring_status(self, database_http_client):
        """Test monitoring_status tool via HTTP"""
        result = await database_http_client.call_tool("monitoring_status", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_http_health_check(self, database_http_client):
        """Test health_check tool via HTTP"""
        result = await database_http_client.call_tool("health_check", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_http_sql_injection_detection(self, database_http_client):
        """Test SQL injection detection via HTTP"""
        # This query contains SQL injection patterns
        malicious_query = "SELECT * FROM users; DROP TABLE users--"
        result = await database_http_client.call_tool("execute_query", {"sql": malicious_query})
        assert len(result.content) > 0
        content_text = result.content[0].text.lower()
        # Security system should detect and block/warn
        assert "error" in content_text or "blocked" in content_text or "not allowed" in content_text or "syntax" in content_text

    @pytest.mark.asyncio
    async def test_http_schema_info(self, database_http_client):
        """Test schema_info tool via HTTP"""
        result = await database_http_client.call_tool("schema_info", {"database": "test_mcp_db"})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_http_table_info(self, database_http_client):
        """Test table_info tool via HTTP"""
        result = await database_http_client.call_tool("table_info", {
            "database": "test_mcp_db",
            "table": "users"
        })
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_http_connection_stats(self, database_http_client):
        """Test connection_stats tool via HTTP"""
        result = await database_http_client.call_tool("connection_stats", {})
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_http_performance_metrics(self, database_http_client):
        """Test performance_metrics tool via HTTP"""
        result = await database_http_client.call_tool("performance_metrics", {})
        assert len(result.content) > 0


# ==============================================================================
# Protocol Parity Tests
# ==============================================================================


@pytest.mark.e2e
class TestDatabaseProtocolParity:
    """Test that all protocols return consistent results"""

    @pytest.mark.asyncio
    async def test_simple_query_parity(self, database_stdio_client, database_sse_client):
        """Test simple query returns consistent results across protocols"""
        query = "SELECT 42 as answer"

        stdio_result = await database_stdio_client.call_tool("execute_query", {"sql": query})
        sse_result = await database_sse_client.call_tool("execute_query", {"sql": query})

        assert len(stdio_result.content) > 0
        assert len(sse_result.content) > 0

        # Both should contain the answer value
        stdio_text = stdio_result.content[0].text
        sse_text = sse_result.content[0].text

        assert "42" in stdio_text
        assert "42" in sse_text


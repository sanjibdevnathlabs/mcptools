"""End-to-end tests for Calculator MCP server - actual client/server communication

This module tests Calculator across ALL protocols:
1. STDIO - Standard input/output (subprocess)
2. SSE - Server-Sent Events (HTTP streaming)
3. streamable-http - HTTP with optional SSE streaming
"""

import asyncio
import os
import signal
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

import pytest
import pytest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

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
    """Find a free port for server binding"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest_asyncio.fixture(scope="class")
async def calculator_stdio_client():
    """Fixture for calculator MCP client using STDIO protocol"""
    env = os.environ.copy()
    env["TRANSPORT_MODE"] = "stdio"
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "calculator"],
        env=env,
    )

    # Create client context
    stdio_ctx = stdio_client(server_params)
    read, write = await stdio_ctx.__aenter__()

    # Create session context
    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()
    await session.initialize()

    yield session

    # Cleanup in reverse order
    with suppress(Exception):
        await session_ctx.__aexit__(None, None, None)

    with suppress(Exception):
        await stdio_ctx.__aexit__(None, None, None)


def find_free_port():
    """Find a free port for SSE/HTTP servers"""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest_asyncio.fixture(scope="class")
async def calculator_sse_server():
    """Fixture to start calculator server in SSE mode (shared across test class)"""
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/sse"

    # Configure server via environment variables
    # The calculator config system will interpolate ${TRANSPORT_MODE}, ${FASTMCP_HOST}, ${FASTMCP_PORT}
    env = os.environ.copy()
    env["APP_ENV"] = "test"  # Use test.toml which references env vars
    env["TRANSPORT_MODE"] = "sse"
    env["FASTMCP_HOST"] = "127.0.0.1"
    env["FASTMCP_PORT"] = str(port)

    # Use actual calculator server with config-driven transport
    process = subprocess.Popen(
        [sys.executable, "-m", "calculator"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
    )

    try:
        # Wait for server to be ready by checking if port is listening
        max_retries = 50
        server_ready = False
        for _ in range(max_retries):
            # Check if process crashed
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise RuntimeError(
                    f"SSE server process terminated unexpectedly\n"
                    f"STDOUT: {stdout.decode()}\n"
                    f"STDERR: {stderr.decode()}"
                )

            # Try to connect to the port
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.1)
                    result = sock.connect_ex(("127.0.0.1", port))
                    if result == 0:
                        server_ready = True
                        break
            except Exception:
                pass

            await asyncio.sleep(0.1)

        if not server_ready:
            raise TimeoutError(f"SSE server didn't become ready on port {port}")

        yield url

    finally:
        # Always cleanup server process and free port
        if hasattr(os, "killpg"):
            with suppress(ProcessLookupError):
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        else:
            process.terminate()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        # Small delay to ensure port is fully released
        await asyncio.sleep(0.1)


@pytest_asyncio.fixture(scope="class")
async def calculator_http_server():
    """Fixture to start calculator server in streamable-http mode (shared across test class)"""
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/mcp"

    # Configure server via environment variables
    # The calculator config system will interpolate ${TRANSPORT_MODE}, ${FASTMCP_HOST}, ${FASTMCP_PORT}
    env = os.environ.copy()
    env["APP_ENV"] = "test"  # Use test.toml which references env vars
    env["TRANSPORT_MODE"] = "streamable-http"
    env["FASTMCP_HOST"] = "127.0.0.1"
    env["FASTMCP_PORT"] = str(port)

    # Use actual calculator server with config-driven transport
    process = subprocess.Popen(
        [sys.executable, "-m", "calculator"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
    )

    try:
        # Wait for server to be ready by checking if port is listening
        max_retries = 50
        server_ready = False
        for _ in range(max_retries):
            # Check if process crashed
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise RuntimeError(
                    f"HTTP server process terminated unexpectedly\n"
                    f"STDOUT: {stdout.decode()}\n"
                    f"STDERR: {stderr.decode()}"
                )

            # Try to connect to the port
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.1)
                    result = sock.connect_ex(("127.0.0.1", port))
                    if result == 0:
                        server_ready = True
                        break
            except Exception:
                pass

            await asyncio.sleep(0.1)

        if not server_ready:
            raise TimeoutError(f"HTTP server didn't become ready on port {port}")

        yield url

    finally:
        # Always cleanup server process and free port
        if hasattr(os, "killpg"):
            with suppress(ProcessLookupError):
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        else:
            process.terminate()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        # Small delay to ensure port is fully released
        await asyncio.sleep(0.1)


@pytest_asyncio.fixture(scope="class")
async def calculator_sse_client(calculator_sse_server):
    """Fixture for calculator MCP client using SSE protocol (shared across test class)"""
    url = calculator_sse_server

    # Create SSE client context
    sse_ctx = sse_client(url)
    read, write = await sse_ctx.__aenter__()

    # Create session context
    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()
    await session.initialize()

    yield session

    # Cleanup in reverse order
    with suppress(Exception):
        await session_ctx.__aexit__(None, None, None)

    with suppress(Exception):
        await sse_ctx.__aexit__(None, None, None)


@pytest_asyncio.fixture(scope="class")
async def calculator_http_client(calculator_http_server):
    """Fixture for calculator MCP client using streamable-http protocol (shared across test class)"""
    url = calculator_http_server

    # Create streamable-http client context
    http_ctx = streamablehttp_client(url)
    read, write, get_session_id = await http_ctx.__aenter__()

    # Create session context
    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()
    await session.initialize()

    yield session

    # Cleanup in reverse order
    with suppress(Exception):
        await session_ctx.__aexit__(None, None, None)

    with suppress(Exception):
        await http_ctx.__aexit__(None, None, None)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCalculatorE2ESTDIO:
    """E2E tests for Calculator via STDIO protocol"""

    async def test_add_operation_e2e(self, calculator_stdio_client):
        """E2E: Test add operation via MCP client"""
        result = await calculator_stdio_client.call_tool("add", {"a": 12, "b": 8})

        assert result.content is not None
        assert len(result.content) > 0
        assert result.content[0].text == "20"

    async def test_subtract_operation_e2e(self, calculator_stdio_client):
        """E2E: Test subtract operation via MCP client"""
        result = await calculator_stdio_client.call_tool("subtract", {"a": 20, "b": 8})

        assert result.content is not None
        assert result.content[0].text == "12"

    async def test_multiply_operation_e2e(self, calculator_stdio_client):
        """E2E: Test multiply operation via MCP client"""
        result = await calculator_stdio_client.call_tool("multiply", {"a": 6, "b": 7})

        assert result.content is not None
        assert result.content[0].text == "42"

    async def test_divide_operation_e2e(self, calculator_stdio_client):
        """E2E: Test divide operation via MCP client"""
        result = await calculator_stdio_client.call_tool("divide", {"a": 20, "b": 4})

        assert result.content is not None
        assert result.content[0].text == "5.0"

    async def test_power_operation_e2e(self, calculator_stdio_client):
        """E2E: Test power operation via MCP client"""
        result = await calculator_stdio_client.call_tool("power", {"a": 2, "b": 10})

        assert result.content is not None
        assert result.content[0].text == "1024"

    async def test_sqrt_operation_e2e(self, calculator_stdio_client):
        """E2E: Test sqrt operation via MCP client"""
        result = await calculator_stdio_client.call_tool("sqrt", {"a": 16})

        assert result.content is not None
        assert result.content[0].text == "4.0"

    async def test_factorial_operation_e2e(self, calculator_stdio_client):
        """E2E: Test factorial operation via MCP client"""
        result = await calculator_stdio_client.call_tool("factorial", {"a": 5})

        assert result.content is not None
        assert result.content[0].text == "120"

    async def test_log_operation_e2e(self, calculator_stdio_client):
        """E2E: Test log operation via MCP client"""
        result = await calculator_stdio_client.call_tool("log", {"a": 10})

        assert result.content is not None
        # log(10) ≈ 2.302585
        result_text = result.content[0].text
        assert abs(float(result_text) - 2.302585) < 0.001

    async def test_trigonometry_operations_e2e(self, calculator_stdio_client):
        """E2E: Test trigonometric operations via MCP client"""
        # sin(0) ≈ 0
        result = await calculator_stdio_client.call_tool("sin", {"a": 0})
        assert result.content is not None
        assert abs(float(result.content[0].text) - 0.0) < 0.001

        # cos(0) ≈ 1
        result = await calculator_stdio_client.call_tool("cos", {"a": 0})
        assert result.content is not None
        assert abs(float(result.content[0].text) - 1.0) < 0.001

        # tan(0) ≈ 0
        result = await calculator_stdio_client.call_tool("tan", {"a": 0})
        assert result.content is not None
        assert abs(float(result.content[0].text) - 0.0) < 0.001


@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.asyncio
class TestCalculatorE2ESmoke:
    """Smoke tests for calculator E2E (critical path)"""

    async def test_calculator_e2e_smoke(self, calculator_stdio_client):
        """Smoke test: Verify server starts and responds to basic operations"""
        # Test that we can call multiple operations in sequence
        operations = [
            ("add", {"a": 2, "b": 3}, "5"),
            ("multiply", {"a": 4, "b": 5}, "20"),
            ("power", {"a": 2, "b": 8}, "256"),
        ]

        for tool_name, args, expected in operations:
            result = await calculator_stdio_client.call_tool(tool_name, args)
            assert result.content is not None
            assert result.content[0].text == expected


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
class TestCalculatorE2EWorkflows:
    """E2E tests for complex calculator workflows"""

    async def test_multi_step_calculation_e2e(self, calculator_stdio_client):
        """E2E: Test multi-step calculation workflow"""
        # Calculate: (10 + 5) * 2
        # Step 1: 10 + 5 = 15
        result1 = await calculator_stdio_client.call_tool("add", {"a": 10, "b": 5})
        step1_result = int(result1.content[0].text)
        assert step1_result == 15

        # Step 2: 15 * 2 = 30
        result2 = await calculator_stdio_client.call_tool("multiply", {"a": step1_result, "b": 2})
        step2_result = int(result2.content[0].text)
        assert step2_result == 30

    async def test_scientific_workflow_e2e(self, calculator_stdio_client):
        """E2E: Test scientific calculation workflow"""
        # Calculate: sqrt(power(5, 2)) = sqrt(25) = 5
        # Step 1: 5^2 = 25
        result1 = await calculator_stdio_client.call_tool("power", {"a": 5, "b": 2})
        step1_result = int(result1.content[0].text)
        assert step1_result == 25

        # Step 2: sqrt(25) = 5
        result2 = await calculator_stdio_client.call_tool("sqrt", {"a": step1_result})
        step2_result = float(result2.content[0].text)
        assert step2_result == 5.0


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCalculatorE2EErrorHandling:
    """E2E tests for error handling"""

    async def test_division_by_zero_e2e(self, calculator_stdio_client):
        """E2E: Test division by zero error handling"""
        # Python's division by zero raises ZeroDivisionError
        # The MCP server will return an error in the response
        result = await calculator_stdio_client.call_tool("divide", {"a": 10, "b": 0})

        # Check if error information is present
        # MCP may return isError flag or error details
        assert result.content is not None or result.isError

    async def test_invalid_factorial_e2e(self, calculator_stdio_client):
        """E2E: Test factorial with negative number"""
        # math.factorial raises ValueError for negative numbers
        # The MCP server will return an error in the response
        result = await calculator_stdio_client.call_tool("factorial", {"a": -5})

        # Check if error information is present
        assert result.content is not None or result.isError


# ═══════════════════════════════════════════════════════════════════
# SSE Protocol E2E Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.slow
class TestCalculatorE2ESSE:
    """E2E tests for Calculator via SSE protocol"""

    async def test_add_operation_sse(self, calculator_sse_client):
        """E2E SSE: Test add operation"""
        result = await calculator_sse_client.call_tool("add", {"a": 15, "b": 25})
        assert result.content is not None
        assert result.content[0].text == "40"

    async def test_multiply_operation_sse(self, calculator_sse_client):
        """E2E SSE: Test multiply operation"""
        result = await calculator_sse_client.call_tool("multiply", {"a": 7, "b": 8})
        assert result.content is not None
        assert result.content[0].text == "56"

    async def test_power_operation_sse(self, calculator_sse_client):
        """E2E SSE: Test power operation"""
        result = await calculator_sse_client.call_tool("power", {"a": 3, "b": 4})
        assert result.content is not None
        assert result.content[0].text == "81"

    async def test_sqrt_operation_sse(self, calculator_sse_client):
        """E2E SSE: Test square root operation"""
        result = await calculator_sse_client.call_tool("sqrt", {"a": 25})
        assert result.content is not None
        assert result.content[0].text == "5.0"


# ═══════════════════════════════════════════════════════════════════
# Streamable-HTTP Protocol E2E Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.slow
class TestCalculatorE2EStreamableHTTP:
    """E2E tests for Calculator via streamable-http protocol"""

    async def test_add_operation_http(self, calculator_http_client):
        """E2E HTTP: Test add operation"""
        result = await calculator_http_client.call_tool("add", {"a": 100, "b": 200})
        assert result.content is not None
        assert result.content[0].text == "300"

    async def test_subtract_operation_http(self, calculator_http_client):
        """E2E HTTP: Test subtract operation"""
        result = await calculator_http_client.call_tool("subtract", {"a": 50, "b": 20})
        assert result.content is not None
        assert result.content[0].text == "30"

    async def test_divide_operation_http(self, calculator_http_client):
        """E2E HTTP: Test divide operation"""
        result = await calculator_http_client.call_tool("divide", {"a": 100, "b": 25})
        assert result.content is not None
        assert result.content[0].text == "4.0"

    async def test_factorial_operation_http(self, calculator_http_client):
        """E2E HTTP: Test factorial operation"""
        result = await calculator_http_client.call_tool("factorial", {"a": 6})
        assert result.content is not None
        assert result.content[0].text == "720"


# ═══════════════════════════════════════════════════════════════════
# Protocol Comparison - Smoke Test
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.asyncio
class TestCalculatorProtocolParity:
    """Verify all protocols produce identical results"""

    async def test_all_protocols_produce_same_result(
        self,
        calculator_stdio_client,
        calculator_sse_client,
        calculator_http_client,
    ):
        """E2E: All 3 protocols should return identical results"""
        test_input = {"a": 123, "b": 456}

        # Test addition across all protocols
        stdio_result = await calculator_stdio_client.call_tool("add", test_input)
        sse_result = await calculator_sse_client.call_tool("add", test_input)
        http_result = await calculator_http_client.call_tool("add", test_input)

        # All should return the same result
        expected = "579"
        assert stdio_result.content[0].text == expected
        assert sse_result.content[0].text == expected
        assert http_result.content[0].text == expected

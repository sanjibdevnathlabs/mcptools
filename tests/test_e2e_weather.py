"""End-to-end tests for Weather MCP server across all protocols.

Tests all three transport modes:
- STDIO: Standard input/output
- SSE: Server-Sent Events
- Streamable-HTTP: HTTP-based streaming

Each protocol is tested with actual weather server process and mock API server.
"""

import asyncio
import contextlib
import multiprocessing
import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

# ============================================================================
# Helper Functions
# ============================================================================


@pytest.fixture(scope="class")
def event_loop():
    """Create an event loop for the test class"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


def find_free_port() -> int:
    """Find a free port to use for server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def start_mock_weather_api_server(port: int):
    """Start mock OpenWeather API server in separate process"""
    from weather.mock_weather_api import run_mock_server

    run_mock_server(host="127.0.0.1", port=port)


# ============================================================================
# Mock Weather API Server Fixture
# ============================================================================


@pytest.fixture(scope="module")
def mock_weather_api():
    """Start mock OpenWeather API server for E2E tests"""
    port = find_free_port()
    process = multiprocessing.Process(target=start_mock_weather_api_server, args=(port,))
    process.start()

    # Wait for mock API server to start
    mock_api_url = f"http://127.0.0.1:{port}"
    max_retries = 50
    server_ready = False

    for _ in range(max_retries):
        try:
            response = httpx.get(f"{mock_api_url}/health", timeout=1.0)
            if response.status_code == 200:
                server_ready = True
                break
        except Exception:
            time.sleep(0.1)

    if not server_ready:
        process.terminate()
        raise TimeoutError("Mock weather API server failed to start")

    yield mock_api_url

    # Cleanup
    process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        process.kill()


# ============================================================================
# STDIO Protocol Tests
# ============================================================================


@pytest_asyncio.fixture(scope="class")
async def weather_stdio_client(mock_weather_api) -> AsyncGenerator[ClientSession, None]:
    """Fixture for weather MCP client using STDIO protocol (shared across test class)"""
    # MCP SDK's stdio_client doesn't inherit os.environ with env=None
    # Must explicitly pass environment dict
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["OPENWEATHER_API_KEY"] = "test_api_key"
    env["OPENWEATHER_API_BASE"] = f"{mock_weather_api}/data/2.5"

    server_params = StdioServerParameters(
        command="python",
        args=["-m", "weather"],
        env=env,  # Explicitly pass environment
    )

    # Create client context (matches calculator pattern)
    stdio_ctx = stdio_client(server_params)
    read, write = await stdio_ctx.__aenter__()

    # Create session context
    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()
    await session.initialize()

    yield session

    # Cleanup in reverse order
    with contextlib.suppress(Exception):
        await session_ctx.__aexit__(None, None, None)

    with contextlib.suppress(Exception):
        await stdio_ctx.__aexit__(None, None, None)


@pytest.mark.e2e
class TestWeatherSTDIO:
    """E2E tests for weather server using STDIO protocol"""

    @pytest.mark.asyncio
    async def test_stdio_list_tools(self, mock_weather_api, weather_stdio_client):
        """Test listing available tools via STDIO"""
        result = await weather_stdio_client.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert "get_current_weather" in tool_names
        assert "get_forecast" in tool_names

    @pytest.mark.asyncio
    async def test_stdio_get_current_weather_mumbai(self, weather_stdio_client):
        """Test get_current_weather for Mumbai via STDIO"""
        result = await weather_stdio_client.call_tool(
            "get_current_weather", arguments={"city": "Mumbai"}
        )

        assert len(result.content) > 0
        content = str(result.content[0].text)
        assert "Mumbai" in content
        assert "Temperature" in content or "temp" in content.lower()

    @pytest.mark.asyncio
    async def test_stdio_get_current_weather_delhi(self, weather_stdio_client):
        """Test get_current_weather for Delhi via STDIO"""
        result = await weather_stdio_client.call_tool(
            "get_current_weather", arguments={"city": "Delhi"}
        )

        content = str(result.content[0].text)
        assert "Delhi" in content
        assert "°C" in content

    @pytest.mark.asyncio
    async def test_stdio_get_forecast_by_city(self, weather_stdio_client):
        """Test get_forecast by city via STDIO"""
        result = await weather_stdio_client.call_tool(
            "get_forecast", arguments={"city": "Bangalore"}
        )

        content = str(result.content[0].text)
        assert "Bangalore" in content
        assert "Forecast" in content or "forecast" in content.lower()

    @pytest.mark.asyncio
    async def test_stdio_get_forecast_by_coordinates(self, weather_stdio_client):
        """Test get_forecast by coordinates via STDIO"""
        result = await weather_stdio_client.call_tool(
            "get_forecast", arguments={"latitude": 19.0760, "longitude": 72.8777}
        )

        content = str(result.content[0].text)
        assert "Forecast" in content or "forecast" in content.lower()
        assert "Temperature" in content or "temp" in content.lower()

    @pytest.mark.asyncio
    async def test_stdio_invalid_city(self, weather_stdio_client):
        """Test handling invalid city via STDIO"""
        result = await weather_stdio_client.call_tool(
            "get_current_weather", arguments={"city": "InvalidCity123"}
        )

        content = str(result.content[0].text)
        assert "Unable to fetch" in content or "unavailable" in content.lower()


# ============================================================================
# SSE Protocol Tests
# ============================================================================


@pytest_asyncio.fixture(scope="class")
async def weather_sse_server(mock_weather_api):
    """Fixture to start weather server in SSE mode with mock API (shared across test class)"""
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/sse"

    # Configure server via environment variables
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["TRANSPORT_MODE"] = "sse"
    env["FASTMCP_HOST"] = "127.0.0.1"
    env["FASTMCP_PORT"] = str(port)
    env["OPENWEATHER_API_KEY"] = "test_api_key"
    env["OPENWEATHER_API_BASE"] = f"{mock_weather_api}/data/2.5"

    # Start weather server
    process = subprocess.Popen(
        [sys.executable, "-m", "weather"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
    )

    try:
        # Wait for server to be ready
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
            with contextlib.suppress(ProcessLookupError):
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
async def weather_sse_client(weather_sse_server) -> AsyncGenerator[ClientSession, None]:
    """Fixture for weather MCP client using SSE protocol (shared across test class)"""
    url = weather_sse_server

    # Create SSE client context
    sse_ctx = sse_client(url)
    read, write = await sse_ctx.__aenter__()

    # Create session context
    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()
    await session.initialize()

    yield session

    # Cleanup in reverse order
    with contextlib.suppress(Exception):
        await session_ctx.__aexit__(None, None, None)

    with contextlib.suppress(Exception):
        await sse_ctx.__aexit__(None, None, None)


@pytest.mark.e2e
class TestWeatherSSE:
    """E2E tests for weather server using SSE protocol"""

    @pytest.mark.asyncio
    async def test_sse_list_tools(self, weather_sse_client):
        """Test listing available tools via SSE"""
        result = await weather_sse_client.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert "get_current_weather" in tool_names
        assert "get_forecast" in tool_names

    @pytest.mark.asyncio
    async def test_sse_get_current_weather_mumbai(self, weather_sse_client):
        """Test get_current_weather for Mumbai via SSE"""
        result = await weather_sse_client.call_tool(
            "get_current_weather", arguments={"city": "Mumbai"}
        )

        content = str(result.content[0].text)
        assert "Mumbai" in content
        assert "Temperature" in content or "temp" in content.lower()

    @pytest.mark.asyncio
    async def test_sse_get_current_weather_delhi(self, weather_sse_client):
        """Test get_current_weather for Delhi via SSE"""
        result = await weather_sse_client.call_tool(
            "get_current_weather", arguments={"city": "Delhi"}
        )

        content = str(result.content[0].text)
        assert "Delhi" in content

    @pytest.mark.asyncio
    async def test_sse_get_forecast_by_city(self, weather_sse_client):
        """Test get_forecast by city via SSE"""
        result = await weather_sse_client.call_tool(
            "get_forecast", arguments={"city": "Bangalore"}
        )

        content = str(result.content[0].text)
        assert "Bangalore" in content
        assert "Forecast" in content or "forecast" in content.lower()

    @pytest.mark.asyncio
    async def test_sse_get_forecast_by_coordinates(self, weather_sse_client):
        """Test get_forecast by coordinates via SSE"""
        result = await weather_sse_client.call_tool(
            "get_forecast", arguments={"latitude": 19.0760, "longitude": 72.8777}
        )

        content = str(result.content[0].text)
        assert "Forecast" in content or "forecast" in content.lower()

    @pytest.mark.asyncio
    async def test_sse_invalid_city(self, weather_sse_client):
        """Test handling invalid city via SSE"""
        result = await weather_sse_client.call_tool(
            "get_current_weather", arguments={"city": "InvalidCity123"}
        )

        content = str(result.content[0].text)
        assert "Unable to fetch" in content or "unavailable" in content.lower()


# ============================================================================
# Streamable-HTTP Protocol Tests
# ============================================================================


@pytest_asyncio.fixture(scope="class")
async def weather_http_server(mock_weather_api):
    """Fixture to start weather server in HTTP mode with mock API (shared across test class)"""
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/mcp"

    # Configure server via environment variables
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["TRANSPORT_MODE"] = "streamable-http"
    env["FASTMCP_HOST"] = "127.0.0.1"
    env["FASTMCP_PORT"] = str(port)
    env["OPENWEATHER_API_KEY"] = "test_api_key"
    env["OPENWEATHER_API_BASE"] = f"{mock_weather_api}/data/2.5"

    # Start weather server
    process = subprocess.Popen(
        [sys.executable, "-m", "weather"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
    )

    try:
        # Wait for server to be ready
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
            with contextlib.suppress(ProcessLookupError):
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
async def weather_http_client(weather_http_server) -> AsyncGenerator[ClientSession, None]:
    """Fixture for weather MCP client using streamable-http protocol (shared across test class)"""
    url = weather_http_server

    # Create streamable-http client context
    http_ctx = streamablehttp_client(url)
    read, write, get_session_id = await http_ctx.__aenter__()

    # Create session context
    session_ctx = ClientSession(read, write)
    session = await session_ctx.__aenter__()
    await session.initialize()

    yield session

    # Cleanup in reverse order
    with contextlib.suppress(Exception):
        await session_ctx.__aexit__(None, None, None)

    with contextlib.suppress(Exception):
        await http_ctx.__aexit__(None, None, None)


@pytest.mark.e2e
class TestWeatherHTTP:
    """E2E tests for weather server using Streamable-HTTP protocol"""

    @pytest.mark.asyncio
    async def test_http_list_tools(self, weather_http_client):
        """Test listing available tools via HTTP"""
        result = await weather_http_client.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert "get_current_weather" in tool_names
        assert "get_forecast" in tool_names

    @pytest.mark.asyncio
    async def test_http_get_current_weather_mumbai(self, weather_http_client):
        """Test get_current_weather for Mumbai via HTTP"""
        result = await weather_http_client.call_tool(
            "get_current_weather", arguments={"city": "Mumbai"}
        )

        content = str(result.content[0].text)
        assert "Mumbai" in content
        assert "Temperature" in content or "temp" in content.lower()

    @pytest.mark.asyncio
    async def test_http_get_current_weather_delhi(self, weather_http_client):
        """Test get_current_weather for Delhi via HTTP"""
        result = await weather_http_client.call_tool(
            "get_current_weather", arguments={"city": "Delhi"}
        )

        content = str(result.content[0].text)
        assert "Delhi" in content

    @pytest.mark.asyncio
    async def test_http_get_forecast_by_city(self, weather_http_client):
        """Test get_forecast by city via HTTP"""
        result = await weather_http_client.call_tool(
            "get_forecast", arguments={"city": "Bangalore"}
        )

        content = str(result.content[0].text)
        assert "Bangalore" in content
        assert "Forecast" in content or "forecast" in content.lower()

    @pytest.mark.asyncio
    async def test_http_get_forecast_by_coordinates(self, weather_http_client):
        """Test get_forecast by coordinates via HTTP"""
        result = await weather_http_client.call_tool(
            "get_forecast", arguments={"latitude": 19.0760, "longitude": 72.8777}
        )

        content = str(result.content[0].text)
        assert "Forecast" in content or "forecast" in content.lower()

    @pytest.mark.asyncio
    async def test_http_invalid_city(self, weather_http_client):
        """Test handling invalid city via HTTP"""
        result = await weather_http_client.call_tool(
            "get_current_weather", arguments={"city": "InvalidCity123"}
        )

        content = str(result.content[0].text)
        assert "Unable to fetch" in content or "unavailable" in content.lower()


# ============================================================================
# Protocol Parity Tests
# ============================================================================


@pytest.mark.e2e
class TestWeatherProtocolParity:
    """Verify all three protocols produce identical results"""

    @pytest.mark.asyncio
    async def test_current_weather_parity(
        self, weather_stdio_client, weather_sse_client, weather_http_client
    ):
        """Test get_current_weather produces same result across all protocols"""
        # Get results from all three protocols
        stdio_result = await weather_stdio_client.call_tool(
            "get_current_weather", arguments={"city": "Mumbai"}
        )
        sse_result = await weather_sse_client.call_tool(
            "get_current_weather", arguments={"city": "Mumbai"}
        )
        http_result = await weather_http_client.call_tool(
            "get_current_weather", arguments={"city": "Mumbai"}
        )

        # Extract content
        stdio_content = str(stdio_result.content[0].text)
        sse_content = str(sse_result.content[0].text)
        http_content = str(http_result.content[0].text)

        # Verify all contain essential weather data
        for content in [stdio_content, sse_content, http_content]:
            assert "Mumbai" in content
            assert "Temperature" in content or "temp" in content.lower()
            assert "°C" in content
            assert "Humidity" in content or "humidity" in content.lower()

    @pytest.mark.asyncio
    async def test_forecast_parity(
        self, weather_stdio_client, weather_sse_client, weather_http_client
    ):
        """Test get_forecast produces same result across all protocols"""
        args = {"city": "Delhi"}

        stdio_result = await weather_stdio_client.call_tool("get_forecast", arguments=args)
        sse_result = await weather_sse_client.call_tool("get_forecast", arguments=args)
        http_result = await weather_http_client.call_tool("get_forecast", arguments=args)

        # Extract content
        stdio_content = str(stdio_result.content[0].text)
        sse_content = str(sse_result.content[0].text)
        http_content = str(http_result.content[0].text)

        # Verify all contain forecast data
        for content in [stdio_content, sse_content, http_content]:
            assert "Delhi" in content
            assert "Forecast" in content or "forecast" in content.lower()
            assert "Temperature" in content or "temp" in content.lower()


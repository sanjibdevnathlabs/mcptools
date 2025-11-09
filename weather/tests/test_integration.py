"""Integration tests for Weather MCP server - hit mock API server"""

import multiprocessing
import time

import httpx
import pytest

# Will be initialized in fixtures
MOCK_SERVER_URL = None


def start_mock_server(port: int):
    """Start mock weather API server in separate process"""
    from weather.mock_weather_api import run_mock_server

    run_mock_server(host="127.0.0.1", port=port)


@pytest.fixture(scope="module")
def mock_weather_server():
    """Start mock OpenWeather API server for integration tests"""
    port = 8765
    process = multiprocessing.Process(target=start_mock_server, args=(port,))
    process.start()

    # Wait for server to start
    global MOCK_SERVER_URL
    MOCK_SERVER_URL = f"http://127.0.0.1:{port}"

    max_retries = 30
    for _ in range(max_retries):
        try:
            response = httpx.get(f"{MOCK_SERVER_URL}/health", timeout=1.0)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    else:
        process.terminate()
        raise TimeoutError("Mock weather API server failed to start")

    yield MOCK_SERVER_URL

    # Cleanup
    process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        process.kill()


@pytest.mark.integration
class TestWeatherIntegration:
    """Integration tests with mock weather API"""

    @pytest.mark.asyncio
    async def test_get_current_weather_mumbai(self, mock_weather_server):
        """Test getting current weather for Mumbai"""
        # Import after mock server is ready
        import weather.main

        # Override API base URL to point to mock server
        original_api_base = weather.main.config.api.openweather_api_base
        weather.main.config.api.openweather_api_base = f"{mock_weather_server}/data/2.5"
        weather.main.config.api.openweather_api_key = "test_api_key"

        try:
            result = await weather.main.get_current_weather("Mumbai")

            # Verify response contains expected data
            assert "Mumbai" in result
            assert "Temperature" in result or "temp" in result.lower()
            assert "°C" in result
            assert "Humidity" in result or "humidity" in result.lower()

        finally:
            # Restore original API base
            weather.main.config.api.openweather_api_base = original_api_base

    @pytest.mark.asyncio
    async def test_get_current_weather_delhi(self, mock_weather_server):
        """Test getting current weather for Delhi"""
        import weather.main

        original_api_base = weather.main.config.api.openweather_api_base
        weather.main.config.api.openweather_api_base = f"{mock_weather_server}/data/2.5"
        weather.main.config.api.openweather_api_key = "test_api_key"

        try:
            result = await weather.main.get_current_weather("Delhi")

            assert "Delhi" in result
            assert "Temperature" in result or "temp" in result.lower()
            assert "°C" in result

        finally:
            weather.main.config.api.openweather_api_base = original_api_base

    @pytest.mark.asyncio
    async def test_get_current_weather_bangalore(self, mock_weather_server):
        """Test getting current weather for Bangalore"""
        import weather.main

        original_api_base = weather.main.config.api.openweather_api_base
        weather.main.config.api.openweather_api_base = f"{mock_weather_server}/data/2.5"
        weather.main.config.api.openweather_api_key = "test_api_key"

        try:
            result = await weather.main.get_current_weather("Bangalore")

            assert "Bangalore" in result
            assert "light rain" in result.lower() or "rain" in result.lower()

        finally:
            weather.main.config.api.openweather_api_base = original_api_base

    @pytest.mark.asyncio
    async def test_get_forecast_by_city(self, mock_weather_server):
        """Test getting 5-day forecast by city"""
        import weather.main

        original_api_base = weather.main.config.api.openweather_api_base
        weather.main.config.api.openweather_api_base = f"{mock_weather_server}/data/2.5"
        weather.main.config.api.openweather_api_key = "test_api_key"

        try:
            result = await weather.main.get_forecast(city="Mumbai")

            assert "Mumbai" in result
            assert "Forecast" in result or "forecast" in result.lower()
            # Should have multiple days
            assert result.count("Weather") >= 1 or result.count("Temperature") >= 1

        finally:
            weather.main.config.api.openweather_api_base = original_api_base

    @pytest.mark.asyncio
    async def test_get_forecast_by_coordinates(self, mock_weather_server):
        """Test getting forecast by coordinates"""
        import weather.main

        original_api_base = weather.main.config.api.openweather_api_base
        weather.main.config.api.openweather_api_base = f"{mock_weather_server}/data/2.5"
        weather.main.config.api.openweather_api_key = "test_api_key"

        try:
            # Mumbai coordinates
            result = await weather.main.get_forecast(
                latitude=19.0760, longitude=72.8777
            )

            assert "Forecast" in result or "forecast" in result.lower()
            assert "Temperature" in result or "temp" in result.lower()

        finally:
            weather.main.config.api.openweather_api_base = original_api_base

    @pytest.mark.asyncio
    async def test_invalid_city(self, mock_weather_server):
        """Test handling invalid city name"""
        import weather.main

        original_api_base = weather.main.config.api.openweather_api_base
        weather.main.config.api.openweather_api_base = f"{mock_weather_server}/data/2.5"
        weather.main.config.api.openweather_api_key = "test_api_key"

        try:
            result = await weather.main.get_current_weather("InvalidCityName123")

            assert "Unable to fetch" in result or "unavailable" in result.lower()

        finally:
            weather.main.config.api.openweather_api_base = original_api_base

    @pytest.mark.asyncio
    async def test_weather_workflow(self, mock_weather_server):
        """Test complete weather workflow"""
        import weather.main

        original_api_base = weather.main.config.api.openweather_api_base
        weather.main.config.api.openweather_api_base = f"{mock_weather_server}/data/2.5"
        weather.main.config.api.openweather_api_key = "test_api_key"

        try:
            # Get current weather
            current = await weather.main.get_current_weather("Mumbai")
            assert "Mumbai" in current

            # Get forecast for same city
            forecast = await weather.main.get_forecast(city="Mumbai")
            assert "Mumbai" in forecast
            assert "Forecast" in forecast or "forecast" in forecast.lower()

            # Both should have temperature data
            assert "Temperature" in current or "temp" in current.lower()
            assert "Temperature" in forecast or "temp" in forecast.lower()

        finally:
            weather.main.config.api.openweather_api_base = original_api_base


@pytest.mark.integration
@pytest.mark.smoke
class TestWeatherCriticalPaths:
    """Critical path and smoke tests for weather integration"""

    @pytest.mark.asyncio
    async def test_smoke_all_operations(self, mock_weather_server):
        """Smoke test: ensure all operations work"""
        import weather.main

        original_api_base = weather.main.config.api.openweather_api_base
        weather.main.config.api.openweather_api_base = f"{mock_weather_server}/data/2.5"
        weather.main.config.api.openweather_api_key = "test_api_key"

        try:
            # Current weather
            current = await weather.main.get_current_weather("Delhi")
            assert isinstance(current, str)
            assert len(current) > 0

            # Forecast by city
            forecast_city = await weather.main.get_forecast(city="Mumbai")
            assert isinstance(forecast_city, str)
            assert len(forecast_city) > 0

            # Forecast by coordinates
            forecast_coords = await weather.main.get_forecast(
                latitude=19.0, longitude=72.8
            )
            assert isinstance(forecast_coords, str)
            assert len(forecast_coords) > 0

        finally:
            weather.main.config.api.openweather_api_base = original_api_base

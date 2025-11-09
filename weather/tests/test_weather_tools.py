"""Unit tests for weather tools with mocked HTTP calls"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import after mocking to avoid real API calls during import
with patch("weather.main.Config"):
    from weather.main import (
        format_weather_condition,
        get_current_weather,
        get_forecast,
    )


@pytest.mark.unit
class TestWeatherTools:
    """Test weather tool functions with mocked HTTP"""

    @pytest.mark.asyncio
    async def test_get_current_weather_success(self):
        """Test successful current weather retrieval"""
        # Mock response data
        mock_response_data = {
            "cod": 200,
            "name": "Mumbai",
            "main": {
                "temp": 28.5,
                "feels_like": 31.2,
                "humidity": 75,
                "pressure": 1013,
            },
            "weather": [{"main": "Clouds", "description": "few clouds"}],
            "wind": {"speed": 5.5, "deg": 270},
            "visibility": 10000,
        }

        # Mock httpx.AsyncClient
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Call the function
            result = await get_current_weather("Mumbai")

            # Assertions
            assert "Mumbai" in result
            assert "28.5" in result
            assert "few clouds" in result.lower()
            assert "75%" in result

    @pytest.mark.asyncio
    async def test_get_current_weather_empty_city(self):
        """Test error handling for empty city name"""
        result = await get_current_weather("")
        assert "Error" in result or "valid city name" in result

    @pytest.mark.asyncio
    async def test_get_current_weather_invalid_city(self):
        """Test error handling for invalid city"""
        mock_response_data = {"cod": 404, "message": "city not found"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await get_current_weather("InvalidCity")
            assert "Error" in result or "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_get_current_weather_network_error(self):
        """Test error handling for network errors"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Network error")
            )

            result = await get_current_weather("Mumbai")
            assert "Unable" in result or "unavailable" in result.lower()

    @pytest.mark.asyncio
    async def test_get_forecast_by_city_success(self):
        """Test successful forecast retrieval by city"""
        mock_response_data = {
            "cod": "200",
            "city": {"name": "Delhi"},
            "list": [
                {
                    "dt_txt": "2025-11-08 12:00:00",
                    "main": {
                        "temp": 25.0,
                        "temp_max": 27.0,
                        "temp_min": 22.0,
                        "humidity": 60,
                        "pressure": 1015,
                    },
                    "weather": [{"description": "clear sky"}],
                    "wind": {"speed": 3.5},
                }
            ],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await get_forecast(city="Delhi")

            assert "Delhi" in result
            assert "25.0" in result
            assert "clear sky" in result.lower()

    @pytest.mark.asyncio
    async def test_get_forecast_by_coordinates_success(self):
        """Test successful forecast retrieval by coordinates"""
        mock_response_data = {
            "cod": "200",
            "city": {"name": "Location"},
            "list": [
                {
                    "dt_txt": "2025-11-08 12:00:00",
                    "main": {
                        "temp": 30.0,
                        "temp_max": 32.0,
                        "temp_min": 28.0,
                        "humidity": 70,
                        "pressure": 1010,
                    },
                    "weather": [{"description": "scattered clouds"}],
                    "wind": {"speed": 4.0},
                }
            ],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await get_forecast(latitude=19.0760, longitude=72.8777)

            assert "30.0" in result
            assert "scattered clouds" in result.lower()

    @pytest.mark.asyncio
    async def test_get_forecast_missing_parameters(self):
        """Test error when neither city nor coordinates provided"""
        result = await get_forecast()
        assert "Error" in result or "provide" in result.lower()

    @pytest.mark.asyncio
    async def test_get_forecast_invalid_latitude(self):
        """Test error for latitude outside India range"""
        result = await get_forecast(latitude=50.0, longitude=75.0)
        assert "Error" in result or "range" in result.lower()

    @pytest.mark.asyncio
    async def test_get_forecast_invalid_longitude(self):
        """Test error for longitude outside India range"""
        result = await get_forecast(latitude=20.0, longitude=150.0)
        assert "Error" in result or "range" in result.lower()

    @pytest.mark.asyncio
    async def test_get_forecast_short_city_name(self):
        """Test error for too short city name"""
        result = await get_forecast(city="A")
        assert "Error" in result or "valid city name" in result.lower()


@pytest.mark.unit
class TestHelperFunctions:
    """Test helper functions"""

    def test_format_weather_condition_normal(self):
        """Test formatting normal weather conditions"""
        mock_data = {
            "name": "Mumbai",
            "main": {
                "temp": 28.5,
                "feels_like": 31.2,
                "humidity": 75,
                "pressure": 1013,
            },
            "weather": [{"main": "Clear", "description": "clear sky"}],
            "wind": {"speed": 5.5, "deg": 270},
            "visibility": 10000,
        }

        result = format_weather_condition(mock_data)

        assert "Mumbai" in result
        assert "28.5" in result
        assert "Clear Sky" in result
        assert "75%" in result
        assert "5.5" in result

    def test_format_weather_condition_severe_weather(self):
        """Test formatting severe weather with alert"""
        mock_data = {
            "name": "Delhi",
            "main": {
                "temp": 25.0,
                "feels_like": 24.0,
                "humidity": 80,
                "pressure": 1010,
            },
            "weather": [{"main": "Thunderstorm", "description": "heavy thunderstorm"}],
            "wind": {"speed": 10.0, "deg": 180},
            "visibility": 5000,
        }

        result = format_weather_condition(mock_data)

        assert "SEVERE WEATHER ALERT" in result or "⚠️" in result
        assert "Delhi" in result
        assert "thunderstorm" in result.lower()

    def test_format_weather_condition_rain(self):
        """Test formatting rainy weather with advisory"""
        mock_data = {
            "name": "Bangalore",
            "main": {
                "temp": 22.0,
                "feels_like": 22.0,
                "humidity": 85,
                "pressure": 1008,
            },
            "weather": [{"main": "Rain", "description": "light rain"}],
            "wind": {"speed": 4.0, "deg": 90},
            "visibility": 8000,
        }

        result = format_weather_condition(mock_data)

        assert "Weather Advisory" in result or "🌧️" in result
        assert "Bangalore" in result
        assert "light rain" in result.lower()

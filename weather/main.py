from typing import Any, Optional

import httpx
from mcp.server import FastMCP
from mcp.server.fastmcp.prompts import base

from shared.logging import setup_logging
from weather.config import Config

# Initialize config
config = Config()

# Setup logging using shared logging module
# Pass transport_mode so stdio can be forced to file logging
logger = setup_logging(config, "weather", transport_mode=config.server.transport_mode)

# Create FastMCP server using configuration
# Pass host/port explicitly so FastMCP doesn't use defaults
mcp = FastMCP(config.app.name, host=config.server.host, port=config.server.port)


async def make_openweather_request(
    url: str, params: dict[str, Any] = None
) -> dict[str, Any] | None:
    """Make a request to the OpenWeatherMap API with proper error handling."""
    if not config.api.openweather_api_key:
        logger.error("OpenWeatherMap API key not configured")
        return None

    headers = {"User-Agent": config.api.user_agent, "Accept": "application/json"}

    # Add API key to parameters
    if params is None:
        params = {}
    params["appid"] = config.api.openweather_api_key

    try:
        async with httpx.AsyncClient(timeout=float(config.api.timeout)) as client:
            logger.debug(f"Making request to: {url} with params: {params}")
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error(f"Timeout while requesting {url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}")
        return None


def format_weather_condition(data: dict) -> str:
    """Format current weather condition data from OpenWeatherMap API."""
    main = data.get("main", {})
    weather = data.get("weather", [{}])[0]
    wind = data.get("wind", {})

    # Check for severe weather conditions
    weather_main = weather.get("main", "").lower()
    description = weather.get("description", "")

    severity_indicator = ""
    if weather_main in ["thunderstorm", "tornado", "hurricane"]:
        severity_indicator = "⚠️ SEVERE WEATHER ALERT"
    elif weather_main in ["rain", "snow", "drizzle"]:
        severity_indicator = "🌧️ Weather Advisory"

    return f"""
{severity_indicator}
Location: {data.get('name', 'Unknown')}
Current Weather: {description.title()}
Temperature: {main.get('temp', 'N/A')}°C (Feels like: {main.get('feels_like', 'N/A')}°C)
Humidity: {main.get('humidity', 'N/A')}%
Pressure: {main.get('pressure', 'N/A')} hPa
Wind: {wind.get('speed', 'N/A')} m/s, {wind.get('deg', 'N/A')}°
Visibility: {data.get('visibility', 'N/A')} meters
"""


@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for an Indian city.

    Args:
        city: Name of an Indian city (e.g. Mumbai, Delhi, Bangalore)
    """
    try:
        # Validate city name
        if not city or len(city.strip()) < 2:
            return "Error: Please provide a valid city name (e.g., Mumbai, Delhi, Bangalore)."

        city = city.strip()
        logger.info(f"Fetching current weather for city: {city}")

        # Use OpenWeatherMap current weather API
        url = f"{config.api.openweather_api_base}/weather"
        params = {
            "q": f"{city},IN",  # IN is the country code for India
            "units": "metric",  # Use Celsius
        }

        data = await make_openweather_request(url, params)

        if not data:
            return f"Unable to fetch weather data for {city}. The weather service may be temporarily unavailable."

        if data.get("cod") != 200:
            error_message = data.get("message", "Unknown error")
            return f"Error fetching weather for {city}: {error_message}"

        formatted_weather = format_weather_condition(data)
        logger.info(f"Successfully retrieved weather for {city}")
        return formatted_weather

    except Exception as e:
        logger.error(f"Error getting weather for {city}: {e}")
        return f"Error retrieving weather for {city}. Please try again later."


@mcp.tool()
async def get_forecast(
    city: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> str:
    """Get 5-day weather forecast for an Indian location.

    Args:
        city: Name of an Indian city (e.g. Mumbai, Delhi, Bangalore) - if provided, latitude/longitude are ignored
        latitude: Latitude of the location (for coordinate-based queries)
        longitude: Longitude of the location (for coordinate-based queries)
    """
    try:
        # Validate input - either city or coordinates must be provided
        if city:
            city = city.strip()
            if len(city) < 2:
                return "Error: Please provide a valid city name (e.g., Mumbai, Delhi, Bangalore)."

            logger.info(f"Fetching forecast for city: {city}")
            params = {
                "q": f"{city},IN",  # IN is the country code for India
                "units": "metric",  # Use Celsius
            }
        elif latitude is not None and longitude is not None:
            # Validate coordinates for India (approximately)
            if not (6 <= latitude <= 37):  # India's latitude range
                return "Error: Latitude must be within India's range (approximately 6° to 37° N)."
            if not (68 <= longitude <= 97):  # India's longitude range
                return "Error: Longitude must be within India's range (approximately 68° to 97° E)."

            logger.info(f"Fetching forecast for coordinates: {latitude}, {longitude}")
            params = {
                "lat": latitude,
                "lon": longitude,
                "units": "metric",  # Use Celsius
            }
        else:
            return "Error: Please provide either a city name or both latitude and longitude coordinates."

        # Use OpenWeatherMap 5-day forecast API
        url = f"{config.api.openweather_api_base}/forecast"
        data = await make_openweather_request(url, params)

        if not data:
            return "Unable to fetch forecast data. The weather service may be temporarily unavailable."

        if data.get("cod") != "200":
            error_message = data.get("message", "Unknown error")
            return f"Error fetching forecast: {error_message}"

        # Format the forecast data
        city_name = data.get("city", {}).get("name", "Unknown Location")
        forecasts = []

        # Group forecasts by day (OpenWeatherMap returns 3-hour intervals)
        daily_forecasts = {}
        for item in data.get("list", [])[
            :15
        ]:  # Limit to next 5 days (3-hour intervals)
            dt_txt = item.get("dt_txt", "")
            date = dt_txt.split(" ")[0] if dt_txt else "Unknown"

            if date not in daily_forecasts:
                daily_forecasts[date] = []
            daily_forecasts[date].append(item)

        for date, periods in list(daily_forecasts.items())[:5]:  # Only show next 5 days
            # Get representative data (midday if available, otherwise first available)
            period = periods[len(periods) // 2] if periods else periods[0]

            main = period.get("main", {})
            weather = period.get("weather", [{}])[0]
            wind = period.get("wind", {})

            forecast = f"""
{date}:
Weather: {weather.get('description', 'N/A').title()}
Temperature: {main.get('temp', 'N/A')}°C (High: {main.get('temp_max', 'N/A')}°C, Low: {main.get('temp_min', 'N/A')}°C)
Humidity: {main.get('humidity', 'N/A')}%
Wind: {wind.get('speed', 'N/A')} m/s
Pressure: {main.get('pressure', 'N/A')} hPa
"""
            forecasts.append(forecast)

        result = f"5-Day Weather Forecast for {city_name}:\n" + "\n---\n".join(
            forecasts
        )
        logger.info(f"Successfully retrieved forecast for {city_name}")
        return result

    except Exception as e:
        location = city if city else f"{latitude}, {longitude}"
        logger.error(f"Error getting forecast for {location}: {e}")
        return "Error retrieving forecast. Please try again later."


@mcp.prompt()
def get_initial_prompts() -> list[base.Message]:
    return [
        base.UserMessage(
            "You are a helpful assistant that can help with weather-related questions for India. You can provide current weather conditions and 5-day forecasts for Indian cities."
        )
    ]


def main():
    """Main entry point for weather server."""
    # Validate transport mode
    valid_transports = ["stdio", "sse", "streamable-http"]
    if config.server.transport_mode not in valid_transports:
        logger.error(
            f"Invalid transport mode: {config.server.transport_mode}. "
            f"Must be one of: {valid_transports}"
        )
        return

    logger.info(
        f"Starting weather MCP server: transport={config.server.transport_mode}, "
        f"host={config.server.host}, port={config.server.port}"
    )

    # Run server with configured transport (FastMCP reads host/port from environment variables)
    mcp.run(transport=config.server.transport_mode)


if __name__ == "__main__":
    main()

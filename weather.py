import asyncio
import logging
import os
import signal
import sys
import threading
import time
from typing import Any, Dict, List

import httpx
import uvicorn
from mcp.server import FastMCP, Server
from mcp.server.fastmcp.prompts import base
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

mcp = FastMCP("weather")

OPENWEATHER_API_BASE = "https://api.openweathermap.org/data/2.5"
USER_AGENT = "weather-app/1.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get API key from environment variable
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    logger.warning("OPENWEATHER_API_KEY environment variable not set. Some features may not work.")

# Global variables for shutdown handling
shutdown_requested = False
server_instance = None


def force_shutdown_handler(signum, frame):
    """Immediate shutdown handler that forces process exit."""
    global shutdown_requested
    
    logger.info(f"Received signal {signum}. Forcing immediate shutdown...")
    logger.info("Disconnecting all MCP clients and exiting...")
    
    # Force immediate exit - no graceful shutdown
    os._exit(0)


def setup_aggressive_signal_handlers():
    """Setup signal handlers that will actually exit the process."""
    signal.signal(signal.SIGINT, force_shutdown_handler)
    signal.signal(signal.SIGTERM, force_shutdown_handler)
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, force_shutdown_handler)


async def make_openweather_request(url: str, params: Dict[str, Any] = None) -> Dict[str, Any] | None:
    """Make a request to the OpenWeatherMap API with proper error handling."""
    if not OPENWEATHER_API_KEY:
        logger.error("OpenWeatherMap API key not configured")
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    
    # Add API key to parameters
    if params is None:
        params = {}
    params["appid"] = OPENWEATHER_API_KEY

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
        url = f"{OPENWEATHER_API_BASE}/weather"
        params = {
            "q": f"{city},IN",  # IN is the country code for India
            "units": "metric"   # Use Celsius
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
async def get_forecast(city: str = None, latitude: float = None, longitude: float = None) -> str:
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
                "units": "metric"   # Use Celsius
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
                "units": "metric"   # Use Celsius
            }
        else:
            return "Error: Please provide either a city name or both latitude and longitude coordinates."
        
        # Use OpenWeatherMap 5-day forecast API
        url = f"{OPENWEATHER_API_BASE}/forecast"
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
        for item in data.get("list", [])[:15]:  # Limit to next 5 days (3-hour intervals)
            dt_txt = item.get("dt_txt", "")
            date = dt_txt.split(" ")[0] if dt_txt else "Unknown"
            
            if date not in daily_forecasts:
                daily_forecasts[date] = []
            daily_forecasts[date].append(item)
        
        for date, periods in list(daily_forecasts.items())[:5]:  # Only show next 5 days
            # Get representative data (midday if available, otherwise first available)
            period = periods[len(periods)//2] if periods else periods[0]
            
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

        result = f"5-Day Weather Forecast for {city_name}:\n" + "\n---\n".join(forecasts)
        logger.info(f"Successfully retrieved forecast for {city_name}")
        return result
        
    except Exception as e:
        location = city if city else f"{latitude}, {longitude}"
        logger.error(f"Error getting forecast for {location}: {e}")
        return f"Error retrieving forecast. Please try again later."


@mcp.prompt()
def get_initial_prompts() -> List[base.Message]:
    return [
        base.UserMessage("You are a helpful assistant that can help with weather-related questions for India. You can provide current weather conditions and 5-day forecasts for Indian cities.")
    ]


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        """Handle SSE connections with shutdown awareness."""
        global shutdown_requested
        try:
            logger.info("New SSE connection established")
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
            ) as (read_stream, write_stream):
                # Check for shutdown during connection
                if shutdown_requested:
                    logger.info("Shutdown requested, closing SSE connection")
                    return
                    
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
        except Exception as e:
            logger.error(f"Error in SSE handler: {e}")
            if shutdown_requested:
                logger.info("Error during shutdown - this is expected")
                return
            raise
        finally:
            logger.info("SSE connection closed")

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message)
        ]
    )





def run_server_with_force_exit(host: str, port: int, debug: bool = True):
    """Run server with immediate exit on CTRL+C."""
    
    mcp_server = mcp._mcp_server  # noqa: WPS437
    starlette_app = create_starlette_app(mcp_server, debug=debug)
    
    logger.info(f"Starting weather MCP server on {host}:{port}")
    logger.info("Press CTRL+C to immediately stop the server and disconnect all clients")
    
    # Install signal handlers before starting
    setup_aggressive_signal_handlers()
    
    try:
        # Use simple uvicorn.run - when CTRL+C is pressed, signal handler will os._exit(0)
        uvicorn.run(
            starlette_app,
            host=host,
            port=port,
            log_level="info" if not debug else "debug",
            access_log=True,
            reload=False,
            use_colors=True
        )
    except Exception as e:
        logger.error(f"Server error: {e}")
    
    # This should never be reached due to os._exit(0) in signal handler
    logger.info("Server exiting normally")
    os._exit(0)


def main():
    """Main entry point with immediate exit on CTRL+C."""
    import argparse

    parser = argparse.ArgumentParser(description="Run MCP SSE-based weather server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Run server - signal handler will force exit on CTRL+C
    run_server_with_force_exit(args.host, args.port, args.debug)


if __name__ == "__main__":
    main()

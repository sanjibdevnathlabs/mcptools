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

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


async def make_nws_request(url: str) -> Dict[str, Any] | None:
    """Make a request to the National Weather Service API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug(f"Making request to: {url}")
            response = await client.get(url, headers=headers)
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


def format_alert(feature: dict) -> str:
    props = feature.get("properties", {})

    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    try:
        # Validate state code
        if not state or len(state) != 2:
            return "Error: Please provide a valid two-letter US state code (e.g., CA, NY)."
        
        state = state.upper()
        logger.info(f"Fetching alerts for state: {state}")
        
        url = f"{NWS_API_BASE}/alerts/active/area/{state}"
        data = await make_nws_request(url)

        if not data:
            return f"Unable to fetch alerts for {state}. The weather service may be temporarily unavailable."
        
        if "features" not in data:
            return f"No alert data available for {state}."
            
        if not data["features"]:
            return f"No active alerts for {state}."

        alerts = [format_alert(feature) for feature in data["features"]]
        logger.info(f"Found {len(alerts)} alerts for {state}")
        return "\n---\n".join(alerts)
        
    except Exception as e:
        logger.error(f"Error getting alerts for {state}: {e}")
        return f"Error retrieving alerts for {state}. Please try again later."


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    try:
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            return "Error: Latitude must be between -90 and 90 degrees."
        if not (-180 <= longitude <= 180):
            return "Error: Longitude must be between -180 and 180 degrees."
            
        logger.info(f"Fetching forecast for coordinates: {latitude}, {longitude}")
        
        # First get the forecast grid endpoint
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)

        if not points_data:
            return "Unable to fetch forecast data for this location. The coordinates may be outside the US or the weather service may be unavailable."

        if "properties" not in points_data or "forecast" not in points_data["properties"]:
            return "This location may be outside the US National Weather Service coverage area."

        # Get the forecast URL from the points response
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)

        if not forecast_data:
            return "Unable to fetch detailed forecast. Please try again later."

        if "properties" not in forecast_data or "periods" not in forecast_data["properties"]:
            return "Invalid forecast data received from weather service."

        # Format the periods into a readable forecast
        periods = forecast_data["properties"]["periods"]
        forecasts = []
        for period in periods[:5]:  # Only show next 5 periods
            forecast = f"""
{period.get('name', 'Unknown')}:
Temperature: {period.get('temperature', 'N/A')}°{period.get('temperatureUnit', 'F')}
Wind: {period.get('windSpeed', 'N/A')} {period.get('windDirection', '')}
Forecast: {period.get('detailedForecast', 'No forecast available')}
"""
            forecasts.append(forecast)

        logger.info(f"Successfully retrieved forecast with {len(forecasts)} periods")
        return "\n---\n".join(forecasts)
        
    except Exception as e:
        logger.error(f"Error getting forecast for {latitude}, {longitude}: {e}")
        return f"Error retrieving forecast. Please try again later."


@mcp.prompt()
def get_initial_prompts() -> List[base.Message]:
    return [
        base.UserMessage("You are a helpful assistant that can help with weather-related questions.")
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

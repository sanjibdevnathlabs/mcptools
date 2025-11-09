"""Calculator MCP Server"""

import math

from mcp.server import FastMCP

from calculator.config import Config
from shared.logging import setup_logging

# Initialize config from TOML files
# Config system automatically interpolates ${VAR} with environment variables
config = Config()

# Setup logging using shared logging module
# Pass transport_mode so stdio can be forced to file logging
logger = setup_logging(
    config, "calculator", transport_mode=config.server.transport_mode
)

# Create FastMCP server using configuration
# Pass host/port explicitly so FastMCP doesn't use defaults
mcp = FastMCP(config.app.name, host=config.server.host, port=config.server.port)

# DEFINE TOOLS


# addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return int(a + b)


# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return int(a - b)


# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return int(a * b)


#  division tool
@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    return float(a / b)


# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    return int(a**b)


# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    return float(a**0.5)


# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    return float(a ** (1 / 3))


# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    return int(math.factorial(a))


# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    return float(math.log(a))


# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    return int(a % b)


# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    return float(math.sin(a))


# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    return float(math.cos(a))


# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    return float(math.tan(a))


# define resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    return f"Hello {name}"


def main():
    """
    Main entry point for calculator server.

    Transport mode is configured via environment variables:
    - TRANSPORT_MODE: stdio|sse|streamable-http (default: stdio from default.toml)
    - FASTMCP_HOST: Host to bind for network transports (default: 127.0.0.1)
    - FASTMCP_PORT: Port to bind for network transports (default: 8000)

    These are automatically loaded from environment/*.toml files and interpolated.
    Set APP_ENV to choose environment: dev, test, docker, prod

    Note: FastMCP reads FASTMCP_HOST and FASTMCP_PORT directly from environment.
    """
    transport_mode = config.server.transport_mode

    # Validate transport mode
    valid_transports = ["stdio", "sse", "streamable-http"]
    if transport_mode not in valid_transports:
        logger.error(
            f"Invalid transport_mode: {transport_mode}. "
            f"Must be one of: {', '.join(valid_transports)}"
        )
        raise ValueError(
            f"Invalid transport_mode: {transport_mode}. "
            f"Must be one of: {', '.join(valid_transports)}"
        )

    # Log startup information
    logger.info(f"Starting {config.app.name} MCP Server v{config.app.version}")
    logger.info(f"Environment: {config.app.environment}")
    logger.info(f"Transport mode: {transport_mode}")

    if transport_mode != "stdio":
        logger.info(f"Host: {config.server.host}")
        logger.info(f"Port: {config.server.port}")
        logger.info(f"Server will listen on {config.server.host}:{config.server.port}")

    logger.info("Calculator MCP Server ready to accept connections")

    # FastMCP handles all transports natively
    # Note: FastMCP reads FASTMCP_HOST and FASTMCP_PORT from environment variables
    try:
        mcp.run(transport=transport_mode)
    except Exception as e:
        logger.error(f"Server failed to start: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

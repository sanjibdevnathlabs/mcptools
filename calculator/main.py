import math

from mcp.server import FastMCP

from calculator.config import Config

# Initialize config from TOML files
# Config system automatically interpolates ${VAR} with environment variables
config = Config()

# Create FastMCP server using configuration
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
    return f"Hellp {name}"


async def run_dual_transport():
    """Run both SSE and HTTP transports simultaneously with ops port"""
    import uvicorn
    from calculator.src.transport import DualTransportManager
    
    # Create unified transport manager
    transport_manager = DualTransportManager(
        config=config,
        mcp_server=mcp._mcp_server,
        version="1.0.0"
    )
    
    # Create three separate apps
    sse_app = transport_manager.create_sse_app()
    http_app = transport_manager.create_http_app()
    ops_app = transport_manager.create_ops_app()
    
    # Configure servers
    sse_config = uvicorn.Config(
        sse_app,
        host=str(config.server.host),
        port=8080,
        log_level="info"
    )
    
    http_config = uvicorn.Config(
        http_app,
        host=str(config.server.host),
        port=8081,
        log_level="info"
    )
    
    ops_config = uvicorn.Config(
        ops_app,
        host=str(config.server.host),
        port=9090,
        log_level="info"
    )
    
    # Create servers
    sse_server = uvicorn.Server(sse_config)
    http_server = uvicorn.Server(http_config)
    ops_server = uvicorn.Server(ops_config)
    
    # Run all three servers concurrently
    import asyncio
    await asyncio.gather(
        sse_server.serve(),
        http_server.serve(),
        ops_server.serve(),
    )


def main():
    """Main entry point for calculator server."""
    import os
    import asyncio
    
    # Check transport mode from environment (for E2E tests compatibility)
    transport_mode = os.getenv("TRANSPORT_MODE", "dual").lower()
    
    if transport_mode == "dual":
        # Production mode: Run SSE + HTTP + Admin
        asyncio.run(run_dual_transport())
    else:
        # Test/single mode: Use FastMCP's built-in transport handling (stdio, sse, http)
        mcp.run(transport=transport_mode)


if __name__ == "__main__":
    main()

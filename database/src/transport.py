import logging
import os
import signal
import sys
from typing import Optional

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from database.config import Config

from .database_manager import DatabaseManager
from .logging_config import get_logger

# Temporary fallback logger for functions that don't have access to self.logger
logger = logging.getLogger(__name__)


class TransportManager:
    """Manages both stdio and SSE transport modes for the MCP server."""

    def __init__(
        self,
        mcp_server: Server,
        database_manager: DatabaseManager,
        mcp_server_instance=None,
        fastmcp_server=None,
    ):
        """Initialize transport manager."""
        self.mcp_server = mcp_server
        self.database_manager = database_manager
        self.mcp_server_instance = (
            mcp_server_instance  # Store the DatabaseMCPServer instance
        )
        self.fastmcp_server = fastmcp_server  # Store the FastMCP instance
        self.config = Config()
        self.logger = get_logger("transport")
        self.shutdown_requested = False

    async def run_stdio_transport(self) -> None:
        """Run the MCP server with stdio transport."""
        self.logger.info(
            "TRANSPORT_STDIO_START",
            {"transport_mode": "stdio", "server_name": self.config.mcp.server_name},
        )
        self.logger.info(
            "TRANSPORT_STDIO_READY",
            {"message": "Server ready for uvx/mcp-client connections via stdin/stdout"},
        )

        try:
            # Set up signal handlers for graceful shutdown
            self._setup_stdio_signal_handlers()

            # Initialize the server
            await self.mcp_server_instance.startup()

            # Run the server with stdio transport
            await self.fastmcp_server.run_stdio_async()

        except KeyboardInterrupt:
            self.logger.info(
                "TRANSPORT_STDIO_INTERRUPT",
                {"transport_mode": "stdio", "reason": "keyboard_interrupt"},
            )
        except Exception as e:
            self.logger.error(
                "TRANSPORT_STDIO_ERROR",
                {
                    "transport_mode": "stdio",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise
        finally:
            # Cleanup
            try:
                await self.mcp_server_instance.shutdown()
            except Exception as e:
                self.logger.error(
                    "TRANSPORT_STDIO_SHUTDOWN_ERROR",
                    {"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )
            self.logger.info("TRANSPORT_STDIO_STOPPED", {"transport_mode": "stdio"})

    async def run_sse_transport(self, host: str, port: int) -> None:
        """Run the MCP server with SSE transport via HTTP."""
        self.logger.info(
            "TRANSPORT_SSE_START",
            {
                "transport_mode": "sse",
                "host": host,
                "port": port,
                "endpoint": f"http://{host}:{port}{self.config.server.sse_path}",
            },
        )
        self.logger.info(
            "TRANSPORT_SSE_READY",
            {
                "sse_endpoint": f"http://{host}:{port}{self.config.server.sse_path}",
                "message": "Press CTRL+C to stop the server",
            },
        )

        try:
            # Set up signal handlers for graceful shutdown
            self._setup_sse_signal_handlers()

            # Initialize the server
            await self.mcp_server_instance.startup()

            # Get FastMCP's SSE app with our registered tools
            app = self.fastmcp_server.sse_app()

            # Configure uvicorn to run our app
            uvicorn_config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level="info" if not self.config.server.debug else "debug",
                access_log=True,
                reload=False,
                use_colors=True,
            )

            # Run server with our configured app
            server = uvicorn.Server(uvicorn_config)
            await server.serve()

        except KeyboardInterrupt:
            self.logger.info(
                "TRANSPORT_SSE_INTERRUPT",
                {"transport_mode": "sse", "reason": "keyboard_interrupt"},
            )
        except Exception as e:
            self.logger.error(
                "TRANSPORT_SSE_ERROR",
                {
                    "transport_mode": "sse",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise
        finally:
            # Cleanup
            try:
                await self.mcp_server_instance.shutdown()
            except Exception as e:
                self.logger.error(
                    "TRANSPORT_SSE_SHUTDOWN_ERROR",
                    {"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )
            self.logger.info("TRANSPORT_SSE_STOPPED", {"transport_mode": "sse"})

    async def run_streamable_http_transport(self, host: str, port: int) -> None:
        """Run the MCP server with Streamable HTTP transport."""
        logger.info(
            f"Starting MCP server with Streamable HTTP transport on {host}:{port}"
        )
        logger.info(f"HTTP endpoint: http://{host}:{port}")
        logger.info("Press CTRL+C to stop the server")

        try:
            # Set up signal handlers for graceful shutdown
            self._setup_sse_signal_handlers()

            # Initialize the server
            await self.mcp_server_instance.startup()

            # Get FastMCP's Streamable HTTP app with our registered tools
            app = self.fastmcp_server.streamable_http_app()

            # Configure uvicorn to run our app
            uvicorn_config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level="info" if not self.config.server.debug else "debug",
                access_log=True,
                reload=False,
                use_colors=True,
            )

            # Run server with our configured app
            server = uvicorn.Server(uvicorn_config)
            await server.serve()

        except KeyboardInterrupt:
            logger.info(
                "Received interrupt signal, shutting down Streamable HTTP transport"
            )
        except Exception as e:
            logger.error(f"Error in Streamable HTTP transport: {e}")
            raise
        finally:
            # Cleanup
            try:
                await self.mcp_server_instance.shutdown()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
            logger.info("Streamable HTTP transport stopped")

    def _create_sse_app(self) -> Starlette:
        """Create a Starlette application for SSE transport."""
        sse_transport = SseServerTransport(self.config.server.sse_messages_path)

        async def handle_sse_connection(request: Request):
            """Handle SSE connections with proper error handling."""
            try:
                logger.info("New SSE connection established")

                # Create and return the SSE response using the SSE transport
                return await sse_transport.handle_sse_request(
                    request,
                    lambda read_stream, write_stream: self.mcp_server.run(
                        read_stream,
                        write_stream,
                        self.mcp_server.create_initialization_options(),
                    ),
                )
            except Exception as e:
                logger.error(f"Error in SSE connection handler: {e}")
                if self.shutdown_requested:
                    logger.info("Error during shutdown - this is expected")
                    return JSONResponse(
                        {"error": "Server shutting down"}, status_code=503
                    )
                return JSONResponse({"error": str(e)}, status_code=500)
            finally:
                logger.info("SSE connection closed")

        async def handle_health_check(request: Request) -> JSONResponse:
            """Health check endpoint."""
            try:
                health_status = await self.database_manager.health_check()
                status_code = 200 if health_status["status"] == "healthy" else 503

                return JSONResponse(
                    content={
                        "status": health_status["status"],
                        "service": "database-mcp",
                        "version": self.config.mcp.server_version,
                        "transport": "sse",
                        **health_status,
                    },
                    status_code=status_code,
                )
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return JSONResponse(
                    content={
                        "status": "unhealthy",
                        "service": "database-mcp",
                        "error": str(e),
                    },
                    status_code=503,
                )

        async def handle_metrics(request: Request) -> Response:
            """Metrics endpoint for external monitoring systems."""
            try:
                # Get format from query parameter (default: prometheus)
                format_param = request.query_params.get("format", "prometheus").lower()

                # Access the production monitor from the stored MCP server instance
                if self.mcp_server_instance and hasattr(
                    self.mcp_server_instance, "production_monitor"
                ):
                    monitor = self.mcp_server_instance.production_monitor
                    exported_data = await monitor.get_metrics_export(format_param)

                    if format_param == "prometheus":
                        return Response(
                            content=exported_data,
                            media_type="text/plain; version=0.0.4; charset=utf-8",
                        )
                    else:  # json
                        return Response(
                            content=exported_data, media_type="application/json"
                        )
                else:
                    return JSONResponse(
                        content={"error": "Monitoring not available"}, status_code=503
                    )

            except Exception as e:
                logger.error(f"Metrics endpoint error: {e}")
                return JSONResponse(
                    content={"error": f"Metrics error: {str(e)}"}, status_code=500
                )

        # Create routes
        routes = [
            Route(self.config.server.sse_path, endpoint=handle_sse_connection),
            Mount(
                self.config.server.sse_messages_path,
                app=sse_transport.handle_post_message,
            ),
        ]

        # Add health check route if enabled
        if self.config.server.enable_health_check:
            routes.append(
                Route(
                    self.config.server.health_check_path, endpoint=handle_health_check
                )
            )

        # Add metrics endpoint for monitoring
        routes.append(Route("/metrics", endpoint=handle_metrics))

        # Create Starlette app
        app = Starlette(debug=self.config.server.debug, routes=routes)

        # Add CORS middleware if enabled
        if self.config.server.enable_cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.server.allowed_origins,
                allow_credentials=True,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
            )

        return app

    def _setup_stdio_signal_handlers(self) -> None:
        """Set up signal handlers for stdio mode."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True
            # For stdio, we can just exit gracefully
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, signal_handler)

    def _setup_sse_signal_handlers(self) -> None:
        """Set up signal handlers for SSE mode."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True
            # For SSE mode running in uvicorn, we need a more aggressive approach
            logger.info("Disconnecting all MCP clients and exiting...")
            os._exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, signal_handler)


class AutoTransportManager(TransportManager):
    """Automatically detects and uses the appropriate transport mode."""

    def __init__(
        self,
        mcp_server: Server,
        database_manager: DatabaseManager,
        mcp_server_instance=None,
    ):
        """Initialize auto transport manager."""
        super().__init__(mcp_server, database_manager, mcp_server_instance)

    async def run_auto_transport(self, host: str, port: int) -> None:
        """Automatically detect and run the appropriate transport mode."""
        transport_mode = self._detect_transport_mode()

        logger.info(f"Auto-detected transport mode: {transport_mode}")

        if transport_mode == "stdio":
            await self.run_stdio_transport()
        else:
            await self.run_sse_transport(host, port)

    def _detect_transport_mode(self) -> str:
        """Detect the appropriate transport mode based on environment."""
        # Check if we're being run with stdio pipes
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            return "stdio"

        # Check if we're in a uvx/mcp environment
        if os.getenv("MCP_TRANSPORT") == "stdio":
            return "stdio"

        # Check if we have explicit environment variables for SSE
        if os.getenv("MCP_TRANSPORT") == "sse":
            return "sse"

        # Default to SSE for interactive use
        return "sse"


def create_transport_manager(
    mcp_server: Server,
    database_manager: DatabaseManager,
    mcp_server_instance=None,
    fastmcp_server=None,
) -> TransportManager:
    """Factory function to create the appropriate transport manager."""
    config = Config()

    if config.server.transport_mode == "auto":
        return AutoTransportManager(
            mcp_server, database_manager, mcp_server_instance, fastmcp_server
        )
    else:
        return TransportManager(
            mcp_server, database_manager, mcp_server_instance, fastmcp_server
        )


async def run_transport(
    mcp_server: Server,
    database_manager: DatabaseManager,
    host: Optional[str] = None,
    port: Optional[int] = None,
    mcp_server_instance=None,
    fastmcp_server=None,
) -> None:
    """
    Run the MCP server with the configured transport mode.

    Args:
        mcp_server: The MCP server instance
        database_manager: The database manager instance
        host: Host for SSE mode (optional, uses config default)
        port: Port for SSE mode (optional, uses config default)
        mcp_server_instance: The DatabaseMCPServer instance for monitoring access
    """
    config = Config()
    transport_manager = create_transport_manager(
        mcp_server, database_manager, mcp_server_instance, fastmcp_server
    )

    # Use provided host/port or config defaults
    host = host or config.server.host
    port = port or config.server.port

    if config.server.transport_mode == "stdio":
        await transport_manager.run_stdio_transport()
    elif config.server.transport_mode == "sse":
        await transport_manager.run_sse_transport(host, port)
    elif config.server.transport_mode == "streamable-http":
        await transport_manager.run_streamable_http_transport(host, port)
    elif config.server.transport_mode == "auto":
        await transport_manager.run_auto_transport(host, port)
    else:
        raise ValueError(f"Unknown transport mode: {config.server.transport_mode}")

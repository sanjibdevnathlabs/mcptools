"""
Transport layer for Calculator MCP Server.

Handles both SSE and HTTP transports with dedicated admin port for health/metrics.
"""

import logging
import asyncio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, Mount
from mcp.server import Server
from mcp.server.sse import SseServerTransport

logger = logging.getLogger(__name__)


class DualTransportManager:
    """Manages both SSE and HTTP transports with unified health/metrics"""

    def __init__(self, config, mcp_server: Server, version: str = "1.0.0"):
        self.config = config
        self.mcp_server = mcp_server
        self.version = version
        # Transports start as healthy (will be set to False only on errors)
        self.sse_healthy = True
        self.http_healthy = True

    async def handle_health_check(self, request: Request) -> JSONResponse:
        """
        Unified health check for both transports.
        Returns 200 if all transports are healthy, 503 if any are unhealthy.
        """
        try:
            overall_healthy = self.sse_healthy and self.http_healthy
            
            response_data = {
                "healthy": overall_healthy,
                "service": "calculator-mcp",
                "version": self.version,
                "transports": {
                    "sse": {"healthy": self.sse_healthy},
                    "http": {"healthy": self.http_healthy}
                }
            }
            
            status_code = 200 if overall_healthy else 503
            return JSONResponse(content=response_data, status_code=status_code)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return JSONResponse(
                content={
                    "healthy": False,
                    "service": "calculator-mcp",
                    "error": str(e),
                },
                status_code=503,
            )

    async def handle_metrics(self, request: Request) -> Response:
        """
        Unified metrics endpoint for both transports (Prometheus format).
        Metrics include cardinality by transport type.
        """
        # Placeholder for future Prometheus metrics implementation
        metrics = """# Prometheus metrics endpoint
# TODO: Implement production metrics with transport labels
# Example: calculator_mcp_requests_total{transport="sse"} 150
# Example: calculator_mcp_requests_total{transport="http"} 300
"""
        return Response(
            content=metrics,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    def create_sse_app(self) -> Starlette:
        """Create Starlette app for SSE transport (port 8080)"""
        sse_transport = SseServerTransport("/messages/")

        async def handle_sse(request: Request):
            """Handle SSE connections"""
            try:
                logger.info("New SSE connection established")
                async with sse_transport.connect_sse(
                    request.scope,
                    request.receive,
                    request._send,
                ) as (read_stream, write_stream):
                    await self.mcp_server.run(
                        read_stream,
                        write_stream,
                        self.mcp_server.create_initialization_options(),
                    )
            except Exception as e:
                logger.error(f"SSE error: {e}")
                self.sse_healthy = False
                raise
            finally:
                logger.info("SSE connection closed")

        # SSE routes - only MCP traffic
        routes = [
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse_transport.handle_post_message),
        ]

        return Starlette(debug=True, routes=routes)

    def create_http_app(self) -> Starlette:
        """Create HTTP transport app (port 8081)"""
        from mcp.server.streamable_http import StreamableHTTPServerTransport
        
        # Create the HTTP transport - it will handle /mcp internally
        http_transport = StreamableHTTPServerTransport("/mcp")
        
        # Wrap the transport to add logging and error handling
        async def http_asgi_app(scope, receive, send):
            """ASGI wrapper for HTTP transport with logging"""
            try:
                if scope["type"] == "http":
                    logger.info(f"HTTP MCP request: {scope['method']} {scope['path']}")
                
                # Delegate to the transport's handle_request
                await http_transport.handle_request(scope, receive, send)
                
            except Exception as e:
                logger.error(f"HTTP MCP error: {e}", exc_info=True)
                self.http_healthy = False
                
                # Send error response using raw ASGI
                if scope["type"] == "http":
                    await send({
                        'type': 'http.response.start',
                        'status': 500,
                        'headers': [[b'content-type', b'text/plain']],
                    })
                    await send({
                        'type': 'http.response.body',
                        'body': f"MCP Error: {str(e)}".encode('utf-8'),
                    })
        
        # Return the raw ASGI app wrapped in Starlette
        # Starlette will handle routing this to all paths
        return http_asgi_app

    def create_ops_app(self) -> Starlette:
        """Create ops app for health and metrics (port 9090)"""
        routes = [
            Route("/health", endpoint=self.handle_health_check),
            Route("/metrics", endpoint=self.handle_metrics),
        ]

        return Starlette(debug=True, routes=routes)

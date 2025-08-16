#!/usr/bin/env python3
"""
Database MCP Server - Main Entry Point

A production-grade Model Context Protocol (MCP) server for MySQL database interactions.
Supports both stdio and SSE transport modes with comprehensive security and monitoring.

Usage:
    # Stdio mode (for uvx/mcp-client)
    python -m database --transport stdio
    
    # SSE mode (HTTP server)
    python -m database --transport sse --host 0.0.0.0 --port 8080
    
    # Auto-detect mode
    python -m database --transport auto
"""

import argparse
import asyncio
import sys
from typing import Optional

from .config import get_config, reload_config
from .server import DatabaseMCPServer
from .transport import run_transport
from .logging_config import setup_logging, get_logger, generate_trace_id

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Database MCP Server - MySQL database operations via MCP protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --transport stdio                    # Run with stdio transport
  %(prog)s --transport sse                      # Run with SSE transport on default host:port
  %(prog)s --transport sse --host 0.0.0.0 --port 3000  # SSE with custom host:port
  %(prog)s --transport auto                     # Auto-detect transport mode
  %(prog)s --config-check                       # Validate configuration only
        """
    )
    
    # Transport options
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse", "streamable-http", "auto"],
        default=None,
        help="Transport mode (overrides config setting)"
    )
    
    # Testing options
    parser.add_argument(
        "--test-tools",
        action="store_true",
        help="Enter CLI testing mode to test tools directly"
    )
    
    parser.add_argument(
        "--test-query",
        type=str,
        help="Execute a specific SQL query in test mode"
    )
    
    # Server options (for SSE mode)
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to for SSE mode (overrides config)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on for SSE mode (overrides config)"
    )
    
    # Debug and logging
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (overrides config)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Set log level (overrides config)"
    )
    
    # Configuration
    parser.add_argument(
        "--config-check",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--config-reload",
        action="store_true",
        help="Reload configuration from environment"
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="Database MCP Server 1.0.0"
    )
    
    return parser

def validate_configuration() -> bool:
    """Validate configuration and return success status."""
    try:
        config = get_config()
        print("✅ Configuration validation successful")
        print(f"📊 Database: {config.get_database_dsn()}")
        print(f"🚀 Transport: {config.server.transport_mode}")
        print(f"🛡️  Security: {'Read-only' if config.mcp.readonly_mode else 'Full access'}")
        print(f"⚡ Rate limiting: {'Enabled' if config.mcp.enable_rate_limiting else 'Disabled'}")
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

async def cli_test_mode(test_query: str = None):
    """CLI testing mode to test tools directly without transport."""
    # Setup logging for CLI test mode
    config = get_config()
    loggers = setup_logging(config)
    logger = loggers['main']
    trace_id = generate_trace_id()
    
    logger.info("CLI_TEST_START", {"trace_id": trace_id, "test_query": test_query})
    
    try:
        # Create server instance
        logger.info("CLI_SERVER_CREATE", {})
        server = DatabaseMCPServer()
        
        # Initialize database
        logger.info("CLI_DATABASE_INIT", {})
        await server.startup()
        
        # List available tools
        tools = await server.mcp.list_tools()
        tool_list = [{"name": tool.name, "description": tool.description or "No description"} for tool in tools]
        logger.info("CLI_TOOLS_LIST", {"tool_count": len(tools), "tools": tool_list})
        
        if test_query:
            # Execute specific query
            logger.info("CLI_QUERY_EXECUTE", {"query": test_query})
            try:
                # Find execute_query tool
                execute_tool = None
                for tool in tools:
                    if tool.name == "execute_query":
                        execute_tool = tool
                        break
                
                if execute_tool:
                    # Call the tool directly
                    result = await server.mcp.call_tool(execute_tool.name, {"sql": test_query})
                    logger.info("CLI_QUERY_SUCCESS", {"result": result})
                    print(f"\n✅ Query executed successfully!")
                    print(f"Result: {result}")
                else:
                    logger.error("CLI_TOOL_NOT_FOUND", {"tool_name": "execute_query"})
                    print("❌ execute_query tool not found!")
                    
            except Exception as e:
                logger.error("CLI_QUERY_ERROR", {"error": str(e), "error_type": type(e).__name__}, exc_info=True)
                print(f"❌ Error: {e}")
        
        else:
            # Interactive mode
            print("\n🔧 CLI Testing Mode")
            print("Available tools:")
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool.name}")
            
            while True:
                print("\nOptions:")
                print("1. Test execute_query tool")
                print("2. List tools again")  
                print("3. Exit")
                
                choice = input("Enter choice (1-3): ").strip()
                
                if choice == "1":
                    sql = input("Enter SQL query: ").strip()
                    if sql:
                        try:
                            result = await server.mcp.call_tool("execute_query", {"sql": sql})
                            print(f"✅ Result: {result}")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                            logger.error("CLI_INTERACTIVE_ERROR", {"error": str(e), "error_type": type(e).__name__}, exc_info=True)
                
                elif choice == "2":
                    tools = await server.mcp.list_tools()
                    print(f"Available tools: {len(tools)}")
                    for i, tool in enumerate(tools, 1):
                        print(f"  {i}. {tool.name}")
                
                elif choice == "3":
                    break
                
                else:
                    print("Invalid choice!")
    
    except Exception as e:
        logger.error("CLI_TEST_ERROR", {"error": str(e), "error_type": type(e).__name__}, exc_info=True)
        print(f"❌ CLI test failed: {e}")
        raise
    
    finally:
        try:
            await server.shutdown()
            logger.info("CLI_TEST_COMPLETE", {})
        except:
            pass


async def run_server(
    transport_mode: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    debug: Optional[bool] = None,
    log_level: Optional[str] = None
) -> None:
    """Run the database MCP server with the specified options."""
    try:
        # Get configuration (reload if requested)
        config = get_config()
        
        # Override config with command line arguments
        if transport_mode:
            config.server.transport_mode = transport_mode
        if host:
            config.server.host = host
        if port:
            config.server.port = port
        if debug is not None:
            config.server.debug = debug
        if log_level:
            config.server.log_level = log_level
        
        # Set up logging with new system
        loggers = setup_logging(config)
        logger = loggers['main']
        
        # Generate trace ID for this server session
        trace_id = generate_trace_id()
        
        logger.info("SERVER_STARTING", {
            "trace_id": trace_id,
            "transport_mode": config.server.transport_mode,
            "database_dsn": config.get_database_dsn(),
            "log_format": config.server.log_format,
            "log_destination": config.server.log_destination
        })
        
        # Create and initialize the MCP server
        mcp_server_instance = DatabaseMCPServer()
        mcp_server = mcp_server_instance.get_server()
        fastmcp_server = mcp_server_instance.get_fastmcp()
        database_manager = mcp_server_instance.database_manager
        
        # Run the transport with monitoring support
        await run_transport(
            mcp_server,
            database_manager,
            host=config.server.host,
            port=config.server.port,
            mcp_server_instance=mcp_server_instance,
            fastmcp_server=fastmcp_server
        )
        
    except KeyboardInterrupt:
        logger.info("SERVER_SHUTDOWN_KEYBOARD", {"reason": "keyboard_interrupt"})
    except Exception as e:
        logger.error("SERVER_ERROR", {"error": str(e), "error_type": type(e).__name__}, exc_info=True)
        raise

def main() -> None:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle configuration reload
    if args.config_reload:
        try:
            reload_config()
            print("✅ Configuration reloaded successfully")
        except Exception as e:
            print(f"❌ Failed to reload configuration: {e}")
            sys.exit(1)
    
    # Handle configuration check
    if args.config_check:
        success = validate_configuration()
        sys.exit(0 if success else 1)
    
    # Handle test modes
    if args.test_tools or args.test_query:
        try:
            asyncio.run(cli_test_mode(args.test_query))
            sys.exit(0)
        except KeyboardInterrupt:
            print("\n👋 CLI test stopped")
            sys.exit(0)
        except Exception as e:
            print(f"❌ CLI test failed: {e}")
            sys.exit(1)
    
    # Run the server
    try:
        asyncio.run(run_server(
            transport_mode=args.transport,
            host=args.host,
            port=args.port,
            debug=args.debug,
            log_level=args.log_level
        ))
    except KeyboardInterrupt:
        print("\n👋 Database MCP Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

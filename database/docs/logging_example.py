#!/usr/bin/env python3
"""
Example demonstrating the new trace code logging system.

This shows how to use the structured JSON logging with trace codes
for better debugging and monitoring in production environments.
"""

import asyncio

from .config import get_config
from .logging_config import generate_trace_id, setup_logging


async def example_usage():
    """Example showing different logging patterns."""

    # Setup logging
    config = get_config()
    loggers = setup_logging(config)

    # Get logger for this module
    logger = loggers["main"]

    # Generate a trace ID for this operation
    trace_id = generate_trace_id()
    print(f"Generated trace ID: {trace_id}")

    # Basic logging with trace codes
    logger.info("EXAMPLE_START", {"operation": "demo", "user_id": "user123"})

    # Logging with different levels
    logger.debug("DEBUG_TRACE", {"step": 1, "data": {"key": "value"}})

    logger.warning("WARNING_TRACE", {"issue": "non_critical_problem", "retry_count": 3})

    try:
        # Simulate an operation that might fail
        pass
    except Exception as e:
        logger.error(
            "ERROR_TRACE",
            {
                "operation": "division",
                "error": str(e),
                "inputs": {"dividend": 10, "divisor": 0},
            },
            exc_info=True,
        )

    # Success logging
    logger.info(
        "OPERATION_SUCCESS",
        {"operation": "demo", "duration_ms": 150, "result_count": 42},
    )

    # Different trace ID for a new operation
    new_trace_id = generate_trace_id()
    logger.info(
        "NEW_OPERATION",
        {
            "previous_trace_id": trace_id,
            "new_trace_id": new_trace_id,
            "operation": "follow_up",
        },
    )


def main():
    """Run the example."""
    print("🔍 Database MCP Logging Example")
    print("=" * 50)
    print()
    print("This example demonstrates:")
    print("- JSON structured logging")
    print("- Trace code based messages")
    print("- Automatic trace ID generation")
    print("- Exception handling with context")
    print()

    asyncio.run(example_usage())

    print()
    print("✅ Example completed!")
    print("📄 Check the log file for JSON formatted output")


if __name__ == "__main__":
    main()

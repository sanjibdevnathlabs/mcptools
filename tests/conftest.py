"""Shared fixtures for E2E tests

This file contains shared fixtures and utilities used across all E2E test files.

Note: Protocol-specific fixtures (STDIO, SSE, streamable-http) are defined
in individual test files (e.g., test_e2e_calculator.py) to keep them focused
and maintainable.
"""

import os

import pytest

# ============================================================================
# Test Database Setup (for database E2E tests)
# ============================================================================


@pytest.fixture(scope="session")
def test_database_config():
    """Provide test database configuration for E2E tests"""
    return {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "port": int(os.getenv("TEST_DB_PORT", "3306")),
        "user": os.getenv("TEST_DB_USER", "root"),
        "password": os.getenv("TEST_DB_PASSWORD", "root"),
        "database": os.getenv("TEST_DB_DATABASE", "mcp_test"),
    }


# ============================================================================
# Weather API Configuration (for weather E2E tests)
# ============================================================================


@pytest.fixture(scope="session")
def weather_api_config():
    """Provide weather API configuration for E2E tests"""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        pytest.skip("OPENWEATHER_API_KEY not set - skipping weather E2E tests")
    return {"api_key": api_key}

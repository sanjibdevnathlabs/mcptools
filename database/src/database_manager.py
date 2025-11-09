import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

import aiomysql

from database.config import Config

from .logging_config import get_logger


class DatabaseManager:
    """Enhanced database manager with connection pooling, query execution, and schema introspection."""

    def __init__(self):
        """Initialize the database manager."""
        self.config = Config()
        self.logger = get_logger("database")
        self.pool: Optional[aiomysql.Pool] = None
        self.connection_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "pool_created_at": None,
            "last_query_at": None,
        }

    async def initialize_pool(self) -> None:
        """Initialize the asynchronous connection pool for MySQL."""
        if self.pool:
            self.logger.warning(
                "POOL_ALREADY_INITIALIZED", {"dsn": self.config.get_database_dsn()}
            )
            return

        try:
            connection_params = self.config.get_connection_params()
            self.logger.info(
                "POOL_INIT_START",
                {
                    "dsn": self.config.get_database_dsn(),
                    "min_size": connection_params.get("minsize"),
                    "max_size": connection_params.get("maxsize"),
                },
            )

            self.pool = await aiomysql.create_pool(
                **connection_params, loop=asyncio.get_event_loop()
            )

            self.connection_stats["pool_created_at"] = time.time()
            self.logger.info(
                "POOL_INIT_SUCCESS",
                {
                    "dsn": self.config.get_database_dsn(),
                    "created_at": self.connection_stats["pool_created_at"],
                },
            )

            # Test the connection
            await self._test_connection()

        except Exception as e:
            self.logger.error(
                "POOL_INIT_FAILED",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "dsn": self.config.get_database_dsn(),
                },
                exc_info=True,
            )
            raise

    async def _test_connection(self) -> None:
        """Test the database connection."""
        try:
            async with self.pool.acquire() as conn, conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                if result[0] != 1:
                    raise Exception("Connection test failed")
            self.logger.info(
                "CONNECTION_TEST_SUCCESS", {"dsn": self.config.get_database_dsn()}
            )
        except Exception as e:
            self.logger.error(
                "CONNECTION_TEST_FAILED",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "dsn": self.config.get_database_dsn(),
                },
                exc_info=True,
            )
            raise

    async def close_pool(self) -> None:
        """Close the asynchronous connection pool."""
        if self.pool:
            try:
                self.pool.close()
                await self.pool.wait_closed()
                self.logger.info(
                    "POOL_CLOSE_SUCCESS", {"dsn": self.config.get_database_dsn()}
                )
                self.pool = None
            except Exception as e:
                self.logger.error(
                    "POOL_CLOSE_FAILED",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "dsn": self.config.get_database_dsn(),
                    },
                    exc_info=True,
                )
                raise

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool with automatic cleanup."""
        # Lazy initialization of connection pool
        if not self.pool:
            await self.initialize_pool()

        conn = None
        try:
            conn = await self.pool.acquire()
            yield conn
        finally:
            if conn:
                self.pool.release(conn)

    async def execute_query(
        self,
        sql: str,
        params: Optional[list[Any]] = None,
        fetch_results: bool = True,
        max_rows: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Execute a SQL query with comprehensive error handling and monitoring.

        Args:
            sql: SQL query string
            params: Query parameters
            fetch_results: Whether to fetch results for SELECT queries
            max_rows: Maximum number of rows to fetch (overrides config default)

        Returns:
            Dictionary with query results and metadata
        """
        # Lazy initialization of connection pool
        if not self.pool:
            await self.initialize_pool()

        # Validate query length
        if len(sql) > self.config.database.max_query_length:
            return {
                "success": False,
                "error": f"Query length exceeds maximum allowed ({self.config.database.max_query_length} characters)",
                "error_code": "QUERY_TOO_LONG",
            }

        start_time = time.time()
        query_id = f"query_{int(start_time * 1000)}"

        self.logger.info(
            "QUERY_EXECUTE_START",
            {
                "query_id": query_id,
                "sql_preview": sql[:100] + ("..." if len(sql) > 100 else ""),
                "sql_length": len(sql),
                "has_params": bool(params),
            },
        )

        try:
            async with self.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Set query timeout (MySQL 5.7.8+ only, ignore if not supported)
                    try:
                        await cursor.execute(
                            f"SET SESSION max_execution_time = {int(self.config.database.query_timeout * 1000)}"
                        )
                    except aiomysql.Error as e:
                        # Ignore if max_execution_time is not supported (older MySQL/MariaDB)
                        if "Unknown system variable" not in str(e):
                            raise

                    # Execute the main query
                    await cursor.execute(sql, params or [])

                    results = []
                    affected_rows = 0

                    # Handle results based on query type
                    if cursor.description:
                        # SELECT-like queries - fetch results
                        if fetch_results:
                            max_fetch = max_rows or self.config.database.max_rows_limit
                            results = await cursor.fetchmany(max_fetch)

                            # Check if there are more rows
                            more_rows_available = False
                            if len(results) == max_fetch:
                                # Try to fetch one more row to see if limit was reached
                                extra_row = await cursor.fetchone()
                                if extra_row:
                                    more_rows_available = True

                            results = [
                                dict(row) for row in results
                            ]  # Convert to regular dicts
                    else:
                        # INSERT, UPDATE, DELETE, etc.
                        affected_rows = cursor.rowcount
                        await conn.commit()

                    execution_time = time.time() - start_time
                    self.connection_stats["total_queries"] += 1
                    self.connection_stats["successful_queries"] += 1
                    self.connection_stats["last_query_at"] = time.time()

                    self.logger.info(
                        "QUERY_EXECUTE_SUCCESS",
                        {
                            "query_id": query_id,
                            "execution_time": execution_time,
                            "row_count": len(results) if results else affected_rows,
                            "affected_rows": affected_rows,
                            "has_results": bool(cursor.description),
                        },
                    )

                    response = {
                        "success": True,
                        "data": results,
                        "metadata": {
                            "query_id": query_id,
                            "execution_time": execution_time,
                            "row_count": len(results) if results else affected_rows,
                            "affected_rows": affected_rows,
                            "has_results": bool(cursor.description),
                            "more_rows_available": (
                                more_rows_available
                                if "more_rows_available" in locals()
                                else False
                            ),
                        },
                    }

                    return response

        except aiomysql.Error as e:
            execution_time = time.time() - start_time
            self.connection_stats["total_queries"] += 1
            self.connection_stats["failed_queries"] += 1

            self.logger.error(
                "QUERY_MYSQL_ERROR",
                {
                    "query_id": query_id,
                    "execution_time": execution_time,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "mysql_errno": (
                        getattr(e, "args", [None])[0] if hasattr(e, "args") else None
                    ),
                    "sql_preview": sql[:100] + ("..." if len(sql) > 100 else ""),
                },
                exc_info=True,
            )

            # Attempt rollback
            try:
                async with self.get_connection() as conn:
                    await conn.rollback()
            except Exception as rollback_error:
                self.logger.error(
                    "QUERY_ROLLBACK_FAILED",
                    {
                        "query_id": query_id,
                        "rollback_error": str(rollback_error),
                        "original_error": str(e),
                    },
                    exc_info=True,
                )

            return {
                "success": False,
                "error": str(e),
                "error_code": "MYSQL_ERROR",
                "metadata": {
                    "query_id": query_id,
                    "execution_time": execution_time,
                    "mysql_errno": (
                        getattr(e, "args", [None])[0] if hasattr(e, "args") else None
                    ),
                },
            }

        except TimeoutError:
            execution_time = time.time() - start_time
            self.connection_stats["total_queries"] += 1
            self.connection_stats["failed_queries"] += 1

            self.logger.error(
                "QUERY_TIMEOUT",
                {
                    "query_id": query_id,
                    "execution_time": execution_time,
                    "timeout_limit": self.config.database.query_timeout,
                    "sql_preview": sql[:100] + ("..." if len(sql) > 100 else ""),
                },
            )

            return {
                "success": False,
                "error": f"Query timeout after {self.config.database.query_timeout} seconds",
                "error_code": "QUERY_TIMEOUT",
                "metadata": {"query_id": query_id, "execution_time": execution_time},
            }

        except Exception as e:
            execution_time = time.time() - start_time
            self.connection_stats["total_queries"] += 1
            self.connection_stats["failed_queries"] += 1

            self.logger.error(
                "QUERY_UNEXPECTED_ERROR",
                {
                    "query_id": query_id,
                    "execution_time": execution_time,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "sql_preview": sql[:100] + ("..." if len(sql) > 100 else ""),
                },
                exc_info=True,
            )

            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_code": "UNEXPECTED_ERROR",
                "metadata": {"query_id": query_id, "execution_time": execution_time},
            }

    async def get_schema_info(
        self, database_name: Optional[str] = None
    ) -> dict[str, Any]:
        """Get database schema information."""
        try:
            if database_name:
                # Get specific database info
                query = """
                SELECT
                    TABLE_NAME as table_name,
                    TABLE_TYPE as table_type,
                    TABLE_COMMENT as table_comment
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
                """
                result = await self.execute_query(query, [database_name])
            else:
                # Get all databases
                query = "SHOW DATABASES"
                result = await self.execute_query(query)

            return result
        except Exception as e:
            self.logger.error(
                "SCHEMA_INFO_FAILED",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "database_name": database_name,
                },
                exc_info=True,
            )
            return {"success": False, "error": str(e), "error_code": "SCHEMA_ERROR"}

    async def get_table_info(
        self, table_name: str, database_name: Optional[str] = None
    ) -> dict[str, Any]:
        """Get detailed information about a specific table."""
        try:
            db_clause = f"AND TABLE_SCHEMA = '{database_name}'" if database_name else ""

            query = f"""
            SELECT
                COLUMN_NAME as column_name,
                DATA_TYPE as data_type,
                IS_NULLABLE as is_nullable,
                COLUMN_DEFAULT as column_default,
                COLUMN_COMMENT as column_comment,
                EXTRA as extra
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = %s {db_clause}
            ORDER BY ORDINAL_POSITION
            """

            params = [table_name]
            result = await self.execute_query(query, params)

            return result
        except Exception as e:
            self.logger.error(
                "TABLE_INFO_FAILED",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "table_name": table_name,
                    "database_name": database_name,
                },
                exc_info=True,
            )
            return {"success": False, "error": str(e), "error_code": "TABLE_INFO_ERROR"}

    async def explain_query(
        self, sql: str, params: Optional[list[Any]] = None
    ) -> dict[str, Any]:
        """Get query execution plan using EXPLAIN."""
        try:
            explain_sql = f"EXPLAIN {sql}"
            result = await self.execute_query(explain_sql, params)
            return result
        except Exception as e:
            self.logger.error(
                "EXPLAIN_QUERY_FAILED",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "sql_preview": sql[:100] + ("..." if len(sql) > 100 else ""),
                },
                exc_info=True,
            )
            return {"success": False, "error": str(e), "error_code": "EXPLAIN_ERROR"}

    async def get_connection_stats(self) -> dict[str, Any]:
        """Get connection pool and query statistics."""
        pool_info = {}
        if self.pool:
            pool_info = {
                "pool_size": self.pool.size,
                "pool_free_size": self.pool.freesize,
                "pool_min_size": self.pool.minsize,
                "pool_max_size": self.pool.maxsize,
            }

        return {
            **self.connection_stats,
            **pool_info,
            "pool_initialized": self.pool is not None,
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on the database connection."""
        try:
            start_time = time.time()
            result = await self.execute_query(
                "SELECT 1 as health_check, NOW() as server_time"
            )

            if result.get("success"):
                health_status = "healthy"
                response_time = time.time() - start_time
            else:
                health_status = "unhealthy"
                response_time = None

            return {
                "status": health_status,
                "response_time": response_time,
                "database_time": (
                    result.get("data", [{}])[0].get("server_time")
                    if result.get("success")
                    else None
                ),
                "connection_stats": await self.get_connection_stats(),
            }

        except Exception as e:
            self.logger.error(
                "HEALTH_CHECK_FAILED",
                {"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": None,
                "connection_stats": await self.get_connection_stats(),
            }

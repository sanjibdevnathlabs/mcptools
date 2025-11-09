import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from database.config import Config

from .error_handling import DatabaseConnectionError, DatabaseQueryError, ValidationError
from .logging_config import get_logger


class SchemaObjectType(Enum):
    """Types of database schema objects."""

    DATABASE = "database"
    TABLE = "table"
    VIEW = "view"
    COLUMN = "column"
    INDEX = "index"
    CONSTRAINT = "constraint"
    TRIGGER = "trigger"
    PROCEDURE = "procedure"
    FUNCTION = "function"


class ColumnType(Enum):
    """Simplified column types for cross-database compatibility."""

    INTEGER = "integer"
    BIGINT = "bigint"
    DECIMAL = "decimal"
    FLOAT = "float"
    DOUBLE = "double"
    VARCHAR = "varchar"
    TEXT = "text"
    CHAR = "char"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    TIMESTAMP = "timestamp"
    BOOLEAN = "boolean"
    JSON = "json"
    BLOB = "blob"
    BINARY = "binary"
    ENUM = "enum"
    SET = "set"
    UNKNOWN = "unknown"


@dataclass
class DatabaseInfo:
    """Information about a database."""

    name: str
    character_set: Optional[str] = None
    collation: Optional[str] = None
    size_bytes: Optional[int] = None
    table_count: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class ColumnInfo:
    """Detailed information about a table column."""

    name: str
    data_type: str
    column_type: ColumnType
    is_nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_auto_increment: bool = False
    is_unsigned: bool = False
    character_maximum_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    column_comment: Optional[str] = None
    ordinal_position: int = 0
    extra: Optional[str] = None


@dataclass
class IndexInfo:
    """Information about a table index."""

    name: str
    table_name: str
    column_names: list[str]
    is_unique: bool = False
    is_primary: bool = False
    index_type: str = "BTREE"
    is_fulltext: bool = False
    comment: Optional[str] = None


@dataclass
class ConstraintInfo:
    """Information about a table constraint."""

    name: str
    table_name: str
    constraint_type: str  # PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK
    column_names: list[str]
    referenced_table: Optional[str] = None
    referenced_columns: Optional[list[str]] = None
    on_delete: Optional[str] = None
    on_update: Optional[str] = None
    check_clause: Optional[str] = None


@dataclass
class TableInfo:
    """Comprehensive information about a table."""

    name: str
    database_name: str
    table_type: str = "BASE TABLE"  # BASE TABLE, VIEW, SYSTEM VIEW
    engine: Optional[str] = None
    row_format: Optional[str] = None
    table_rows: Optional[int] = None
    avg_row_length: Optional[int] = None
    data_length: Optional[int] = None
    index_length: Optional[int] = None
    data_free: Optional[int] = None
    auto_increment: Optional[int] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    check_time: Optional[datetime] = None
    table_collation: Optional[str] = None
    checksum: Optional[int] = None
    create_options: Optional[str] = None
    table_comment: Optional[str] = None
    columns: list[ColumnInfo] = field(default_factory=list)
    indexes: list[IndexInfo] = field(default_factory=list)
    constraints: list[ConstraintInfo] = field(default_factory=list)


@dataclass
class SchemaSnapshot:
    """Complete schema snapshot at a point in time."""

    timestamp: datetime
    databases: dict[str, DatabaseInfo]
    tables: dict[str, TableInfo]  # key: "database.table"
    schema_hash: str
    mysql_version: Optional[str] = None
    server_info: Optional[dict[str, Any]] = None


class SchemaAnalyzer:
    """Analyzes database schemas for issues and recommendations."""

    def __init__(self):
        """Initialize schema analyzer."""
        self.config = Config()

    def analyze_table(self, table_info: TableInfo) -> dict[str, Any]:
        """Analyze a table for potential issues and recommendations."""
        issues = []
        recommendations = []
        metrics = {}

        # Analyze columns
        primary_keys = [col for col in table_info.columns if col.is_primary_key]
        nullable_columns = [col for col in table_info.columns if col.is_nullable]
        text_columns = [
            col
            for col in table_info.columns
            if col.column_type in [ColumnType.TEXT, ColumnType.VARCHAR]
        ]

        metrics.update(
            {
                "column_count": len(table_info.columns),
                "primary_key_count": len(primary_keys),
                "nullable_column_count": len(nullable_columns),
                "text_column_count": len(text_columns),
                "index_count": len(table_info.indexes),
                "constraint_count": len(table_info.constraints),
            }
        )

        # Check for missing primary key
        if not primary_keys:
            issues.append(
                {
                    "type": "missing_primary_key",
                    "severity": "high",
                    "message": f"Table {table_info.name} has no primary key",
                    "recommendation": "Add a primary key for better performance and replication support",
                }
            )

        # Check for too many columns
        if len(table_info.columns) > 50:
            issues.append(
                {
                    "type": "too_many_columns",
                    "severity": "medium",
                    "message": f"Table {table_info.name} has {len(table_info.columns)} columns",
                    "recommendation": "Consider normalizing the table structure",
                }
            )

        # Check for missing indexes on foreign key columns
        foreign_key_columns = set()
        for constraint in table_info.constraints:
            if constraint.constraint_type == "FOREIGN KEY":
                foreign_key_columns.update(constraint.column_names)

        indexed_columns = set()
        for index in table_info.indexes:
            indexed_columns.update(index.column_names)

        unindexed_fk_columns = foreign_key_columns - indexed_columns
        if unindexed_fk_columns:
            issues.append(
                {
                    "type": "unindexed_foreign_keys",
                    "severity": "medium",
                    "message": f"Foreign key columns without indexes: {list(unindexed_fk_columns)}",
                    "recommendation": "Add indexes on foreign key columns for better join performance",
                }
            )

        # Check for large VARCHAR columns
        large_varchar_columns = [
            col
            for col in table_info.columns
            if col.column_type == ColumnType.VARCHAR
            and col.character_maximum_length
            and col.character_maximum_length > 1000
        ]
        if large_varchar_columns:
            col_names = [col.name for col in large_varchar_columns]
            recommendations.append(
                {
                    "type": "large_varchar_optimization",
                    "message": f"Consider using TEXT type for large VARCHAR columns: {col_names}",
                    "impact": "Storage and performance optimization",
                }
            )

        # Check table size metrics
        if table_info.table_rows and table_info.table_rows > 1000000:
            recommendations.append(
                {
                    "type": "large_table_optimization",
                    "message": f"Table has {table_info.table_rows:,} rows - consider partitioning or archiving",
                    "impact": "Query performance optimization",
                }
            )

        return {
            "table_name": table_info.name,
            "analysis_timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "issues": issues,
            "recommendations": recommendations,
            "overall_score": self._calculate_table_score(metrics, issues),
        }

    def _calculate_table_score(
        self, metrics: dict[str, Any], issues: list[dict]
    ) -> int:
        """Calculate an overall table health score (0-100)."""
        score = 100

        # Deduct points for issues
        for issue in issues:
            if issue["severity"] == "critical":
                score -= 30
            elif issue["severity"] == "high":
                score -= 20
            elif issue["severity"] == "medium":
                score -= 10
            elif issue["severity"] == "low":
                score -= 5

        return max(0, score)

    def analyze_database(self, schema_snapshot: SchemaSnapshot) -> dict[str, Any]:
        """Analyze entire database schema for issues and recommendations."""
        database_issues = []
        database_recommendations = []
        table_analyses = {}

        overall_metrics = {
            "database_count": len(schema_snapshot.databases),
            "table_count": len(schema_snapshot.tables),
            "total_columns": 0,
            "total_indexes": 0,
            "total_constraints": 0,
        }

        # Analyze each table
        for table_key, table_info in schema_snapshot.tables.items():
            analysis = self.analyze_table(table_info)
            table_analyses[table_key] = analysis

            overall_metrics["total_columns"] += analysis["metrics"]["column_count"]
            overall_metrics["total_indexes"] += analysis["metrics"]["index_count"]
            overall_metrics["total_constraints"] += analysis["metrics"][
                "constraint_count"
            ]

        # Database-level checks
        if overall_metrics["table_count"] > 500:
            database_recommendations.append(
                {
                    "type": "schema_complexity",
                    "message": f"Database has {overall_metrics['table_count']} tables - consider schema organization",
                    "impact": "Maintainability and development efficiency",
                }
            )

        # Calculate overall health score
        table_scores = [
            analysis.get("overall_score", 0) for analysis in table_analyses.values()
        ]
        overall_score = sum(table_scores) / len(table_scores) if table_scores else 0

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "overall_metrics": overall_metrics,
            "overall_score": int(overall_score),
            "database_issues": database_issues,
            "database_recommendations": database_recommendations,
            "table_analyses": table_analyses,
            "schema_hash": schema_snapshot.schema_hash,
        }


class SchemaComparator:
    """Compares database schemas and generates diff reports."""

    def compare_schemas(
        self, schema1: SchemaSnapshot, schema2: SchemaSnapshot
    ) -> dict[str, Any]:
        """Compare two schema snapshots and generate a detailed diff."""
        diff = {
            "comparison_timestamp": datetime.now().isoformat(),
            "schema1_timestamp": schema1.timestamp.isoformat(),
            "schema2_timestamp": schema2.timestamp.isoformat(),
            "schema1_hash": schema1.schema_hash,
            "schema2_hash": schema2.schema_hash,
            "changes_detected": schema1.schema_hash != schema2.schema_hash,
            "database_changes": self._compare_databases(
                schema1.databases, schema2.databases
            ),
            "table_changes": self._compare_tables(schema1.tables, schema2.tables),
        }

        return diff

    def _compare_databases(
        self, db1: dict[str, DatabaseInfo], db2: dict[str, DatabaseInfo]
    ) -> dict[str, Any]:
        """Compare database-level changes."""
        added = set(db2.keys()) - set(db1.keys())
        removed = set(db1.keys()) - set(db2.keys())
        common = set(db1.keys()) & set(db2.keys())

        modified = []
        for db_name in common:
            if db1[db_name] != db2[db_name]:
                modified.append(
                    {
                        "database": db_name,
                        "changes": self._get_database_changes(
                            db1[db_name], db2[db_name]
                        ),
                    }
                )

        return {
            "added_databases": list(added),
            "removed_databases": list(removed),
            "modified_databases": modified,
        }

    def _compare_tables(
        self, tables1: dict[str, TableInfo], tables2: dict[str, TableInfo]
    ) -> dict[str, Any]:
        """Compare table-level changes."""
        added = set(tables2.keys()) - set(tables1.keys())
        removed = set(tables1.keys()) - set(tables2.keys())
        common = set(tables1.keys()) & set(tables2.keys())

        modified = []
        for table_key in common:
            changes = self._get_table_changes(tables1[table_key], tables2[table_key])
            if changes:
                modified.append({"table": table_key, "changes": changes})

        return {
            "added_tables": list(added),
            "removed_tables": list(removed),
            "modified_tables": modified,
        }

    def _get_database_changes(
        self, db1: DatabaseInfo, db2: DatabaseInfo
    ) -> dict[str, Any]:
        """Get specific changes between two database infos."""
        changes = {}

        if db1.character_set != db2.character_set:
            changes["character_set"] = {
                "old": db1.character_set,
                "new": db2.character_set,
            }
        if db1.collation != db2.collation:
            changes["collation"] = {"old": db1.collation, "new": db2.collation}
        if db1.table_count != db2.table_count:
            changes["table_count"] = {"old": db1.table_count, "new": db2.table_count}

        return changes

    def _get_table_changes(
        self, table1: TableInfo, table2: TableInfo
    ) -> dict[str, Any]:
        """Get specific changes between two table infos."""
        changes = {}

        # Compare basic table properties
        if table1.engine != table2.engine:
            changes["engine"] = {"old": table1.engine, "new": table2.engine}
        if table1.table_comment != table2.table_comment:
            changes["comment"] = {
                "old": table1.table_comment,
                "new": table2.table_comment,
            }

        # Compare columns
        column_changes = self._compare_columns(table1.columns, table2.columns)
        if column_changes:
            changes["columns"] = column_changes

        # Compare indexes
        index_changes = self._compare_indexes(table1.indexes, table2.indexes)
        if index_changes:
            changes["indexes"] = index_changes

        # Compare constraints
        constraint_changes = self._compare_constraints(
            table1.constraints, table2.constraints
        )
        if constraint_changes:
            changes["constraints"] = constraint_changes

        return changes

    def _compare_columns(
        self, cols1: list[ColumnInfo], cols2: list[ColumnInfo]
    ) -> dict[str, Any]:
        """Compare column lists."""
        cols1_dict = {col.name: col for col in cols1}
        cols2_dict = {col.name: col for col in cols2}

        added = set(cols2_dict.keys()) - set(cols1_dict.keys())
        removed = set(cols1_dict.keys()) - set(cols2_dict.keys())
        common = set(cols1_dict.keys()) & set(cols2_dict.keys())

        modified = []
        for col_name in common:
            if cols1_dict[col_name] != cols2_dict[col_name]:
                modified.append(
                    {
                        "column": col_name,
                        "old": cols1_dict[col_name],
                        "new": cols2_dict[col_name],
                    }
                )

        return (
            {"added": list(added), "removed": list(removed), "modified": modified}
            if (added or removed or modified)
            else {}
        )

    def _compare_indexes(
        self, idx1: list[IndexInfo], idx2: list[IndexInfo]
    ) -> dict[str, Any]:
        """Compare index lists."""
        idx1_dict = {idx.name: idx for idx in idx1}
        idx2_dict = {idx.name: idx for idx in idx2}

        added = set(idx2_dict.keys()) - set(idx1_dict.keys())
        removed = set(idx1_dict.keys()) - set(idx2_dict.keys())
        common = set(idx1_dict.keys()) & set(idx2_dict.keys())

        modified = []
        for idx_name in common:
            if idx1_dict[idx_name] != idx2_dict[idx_name]:
                modified.append(
                    {
                        "index": idx_name,
                        "old": idx1_dict[idx_name],
                        "new": idx2_dict[idx_name],
                    }
                )

        return (
            {"added": list(added), "removed": list(removed), "modified": modified}
            if (added or removed or modified)
            else {}
        )

    def _compare_constraints(
        self, const1: list[ConstraintInfo], const2: list[ConstraintInfo]
    ) -> dict[str, Any]:
        """Compare constraint lists."""
        const1_dict = {const.name: const for const in const1}
        const2_dict = {const.name: const for const in const2}

        added = set(const2_dict.keys()) - set(const1_dict.keys())
        removed = set(const1_dict.keys()) - set(const2_dict.keys())
        common = set(const1_dict.keys()) & set(const2_dict.keys())

        modified = []
        for const_name in common:
            if const1_dict[const_name] != const2_dict[const_name]:
                modified.append(
                    {
                        "constraint": const_name,
                        "old": const1_dict[const_name],
                        "new": const2_dict[const_name],
                    }
                )

        return (
            {"added": list(added), "removed": list(removed), "modified": modified}
            if (added or removed or modified)
            else {}
        )


class SchemaManager:
    """Main schema management class that coordinates all schema operations."""

    def __init__(self, database_manager):
        """Initialize schema manager."""
        self.database_manager = database_manager
        self.config = Config()
        self.logger = get_logger("schema")
        self.analyzer = SchemaAnalyzer()
        self.comparator = SchemaComparator()

    async def get_databases(self) -> list[DatabaseInfo]:
        """Get list of all databases with basic information."""
        try:
            query = """
            SELECT
                SCHEMA_NAME as name,
                DEFAULT_CHARACTER_SET_NAME as character_set,
                DEFAULT_COLLATION_NAME as collation
            FROM INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
            ORDER BY SCHEMA_NAME
            """

            result = await self.database_manager.execute_query(query)
            if not result.get("success"):
                raise DatabaseQueryError(
                    f"Failed to get databases: {result.get('error')}"
                )

            databases = []
            for row in result.get("data", []):
                # Get additional database statistics
                db_name = row["name"]
                table_count = await self._get_table_count(db_name)

                db_info = DatabaseInfo(
                    name=db_name,
                    character_set=row.get("character_set"),
                    collation=row.get("collation"),
                    table_count=table_count,
                )
                databases.append(db_info)

            return databases

        except Exception as e:
            self.logger.error(
                "SCHEMA_GET_DATABASES_ERROR",
                {"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise DatabaseConnectionError(f"Failed to retrieve databases: {str(e)}")

    async def _get_table_count(self, database_name: str) -> int:
        """Get number of tables in a database."""
        try:
            query = """
            SELECT COUNT(*) as table_count
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            """
            result = await self.database_manager.execute_query(query, [database_name])
            if result.get("success") and result.get("data"):
                return result["data"][0].get("table_count", 0)
            return 0
        except Exception:
            return 0

    async def get_tables(
        self, database_name: Optional[str] = None, include_views: bool = False
    ) -> list[TableInfo]:
        """Get comprehensive table information."""
        try:
            # Base query for table information
            where_clause = ""
            params = []

            if database_name:
                where_clause = "WHERE TABLE_SCHEMA = %s"
                params.append(database_name)

                if not include_views:
                    where_clause += " AND TABLE_TYPE = 'BASE TABLE'"
            elif not include_views:
                where_clause = "WHERE TABLE_TYPE = 'BASE TABLE'"

            query = f"""
            SELECT
                TABLE_NAME as name,
                TABLE_SCHEMA as database_name,
                TABLE_TYPE as table_type,
                ENGINE as engine,
                ROW_FORMAT as row_format,
                TABLE_ROWS as table_rows,
                AVG_ROW_LENGTH as avg_row_length,
                DATA_LENGTH as data_length,
                INDEX_LENGTH as index_length,
                DATA_FREE as data_free,
                AUTO_INCREMENT as auto_increment,
                CREATE_TIME as create_time,
                UPDATE_TIME as update_time,
                CHECK_TIME as check_time,
                TABLE_COLLATION as table_collation,
                CHECKSUM as checksum,
                CREATE_OPTIONS as create_options,
                TABLE_COMMENT as table_comment
            FROM INFORMATION_SCHEMA.TABLES
            {where_clause}
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """

            result = await self.database_manager.execute_query(query, params)
            if not result.get("success"):
                raise DatabaseQueryError(f"Failed to get tables: {result.get('error')}")

            tables = []
            for row in result.get("data", []):
                table_info = TableInfo(
                    name=row["name"],
                    database_name=row["database_name"],
                    table_type=row.get("table_type", "BASE TABLE"),
                    engine=row.get("engine"),
                    row_format=row.get("row_format"),
                    table_rows=row.get("table_rows"),
                    avg_row_length=row.get("avg_row_length"),
                    data_length=row.get("data_length"),
                    index_length=row.get("index_length"),
                    data_free=row.get("data_free"),
                    auto_increment=row.get("auto_increment"),
                    create_time=row.get("create_time"),
                    update_time=row.get("update_time"),
                    check_time=row.get("check_time"),
                    table_collation=row.get("table_collation"),
                    checksum=row.get("checksum"),
                    create_options=row.get("create_options"),
                    table_comment=row.get("table_comment"),
                )
                tables.append(table_info)

            return tables

        except Exception as e:
            self.logger.error(
                "SCHEMA_GET_TABLES_ERROR",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "database_name": database_name,
                },
                exc_info=True,
            )
            raise DatabaseConnectionError(f"Failed to retrieve tables: {str(e)}")

    async def get_table_details(
        self, table_name: str, database_name: Optional[str] = None
    ) -> TableInfo:
        """Get comprehensive details for a specific table."""
        try:
            # Get basic table info
            tables = await self.get_tables(database_name)
            table_info = None

            for table in tables:
                if table.name == table_name and (
                    not database_name or table.database_name == database_name
                ):
                    table_info = table
                    break

            if not table_info:
                raise ValidationError(f"Table '{table_name}' not found")

            # Get columns
            table_info.columns = await self._get_table_columns(
                table_name, table_info.database_name
            )

            # Get indexes
            table_info.indexes = await self._get_table_indexes(
                table_name, table_info.database_name
            )

            # Get constraints
            table_info.constraints = await self._get_table_constraints(
                table_name, table_info.database_name
            )

            return table_info

        except Exception as e:
            self.logger.error(
                "SCHEMA_GET_TABLE_DETAILS_ERROR",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "table_name": table_name,
                    "database_name": database_name,
                },
                exc_info=True,
            )
            if isinstance(
                e, ValidationError | DatabaseConnectionError | DatabaseQueryError
            ):
                raise
            raise DatabaseConnectionError(f"Failed to retrieve table details: {str(e)}")

    async def _get_table_columns(
        self, table_name: str, database_name: str
    ) -> list[ColumnInfo]:
        """Get detailed column information for a table."""
        query = """
        SELECT
            COLUMN_NAME as name,
            DATA_TYPE as data_type,
            IS_NULLABLE as is_nullable,
            COLUMN_DEFAULT as default_value,
            COLUMN_TYPE as column_type_full,
            CHARACTER_MAXIMUM_LENGTH as character_maximum_length,
            NUMERIC_PRECISION as numeric_precision,
            NUMERIC_SCALE as numeric_scale,
            COLUMN_COMMENT as column_comment,
            ORDINAL_POSITION as ordinal_position,
            EXTRA as extra,
            COLUMN_KEY as column_key
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = %s AND TABLE_SCHEMA = %s
        ORDER BY ORDINAL_POSITION
        """

        result = await self.database_manager.execute_query(
            query, [table_name, database_name]
        )
        if not result.get("success"):
            raise DatabaseQueryError(f"Failed to get columns: {result.get('error')}")

        columns = []
        for row in result.get("data", []):
            column_type = self._map_mysql_type_to_standard(row["data_type"])

            column = ColumnInfo(
                name=row["name"],
                data_type=row["data_type"],
                column_type=column_type,
                is_nullable=row["is_nullable"] == "YES",
                default_value=row.get("default_value"),
                is_primary_key=row.get("column_key") == "PRI",
                is_auto_increment="auto_increment" in (row.get("extra") or "").lower(),
                is_unsigned="unsigned" in (row.get("column_type_full") or "").lower(),
                character_maximum_length=row.get("character_maximum_length"),
                numeric_precision=row.get("numeric_precision"),
                numeric_scale=row.get("numeric_scale"),
                column_comment=row.get("column_comment"),
                ordinal_position=row.get("ordinal_position", 0),
                extra=row.get("extra"),
            )
            columns.append(column)

        return columns

    async def _get_table_indexes(
        self, table_name: str, database_name: str
    ) -> list[IndexInfo]:
        """Get index information for a table."""
        query = """
        SELECT
            INDEX_NAME as name,
            COLUMN_NAME as column_name,
            NON_UNIQUE as non_unique,
            INDEX_TYPE as index_type,
            COMMENT as comment
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_NAME = %s AND TABLE_SCHEMA = %s
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """

        result = await self.database_manager.execute_query(
            query, [table_name, database_name]
        )
        if not result.get("success"):
            raise DatabaseQueryError(f"Failed to get indexes: {result.get('error')}")

        # Group columns by index name
        indexes_dict = defaultdict(list)
        index_info_dict = {}

        for row in result.get("data", []):
            index_name = row["name"]
            indexes_dict[index_name].append(row["column_name"])

            if index_name not in index_info_dict:
                index_info_dict[index_name] = {
                    "is_unique": row["non_unique"] == 0,
                    "is_primary": index_name == "PRIMARY",
                    "index_type": row.get("index_type", "BTREE"),
                    "comment": row.get("comment"),
                }

        indexes = []
        for index_name, columns in indexes_dict.items():
            info = index_info_dict[index_name]
            index = IndexInfo(
                name=index_name,
                table_name=table_name,
                column_names=columns,
                is_unique=info["is_unique"],
                is_primary=info["is_primary"],
                index_type=info["index_type"],
                comment=info["comment"],
            )
            indexes.append(index)

        return indexes

    async def _get_table_constraints(
        self, table_name: str, database_name: str
    ) -> list[ConstraintInfo]:
        """Get constraint information for a table."""
        query = """
        SELECT
            kcu.CONSTRAINT_NAME as name,
            tc.CONSTRAINT_TYPE as constraint_type,
            kcu.COLUMN_NAME as column_name,
            kcu.REFERENCED_TABLE_SCHEMA as referenced_database,
            kcu.REFERENCED_TABLE_NAME as referenced_table,
            kcu.REFERENCED_COLUMN_NAME as referenced_column,
            rc.DELETE_RULE as on_delete,
            rc.UPDATE_RULE as on_update
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        LEFT JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
        LEFT JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            ON kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            AND kcu.TABLE_SCHEMA = tc.TABLE_SCHEMA
        WHERE kcu.TABLE_NAME = %s AND kcu.TABLE_SCHEMA = %s
        ORDER BY kcu.CONSTRAINT_NAME, kcu.ORDINAL_POSITION
        """

        result = await self.database_manager.execute_query(
            query, [table_name, database_name]
        )
        if not result.get("success"):
            raise DatabaseQueryError(
                f"Failed to get constraints: {result.get('error')}"
            )

        # Group constraints
        constraints_dict = defaultdict(
            lambda: {
                "columns": [],
                "referenced_columns": [],
                "type": None,
                "referenced_table": None,
                "on_delete": None,
                "on_update": None,
            }
        )

        for row in result.get("data", []):
            constraint_name = row["name"]
            constraint_data = constraints_dict[constraint_name]

            constraint_data["columns"].append(row["column_name"])
            constraint_data["type"] = row["constraint_type"]

            if row.get("referenced_table"):
                constraint_data["referenced_table"] = row["referenced_table"]
                constraint_data["referenced_columns"].append(row["referenced_column"])
                constraint_data["on_delete"] = row.get("on_delete")
                constraint_data["on_update"] = row.get("on_update")

        constraints = []
        for constraint_name, data in constraints_dict.items():
            constraint = ConstraintInfo(
                name=constraint_name,
                table_name=table_name,
                constraint_type=data["type"],
                column_names=data["columns"],
                referenced_table=data["referenced_table"],
                referenced_columns=(
                    data["referenced_columns"] if data["referenced_columns"] else None
                ),
                on_delete=data["on_delete"],
                on_update=data["on_update"],
            )
            constraints.append(constraint)

        return constraints

    def _map_mysql_type_to_standard(self, mysql_type: str) -> ColumnType:
        """Map MySQL data types to standard column types."""
        mysql_type = mysql_type.lower()

        type_mapping = {
            "int": ColumnType.INTEGER,
            "integer": ColumnType.INTEGER,
            "tinyint": ColumnType.INTEGER,
            "smallint": ColumnType.INTEGER,
            "mediumint": ColumnType.INTEGER,
            "bigint": ColumnType.BIGINT,
            "decimal": ColumnType.DECIMAL,
            "numeric": ColumnType.DECIMAL,
            "float": ColumnType.FLOAT,
            "double": ColumnType.DOUBLE,
            "real": ColumnType.DOUBLE,
            "varchar": ColumnType.VARCHAR,
            "char": ColumnType.CHAR,
            "text": ColumnType.TEXT,
            "tinytext": ColumnType.TEXT,
            "mediumtext": ColumnType.TEXT,
            "longtext": ColumnType.TEXT,
            "datetime": ColumnType.DATETIME,
            "date": ColumnType.DATE,
            "time": ColumnType.TIME,
            "timestamp": ColumnType.TIMESTAMP,
            "year": ColumnType.INTEGER,
            "boolean": ColumnType.BOOLEAN,
            "bool": ColumnType.BOOLEAN,
            "json": ColumnType.JSON,
            "blob": ColumnType.BLOB,
            "tinyblob": ColumnType.BLOB,
            "mediumblob": ColumnType.BLOB,
            "longblob": ColumnType.BLOB,
            "binary": ColumnType.BINARY,
            "varbinary": ColumnType.BINARY,
            "enum": ColumnType.ENUM,
            "set": ColumnType.SET,
        }

        return type_mapping.get(mysql_type, ColumnType.UNKNOWN)

    async def create_schema_snapshot(
        self, database_names: Optional[list[str]] = None
    ) -> SchemaSnapshot:
        """Create a complete schema snapshot."""
        try:
            # Get server info
            server_info = await self._get_server_info()

            # Get databases
            all_databases = await self.get_databases()
            if database_names:
                databases = {
                    db.name: db for db in all_databases if db.name in database_names
                }
            else:
                databases = {db.name: db for db in all_databases}

            # Get all tables with full details
            tables = {}
            for db_name in databases:
                db_tables = await self.get_tables(db_name, include_views=True)
                for table in db_tables:
                    # Get full table details
                    detailed_table = await self.get_table_details(table.name, db_name)
                    table_key = f"{db_name}.{table.name}"
                    tables[table_key] = detailed_table

            # Calculate schema hash
            schema_content = json.dumps(
                {
                    "databases": {name: db.name for name, db in databases.items()},
                    "tables": {
                        key: {
                            "name": table.name,
                            "columns": [col.name for col in table.columns],
                            "indexes": [idx.name for idx in table.indexes],
                            "constraints": [const.name for const in table.constraints],
                        }
                        for key, table in tables.items()
                    },
                },
                sort_keys=True,
            )

            schema_hash = hashlib.sha256(schema_content.encode()).hexdigest()

            snapshot = SchemaSnapshot(
                timestamp=datetime.now(),
                databases=databases,
                tables=tables,
                schema_hash=schema_hash,
                mysql_version=server_info.get("version"),
                server_info=server_info,
            )

            return snapshot

        except Exception as e:
            self.logger.error(
                "SCHEMA_CREATE_SNAPSHOT_ERROR",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "database_names": database_names,
                },
                exc_info=True,
            )
            raise DatabaseConnectionError(f"Failed to create schema snapshot: {str(e)}")

    async def _get_server_info(self) -> dict[str, Any]:
        """Get MySQL server information."""
        try:
            query = "SELECT VERSION() as version"
            result = await self.database_manager.execute_query(query)

            server_info = {
                "version": (
                    result.get("data", [{}])[0].get("version")
                    if result.get("success")
                    else None
                ),
                "snapshot_time": datetime.now().isoformat(),
            }

            return server_info
        except Exception:
            return {"version": None, "snapshot_time": datetime.now().isoformat()}

    def export_schema_snapshot(
        self, snapshot: SchemaSnapshot, format_type: str = "json"
    ) -> str:
        """Export schema snapshot to various formats."""
        if format_type.lower() == "json":
            return self._export_json(snapshot)
        elif format_type.lower() == "sql":
            return self._export_sql(snapshot)
        else:
            raise ValidationError(f"Unsupported export format: {format_type}")

    def _export_json(self, snapshot: SchemaSnapshot) -> str:
        """Export schema snapshot as JSON."""

        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        export_data = {
            "schema_snapshot": {
                "timestamp": snapshot.timestamp.isoformat(),
                "schema_hash": snapshot.schema_hash,
                "mysql_version": snapshot.mysql_version,
                "server_info": snapshot.server_info,
                "databases": {
                    name: {
                        "name": db.name,
                        "character_set": db.character_set,
                        "collation": db.collation,
                        "table_count": db.table_count,
                    }
                    for name, db in snapshot.databases.items()
                },
                "tables": {
                    key: {
                        "name": table.name,
                        "database_name": table.database_name,
                        "table_type": table.table_type,
                        "engine": table.engine,
                        "table_rows": table.table_rows,
                        "table_comment": table.table_comment,
                        "columns": [
                            {
                                "name": col.name,
                                "data_type": col.data_type,
                                "column_type": col.column_type.value,
                                "is_nullable": col.is_nullable,
                                "default_value": col.default_value,
                                "is_primary_key": col.is_primary_key,
                                "is_auto_increment": col.is_auto_increment,
                                "character_maximum_length": col.character_maximum_length,
                                "column_comment": col.column_comment,
                                "ordinal_position": col.ordinal_position,
                            }
                            for col in table.columns
                        ],
                        "indexes": [
                            {
                                "name": idx.name,
                                "column_names": idx.column_names,
                                "is_unique": idx.is_unique,
                                "is_primary": idx.is_primary,
                                "index_type": idx.index_type,
                            }
                            for idx in table.indexes
                        ],
                        "constraints": [
                            {
                                "name": const.name,
                                "constraint_type": const.constraint_type,
                                "column_names": const.column_names,
                                "referenced_table": const.referenced_table,
                                "referenced_columns": const.referenced_columns,
                            }
                            for const in table.constraints
                        ],
                    }
                    for key, table in snapshot.tables.items()
                },
            }
        }

        return json.dumps(export_data, indent=2, default=serialize_datetime)

    def _export_sql(self, snapshot: SchemaSnapshot) -> str:
        """Export schema snapshot as SQL DDL statements."""
        sql_statements = []

        # Add header comment
        sql_statements.append(
            f"-- Schema export generated on {snapshot.timestamp.isoformat()}"
        )
        sql_statements.append(
            f"-- MySQL version: {snapshot.mysql_version or 'Unknown'}"
        )
        sql_statements.append(f"-- Schema hash: {snapshot.schema_hash}")
        sql_statements.append("")

        # Export database creation statements
        for db_name, db_info in snapshot.databases.items():
            sql_statements.append(f"-- Database: {db_name}")
            sql_statements.append(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
            if db_info.character_set:
                sql_statements.append(f"  CHARACTER SET {db_info.character_set}")
            if db_info.collation:
                sql_statements.append(f"  COLLATE {db_info.collation};")
            else:
                sql_statements.append(";")
            sql_statements.append("")

        # Export table creation statements
        for _table_key, table in snapshot.tables.items():
            if table.table_type == "BASE TABLE":  # Skip views for now
                sql_statements.append(f"-- Table: {table.database_name}.{table.name}")
                sql_statements.append(f"USE `{table.database_name}`;")

                create_statement = f"CREATE TABLE `{table.name}` ("

                # Add columns
                column_defs = []
                for col in table.columns:
                    col_def = f"  `{col.name}` {col.data_type}"
                    if col.character_maximum_length:
                        col_def = f"  `{col.name}` {col.data_type}({col.character_maximum_length})"
                    elif col.numeric_precision:
                        if col.numeric_scale:
                            col_def = f"  `{col.name}` {col.data_type}({col.numeric_precision},{col.numeric_scale})"
                        else:
                            col_def = f"  `{col.name}` {col.data_type}({col.numeric_precision})"

                    if not col.is_nullable:
                        col_def += " NOT NULL"

                    if col.default_value is not None:
                        col_def += f" DEFAULT {col.default_value}"

                    if col.is_auto_increment:
                        col_def += " AUTO_INCREMENT"

                    if col.column_comment:
                        col_def += f" COMMENT '{col.column_comment}'"

                    column_defs.append(col_def)

                # Add primary key
                primary_key_cols = [
                    col.name for col in table.columns if col.is_primary_key
                ]
                if primary_key_cols:
                    pk_def = f"  PRIMARY KEY (`{'`, `'.join(primary_key_cols)}`)"
                    column_defs.append(pk_def)

                create_statement += ",\n".join(column_defs)
                create_statement += "\n)"

                if table.engine:
                    create_statement += f" ENGINE={table.engine}"

                if table.table_comment:
                    create_statement += f" COMMENT='{table.table_comment}'"

                create_statement += ";"

                sql_statements.append(create_statement)
                sql_statements.append("")

        return "\n".join(sql_statements)

    async def analyze_schema(
        self, database_names: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Analyze schema and provide recommendations."""
        try:
            snapshot = await self.create_schema_snapshot(database_names)
            analysis = self.analyzer.analyze_database(snapshot)
            return analysis
        except Exception as e:
            self.logger.error(
                "SCHEMA_ANALYZE_ERROR",
                {"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise DatabaseConnectionError(f"Failed to analyze schema: {str(e)}")

    async def compare_schemas(
        self, snapshot1: SchemaSnapshot, snapshot2: SchemaSnapshot
    ) -> dict[str, Any]:
        """Compare two schema snapshots."""
        try:
            comparison = self.comparator.compare_schemas(snapshot1, snapshot2)
            return comparison
        except Exception as e:
            self.logger.error(
                "SCHEMA_COMPARE_ERROR",
                {"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise DatabaseConnectionError(f"Failed to compare schemas: {str(e)}")

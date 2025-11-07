"""MCP-specific configuration classes."""

from typing import List, Optional


class MCPConfig:
    """MCP server configuration from [mcp] section"""
    
    server_name: str = "database-mcp"
    server_version: str = "1.0.0"
    readonly_mode: bool = False
    tool_mode: bool = True
    enable_rate_limiting: bool = True
    max_queries_per_minute: int = 60
    enable_query_execution: bool = True
    enable_query_explain: bool = True
    enable_schema_introspection: bool = True
    allowed_query_types: str = "SELECT, SHOW, DESCRIBE, EXPLAIN, UPDATE, INSERT, DELETE, CREATE, ALTER, DROP"
    
    def get_allowed_query_types_list(self) -> List[str]:
        """
        Parse allowed_query_types string to list.
        
        Supports fine-grained rules:
        - "DROP" - allows any DROP operation
        - "DROP TABLE" - allows ONLY DROP TABLE, blocks DROP DATABASE
        - "DROP DATABASE" - allows ONLY DROP DATABASE
        
        Returns:
            List of allowed query types (normalized to uppercase)
        """
        if not self.allowed_query_types:
            return []
        
        return [t.strip().upper() for t in self.allowed_query_types.split(',') if t.strip()]


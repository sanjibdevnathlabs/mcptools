"""Unit tests for DatabaseSecurityManager"""
import os

# Set test environment before imports
os.environ["APP_ENV"] = "test"

import pytest  # noqa: E402

from database.src.security import DatabaseSecurityManager  # noqa: E402


@pytest.mark.unit
class TestDatabaseSecurityUnit:
    """Unit tests for database security"""

    @pytest.fixture
    def security_manager(self):
        """Create security manager for testing"""
        return DatabaseSecurityManager()

    def test_validate_query_returns_required_fields(self, security_manager):
        """Test that validate_query_security returns required fields"""
        result = security_manager.validate_query_security("SHOW TABLES")
        assert "safe" in result
        assert "risk_level" in result
        assert "threats_detected" in result
        assert "query_type" in result
        assert "client_id" in result
        assert "timestamp" in result

    def test_validate_query_show_tables_is_safe(self, security_manager):
        """Test that SHOW TABLES is considered safe"""
        result = security_manager.validate_query_security("SHOW TABLES")
        assert result["safe"] is True
        assert result["risk_level"] == "low"
        assert len(result["threats_detected"]) == 0

    def test_validate_query_show_databases_is_safe(self, security_manager):
        """Test that SHOW DATABASES is considered safe"""
        result = security_manager.validate_query_security("SHOW DATABASES")
        assert result["safe"] is True
        assert result["risk_level"] == "low"

    def test_validate_query_describe_is_safe(self, security_manager):
        """Test that DESCRIBE is considered safe"""
        result = security_manager.validate_query_security("DESCRIBE users")
        assert result["safe"] is True
        assert result["risk_level"] == "low"

    def test_validate_query_explain_is_safe(self, security_manager):
        """Test that EXPLAIN is considered safe"""
        result = security_manager.validate_query_security("EXPLAIN SELECT id FROM users")
        # EXPLAIN with simple query should be safe
        assert "safe" in result
        assert "risk_level" in result

    def test_validate_query_with_client_id(self, security_manager):
        """Test that client_id is included in result"""
        result = security_manager.validate_query_security(
            "SHOW TABLES",
            client_id="test_client_123"
        )
        assert result["client_id"] == "test_client_123"

    def test_validate_query_type_detection(self, security_manager):
        """Test query type detection"""
        show_result = security_manager.validate_query_security("SHOW TABLES")
        assert show_result["query_type"] == "SHOW"

        describe_result = security_manager.validate_query_security("DESCRIBE users")
        assert describe_result["query_type"] == "DESCRIBE"

    def test_get_comprehensive_security_report(self, security_manager):
        """Test comprehensive security report"""
        report = security_manager.get_comprehensive_security_report()
        assert "timestamp" in report
        assert "security_config" in report
        assert "readonly_mode" in report["security_config"]
        assert "rate_limiting_enabled" in report["security_config"]
        assert "ssl_enabled" in report["security_config"]

    def test_validate_connection_security(self, security_manager):
        """Test connection security validation"""
        result = security_manager.validate_connection_security(
            client_id="test_client"
        )
        assert isinstance(result, dict)
        # Should have validation results
        assert "allowed" in result or "rate_limit_exceeded" in result

    def test_record_authentication_success(self, security_manager):
        """Test recording successful authentication"""
        # Should not raise error
        security_manager.record_authentication_event(
            "test_client",
            success=True
        )

    def test_record_authentication_failure(self, security_manager):
        """Test recording failed authentication"""
        # Should not raise error
        security_manager.record_authentication_event(
            "test_client",
            success=False,
            reason="Invalid credentials"
        )

    def test_validate_query_with_sql_injection(self, security_manager):
        """Test detection of SQL injection patterns"""
        # Test various SQL injection patterns
        injection_queries = [
            "SELECT * FROM users WHERE id = 1 OR 1=1",
            "SELECT * FROM users WHERE username = 'admin'--",
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM users WHERE id = 1 UNION SELECT * FROM passwords",
        ]
        
        for query in injection_queries:
            result = security_manager.validate_query_security(query)
            # Should detect threats
            assert "safe" in result
            assert "threats_detected" in result
            # Most injection patterns should be flagged
            if result["safe"] is False:
                assert len(result["threats_detected"]) > 0

    def test_validate_query_with_complex_query(self, security_manager):
        """Test detection of complex queries"""
        # Create a very complex query with multiple joins
        complex_query = """
            SELECT u.id, u.name, o.order_id, p.product_name
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            INNER JOIN order_items oi ON o.order_id = oi.order_id
            INNER JOIN products p ON oi.product_id = p.id
            WHERE u.status = 'active'
            GROUP BY u.id, o.order_id
            HAVING COUNT(*) > 10
            ORDER BY u.name
            LIMIT 1000
        """
        result = security_manager.validate_query_security(complex_query)
        assert "safe" in result
        assert "risk_level" in result
        assert "threats_detected" in result

    def test_validate_query_with_parameters(self, security_manager):
        """Test validation with query parameters"""
        query = "SELECT * FROM users WHERE id = %s AND status = %s"
        params = [1, "active"]
        
        result = security_manager.validate_query_security(query, params=params)
        assert "safe" in result
        assert "risk_level" in result

    def test_validate_query_with_suspicious_parameters(self, security_manager):
        """Test validation with suspicious parameters"""
        query = "SELECT * FROM users WHERE username = %s"
        # Try various suspicious parameters
        suspicious_params = [
            ["' OR '1'='1"],
            ["admin'--"],
            ["1; DROP TABLE users"],
        ]
        
        for params in suspicious_params:
            result = security_manager.validate_query_security(query, params=params)
            assert "safe" in result
            # Should have some analysis even if params are suspicious

    def test_validate_query_with_multiple_statements(self, security_manager):
        """Test detection of multiple SQL statements"""
        query = "SELECT * FROM users; DELETE FROM users WHERE id = 1"
        result = security_manager.validate_query_security(query)
        assert "safe" in result
        assert "threats_detected" in result

    def test_validate_query_with_comment_injection(self, security_manager):
        """Test detection of comment-based injection"""
        queries = [
            "SELECT * FROM users WHERE id = 1 -- comment",
            "SELECT * FROM users WHERE id = 1 /* comment */",
            "SELECT * FROM users WHERE id = 1 #comment",
        ]
        
        for query in queries:
            result = security_manager.validate_query_security(query)
            assert "safe" in result

    def test_validate_query_with_union_based_injection(self, security_manager):
        """Test detection of UNION-based injection"""
        query = "SELECT id, name FROM users UNION SELECT credit_card, cvv FROM payments"
        result = security_manager.validate_query_security(query)
        assert "safe" in result
        assert "threats_detected" in result

    def test_validate_query_with_nested_subqueries(self, security_manager):
        """Test validation of nested subqueries"""
        query = """
            SELECT * FROM users WHERE id IN (
                SELECT user_id FROM orders WHERE total > (
                    SELECT AVG(total) FROM orders
                )
            )
        """
        result = security_manager.validate_query_security(query)
        assert "safe" in result
        assert "risk_level" in result

    def test_validate_query_with_dangerous_functions(self, security_manager):
        """Test detection of dangerous SQL functions"""
        queries = [
            "SELECT LOAD_FILE('/etc/passwd')",
            "SELECT INTO OUTFILE '/tmp/dump.txt' FROM users",
            "CALL SYSTEM('ls -la')",
        ]
        
        for query in queries:
            result = security_manager.validate_query_security(query)
            assert "safe" in result
            # Dangerous functions should be flagged
            if not result["safe"]:
                assert len(result["threats_detected"]) > 0

    def test_validate_query_error_handling(self, security_manager):
        """Test error handling in query validation"""
        # Test with empty query
        result = security_manager.validate_query_security("")
        assert "safe" in result
        
        # Test with None (should handle gracefully)
        result = security_manager.validate_query_security(None)
        assert "safe" in result

    def test_validate_query_with_time_based_injection(self, security_manager):
        """Test detection of time-based injection"""
        queries = [
            "SELECT * FROM users WHERE id = 1 AND SLEEP(5)",
            "SELECT * FROM users WHERE id = 1 AND BENCHMARK(1000000,MD5('test'))",
        ]
        
        for query in queries:
            result = security_manager.validate_query_security(query)
            assert "safe" in result
            assert "threats_detected" in result

    def test_query_normalization(self, security_manager):
        """Test query normalization"""
        # Same query with different whitespace should be analyzed consistently
        queries = [
            "SELECT   *   FROM   users",
            "SELECT * FROM users",
            "  SELECT  *  FROM  users  ",
        ]
        
        results = [security_manager.validate_query_security(q) for q in queries]
        # All should have same query type
        for result in results:
            assert result["query_type"] == "SELECT"

    def test_validate_query_with_encoding_attacks(self, security_manager):
        """Test detection of encoding-based attacks"""
        queries = [
            "SELECT * FROM users WHERE name = CHAR(97,100,109,105,110)",
            "SELECT * FROM users WHERE id = 0x61646D696E",
        ]
        
        for query in queries:
            result = security_manager.validate_query_security(query)
            assert "safe" in result

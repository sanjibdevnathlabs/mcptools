import hashlib
import logging
import re
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple
import sqlparse
from sqlparse import sql, tokens as T
from database.config import Config
from .logging_config import get_logger

class SecurityAuditLogger:
    """Dedicated security audit logger for tracking security events."""
    
    def __init__(self):
        """Initialize security audit logger."""
        self.audit_logger = logging.getLogger("database.security.audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # Create a separate handler for security audit logs if needed
        if not self.audit_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - SECURITY-AUDIT - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
    
    def log_security_event(
        self, 
        event_type: str, 
        message: str, 
        client_id: str = "unknown",
        severity: str = "INFO",
        **extra_data
    ) -> None:
        """Log a security event with structured data."""
        log_data = {
            "event_type": event_type,
            "client_id": client_id,
            "timestamp": time.time(),
            **extra_data
        }
        
        log_message = f"[{event_type}] {message} | Client: {client_id} | Data: {log_data}"
        
        if severity == "CRITICAL":
            self.audit_logger.critical(log_message)
        elif severity == "ERROR":
            self.audit_logger.error(log_message)
        elif severity == "WARNING":
            self.audit_logger.warning(log_message)
        else:
            self.audit_logger.info(log_message)

class QuerySecurityAnalyzer:
    """Advanced SQL query security analyzer with pattern detection and risk assessment."""
    
    def __init__(self):
        """Initialize query security analyzer."""
        self.config = Config()
        self.logger = get_logger('security')
        self.audit_logger = SecurityAuditLogger()
        
        # SQL injection patterns (more comprehensive)
        self.injection_patterns = [
            # Classic SQL injection
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b.*\b(select|from|where|union)\b)",
            r"(\b(or|and)\b\s*[\d\w]*\s*=\s*[\d\w]*)",
            r"(;\s*(drop|delete|insert|update|create|alter))",
            r"(--|\#|\/\*|\*\/)",
            r"(\b(xp_cmdshell|sp_executesql|openrowset|opendatasource)\b)",
            
            # Boolean-based blind injection
            r"(\b(or|and)\b\s*(true|false|\d+\s*=\s*\d+))",
            r"(\b(or|and)\b\s*\d+\s*[<>=]+\s*\d+)",
            
            # Time-based blind injection
            r"(waitfor\s+delay|sleep\s*\(|pg_sleep\s*\()",
            r"(benchmark\s*\(|get_lock\s*\()",
            
            # Error-based injection
            r"(extractvalue\s*\(|updatexml\s*\()",
            r"(cast\s*\(.*as\s+(int|integer|decimal))",
            
            # UNION-based injection
            r"(union\s+(all\s+)?select.*null)",
            r"(union\s+select.*\d+)",
            
            # Stacked queries
            r"(;\s*(select|insert|update|delete|drop|create|alter))",
            
            # File operations
            r"(load_file\s*\(|into\s+outfile|into\s+dumpfile)",
            r"(load\s+data\s+infile)",
            
            # Information schema attacks
            r"(information_schema\.(tables|columns|schemata))",
            r"(sys\.(databases|tables|columns))",
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                for pattern in self.injection_patterns]
        
        # High-risk SQL keywords that should be monitored
        self.high_risk_keywords = {
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE',
            'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'XP_CMDSHELL', 'SP_EXECUTESQL',
            'LOAD_FILE', 'INTO OUTFILE', 'INTO DUMPFILE', 'LOAD DATA INFILE',
            'OPENROWSET', 'OPENDATASOURCE', 'BULK', 'SHUTDOWN'
        }
        
        # Safe query prefixes for read-only operations
        self.safe_query_prefixes = {
            'SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN', 'ANALYZE'
        }
    
    def analyze_query_security(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive security analysis of a SQL query.
        
        Returns:
            Dictionary with security analysis results
        """
        analysis_result = {
            "safe": True,
            "risk_level": "low",
            "threats_detected": [],
            "recommendations": [],
            "query_type": "",
            "sanitized_sql": sql
        }
        
        try:
            # Basic normalization
            normalized_sql = self._normalize_query(sql)
            analysis_result["query_type"] = self._get_query_type(normalized_sql)
            
            # Check for SQL injection patterns
            injection_threats = self._detect_injection_patterns(normalized_sql)
            if injection_threats:
                analysis_result["threats_detected"].extend(injection_threats)
                analysis_result["risk_level"] = "critical"
                analysis_result["safe"] = False
            
            # Parse SQL structure for deeper analysis
            parsed_threats = self._analyze_parsed_structure(sql)
            if parsed_threats:
                analysis_result["threats_detected"].extend(parsed_threats)
                if analysis_result["risk_level"] == "low":
                    analysis_result["risk_level"] = "medium"
                analysis_result["safe"] = False
            
            # Check query complexity and resource usage risks
            complexity_issues = self._analyze_query_complexity(normalized_sql)
            if complexity_issues:
                analysis_result["threats_detected"].extend(complexity_issues)
                if analysis_result["risk_level"] == "low":
                    analysis_result["risk_level"] = "medium"
            
            # Validate parameters
            if params:
                param_issues = self._analyze_parameters(params)
                if param_issues:
                    analysis_result["threats_detected"].extend(param_issues)
            
            # Generate recommendations
            analysis_result["recommendations"] = self._generate_security_recommendations(
                analysis_result["threats_detected"], 
                analysis_result["query_type"]
            )
            
            # Log security events
            if analysis_result["threats_detected"]:
                self.audit_logger.log_security_event(
                    "QUERY_SECURITY_THREAT",
                    f"Security threats detected in query: {analysis_result['threats_detected']}",
                    severity="WARNING" if analysis_result["risk_level"] == "medium" else "ERROR",
                    query_hash=hashlib.md5(sql.encode()).hexdigest()[:16],
                    risk_level=analysis_result["risk_level"],
                    threats=analysis_result["threats_detected"]
                )
            
        except Exception as e:
            self.logger.error("SECURITY_ANALYSIS_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            analysis_result.update({
                "safe": False,
                "risk_level": "unknown",
                "threats_detected": [f"Analysis error: {str(e)}"]
            })
        
        return analysis_result
    
    def _normalize_query(self, sql: str) -> str:
        """Normalize SQL query for consistent analysis."""
        # Remove extra whitespace and normalize case
        normalized = re.sub(r'\s+', ' ', sql.strip())
        return normalized
    
    def _get_query_type(self, sql: str) -> str:
        """Extract the primary query type."""
        first_word = sql.split()[0].upper() if sql.split() else ""
        return first_word
    
    def _detect_injection_patterns(self, sql: str) -> List[Dict[str, str]]:
        """Detect SQL injection patterns using regex."""
        threats = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(sql)
            if matches:
                threats.append({
                    "type": "sql_injection",
                    "pattern_id": f"INJECT_{i:03d}",
                    "description": f"Potential SQL injection pattern detected: {matches[0] if matches else 'pattern match'}",
                    "severity": "critical"
                })
        
        return threats
    
    def _analyze_parsed_structure(self, sql: str) -> List[Dict[str, str]]:
        """Analyze SQL using sqlparse for structural threats."""
        threats = []
        
        try:
            parsed = sqlparse.parse(sql)[0]
            
            # Check for dangerous operations with context extraction
            tokens = list(parsed.flatten())
            for i, token in enumerate(tokens):
                if token.ttype in (T.Keyword, T.Keyword.DDL, T.Keyword.DML):
                    keyword = token.value.upper()
                    if keyword in self.high_risk_keywords:
                        # Extract context (next keyword for fine-grained rules)
                        context = None
                        if i + 1 < len(tokens):
                            next_token = tokens[i + 1]
                            if next_token.ttype in (T.Keyword, T.Keyword.DDL, T.Keyword.DML):
                                context = next_token.value.upper()
                        
                        if not self._is_keyword_allowed(keyword, context):
                            context_str = f" {context}" if context else ""
                            threats.append({
                                "type": "dangerous_operation",
                                "description": f"High-risk keyword detected: {keyword}{context_str}",
                                "severity": "high",
                                "keyword": keyword
                            })
            
            # Check for suspicious constructs
            sql_upper = sql.upper()
            if 'UNION' in sql_upper and 'SELECT' in sql_upper:
                select_count = sql_upper.count('SELECT')
                if select_count > 1:
                    threats.append({
                        "type": "union_injection",
                        "description": f"Multiple SELECT statements with UNION detected ({select_count} SELECT clauses)",
                        "severity": "high"
                    })
            
        except Exception as e:
            self.logger.warning("SQL_PARSE_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            # If we can't parse, treat as suspicious
            threats.append({
                "type": "parse_error",
                "description": f"Query could not be parsed safely: {str(e)}",
                "severity": "medium"
            })
        
        return threats
    
    def _analyze_query_complexity(self, sql: str) -> List[Dict[str, str]]:
        """Analyze query for complexity and resource usage risks."""
        threats = []
        
        # Check for potential DoS patterns
        if sql.count('JOIN') > 5:
            threats.append({
                "type": "complexity_risk",
                "description": f"Query has {sql.count('JOIN')} JOINs, may cause performance issues",
                "severity": "low"
            })
        
        if sql.count('(') > 20:  # Nested subqueries
            threats.append({
                "type": "complexity_risk", 
                "description": "Query has deep nesting, may cause performance issues",
                "severity": "low"
            })
        
        # Check for cartesian products
        if re.search(r'FROM\s+\w+\s*,\s*\w+(?:\s*,\s*\w+)*(?!\s+WHERE)', sql, re.IGNORECASE):
            threats.append({
                "type": "cartesian_product",
                "description": "Potential cartesian product detected (missing JOIN conditions)",
                "severity": "medium"
            })
        
        return threats
    
    def _analyze_parameters(self, params: List[Any]) -> List[Dict[str, str]]:
        """Analyze query parameters for security issues."""
        threats = []
        
        for i, param in enumerate(params):
            if isinstance(param, str):
                # Check for SQL keywords in parameters
                param_upper = param.upper()
                for keyword in self.high_risk_keywords:
                    if keyword in param_upper:
                        threats.append({
                            "type": "parameter_injection",
                            "description": f"Parameter {i} contains SQL keyword: {keyword}",
                            "severity": "medium",
                            "parameter_index": i
                        })
                
                # Check for suspicious patterns in string parameters
                if re.search(r'[\'";\-\-\/\*]', param):
                    threats.append({
                        "type": "parameter_suspicious",
                        "description": f"Parameter {i} contains suspicious characters",
                        "severity": "low",
                        "parameter_index": i
                    })
        
        return threats
    
    def _is_keyword_allowed(self, keyword: str, context: str = None) -> bool:
        """
        Check if a keyword is allowed based on configuration.
        
        Supports fine-grained rules:
        - "DROP" allows any DROP operation
        - "DROP TABLE" allows ONLY DROP TABLE, blocks DROP DATABASE
        - "DROP DATABASE" allows ONLY DROP DATABASE
        
        Args:
            keyword: SQL keyword (e.g., "DROP")
            context: Additional context (e.g., "TABLE", "DATABASE")
            
        Returns:
            True if allowed, False otherwise
        """
        if self.config.mcp.readonly_mode:
            return keyword in {'SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN', 'ANALYZE'}
        
        # Get allowed query types as list
        allowed_types = self.config.mcp.get_allowed_query_types_list()
        
        # Check for exact match with context (fine-grained rule)
        if context:
            compound_rule = f"{keyword} {context}"
            if compound_rule in allowed_types:
                return True
            
            # If compound rules exist for this keyword, keyword alone is NOT allowed
            # Example: ["DROP TABLE"] means DROP DATABASE is blocked
            has_compound_rules = any(rule.startswith(f"{keyword} ") for rule in allowed_types)
            if has_compound_rules:
                return False
        
        # Check for keyword alone (allows any variation)
        return keyword in allowed_types
    
    def _generate_security_recommendations(self, threats: List[Dict], query_type: str) -> List[str]:
        """Generate security recommendations based on detected threats."""
        recommendations = []
        
        if any(t["type"] == "sql_injection" for t in threats):
            recommendations.extend([
                "Use parameterized queries to prevent SQL injection",
                "Validate all user input before processing",
                "Consider using stored procedures for complex operations"
            ])
        
        if any(t["type"] == "dangerous_operation" for t in threats):
            recommendations.extend([
                "Enable read-only mode if write operations are not needed",
                "Implement proper access controls for DDL/DML operations",
                "Log and monitor all high-risk operations"
            ])
        
        if any(t["type"] == "complexity_risk" for t in threats):
            recommendations.extend([
                "Consider query optimization to reduce complexity",
                "Implement query timeout limits",
                "Monitor query execution time and resource usage"
            ])
        
        if not recommendations:
            recommendations.append("Query appears safe, but continue monitoring for anomalies")
        
        return recommendations

class ConnectionSecurityManager:
    """Manages connection-level security including rate limiting and access controls."""
    
    def __init__(self):
        """Initialize connection security manager."""
        self.config = Config()
        self.audit_logger = SecurityAuditLogger()
        
        # Connection tracking
        self.connection_attempts = defaultdict(deque)
        self.failed_attempts = defaultdict(int)
        self.blocked_clients = defaultdict(float)  # client_id -> block_until_time
        
        # Rate limiting windows
        self.rate_limit_window = 300  # 5 minutes
        self.max_connections_per_window = 100
        self.max_failed_attempts = 10
        self.block_duration = 900  # 15 minutes
    
    def validate_connection_attempt(self, client_id: str = "default", client_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Validate a connection attempt and apply rate limiting.
        
        Returns:
            Dictionary with validation results
        """
        now = time.time()
        
        # Check if client is currently blocked
        if client_id in self.blocked_clients:
            if now < self.blocked_clients[client_id]:
                remaining_time = self.blocked_clients[client_id] - now
                self.audit_logger.log_security_event(
                    "CONNECTION_BLOCKED",
                    f"Connection attempt from blocked client",
                    client_id=client_id,
                    severity="WARNING",
                    remaining_block_time=remaining_time
                )
                return {
                    "allowed": False,
                    "reason": "client_blocked",
                    "message": f"Client blocked. Try again in {remaining_time:.0f} seconds.",
                    "retry_after": remaining_time
                }
            else:
                # Block expired, remove from blocked list
                del self.blocked_clients[client_id]
                self.failed_attempts[client_id] = 0
        
        # Clean up old connection attempts
        cutoff_time = now - self.rate_limit_window
        client_attempts = self.connection_attempts[client_id]
        while client_attempts and client_attempts[0] < cutoff_time:
            client_attempts.popleft()
        
        # Check rate limit
        if len(client_attempts) >= self.max_connections_per_window:
            self.audit_logger.log_security_event(
                "RATE_LIMIT_EXCEEDED",
                f"Rate limit exceeded for client",
                client_id=client_id,
                severity="WARNING",
                attempt_count=len(client_attempts)
            )
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "message": "Rate limit exceeded. Too many connection attempts.",
                "retry_after": self.rate_limit_window
            }
        
        # Record this attempt
        client_attempts.append(now)
        
        self.audit_logger.log_security_event(
            "CONNECTION_ATTEMPT",
            f"Connection attempt validated",
            client_id=client_id,
            severity="INFO",
            client_info=client_info or {}
        )
        
        return {
            "allowed": True,
            "message": "Connection attempt validated successfully"
        }
    
    def record_authentication_failure(self, client_id: str, reason: str) -> None:
        """Record an authentication failure and potentially block the client."""
        self.failed_attempts[client_id] += 1
        
        self.audit_logger.log_security_event(
            "AUTH_FAILURE",
            f"Authentication failure: {reason}",
            client_id=client_id,
            severity="WARNING",
            failure_count=self.failed_attempts[client_id],
            reason=reason
        )
        
        # Block client if too many failures
        if self.failed_attempts[client_id] >= self.max_failed_attempts:
            block_until = time.time() + self.block_duration
            self.blocked_clients[client_id] = block_until
            
            self.audit_logger.log_security_event(
                "CLIENT_BLOCKED",
                f"Client blocked due to {self.failed_attempts[client_id]} failed attempts",
                client_id=client_id,
                severity="ERROR",
                failure_count=self.failed_attempts[client_id],
                block_duration=self.block_duration
            )
    
    def record_successful_connection(self, client_id: str) -> None:
        """Record a successful connection and reset failure count."""
        if client_id in self.failed_attempts:
            del self.failed_attempts[client_id]
        
        self.audit_logger.log_security_event(
            "CONNECTION_SUCCESS",
            "Successful connection established",
            client_id=client_id,
            severity="INFO"
        )
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get connection security statistics."""
        now = time.time()
        active_blocks = sum(1 for block_time in self.blocked_clients.values() if block_time > now)
        
        total_recent_attempts = sum(
            len([attempt for attempt in attempts if attempt > now - self.rate_limit_window])
            for attempts in self.connection_attempts.values()
        )
        
        return {
            "active_blocks": active_blocks,
            "total_clients_tracked": len(self.connection_attempts),
            "recent_connection_attempts": total_recent_attempts,
            "clients_with_failures": len(self.failed_attempts),
            "rate_limit_window": self.rate_limit_window,
            "max_connections_per_window": self.max_connections_per_window
        }

class DatabaseSecurityManager:
    """Main security manager that coordinates all security components."""
    
    def __init__(self):
        """Initialize the database security manager."""
        self.config = Config()
        self.logger = get_logger('security')
        self.query_analyzer = QuerySecurityAnalyzer()
        self.connection_manager = ConnectionSecurityManager()
        self.audit_logger = SecurityAuditLogger()
        
        # Security configuration validation
        self._validate_security_config()
    
    def _validate_security_config(self) -> None:
        """Validate security configuration settings."""
        if not self.config.mcp.enable_rate_limiting:
            self.logger.warning("SECURITY_CONFIG_RATE_LIMITING_DISABLED", {
                "recommendation": "consider enabling for production"
            })
        
        if not self.config.database.use_ssl and not self.config.server.debug:
            self.logger.warning("SECURITY_CONFIG_SSL_DISABLED", {
                "recommendation": "consider enabling for production"
            })
        
        if self.config.mcp.max_queries_per_minute > 1000:
            self.logger.warning("SECURITY_CONFIG_HIGH_RATE_LIMIT", {
                "current_limit": self.config.mcp.max_queries_per_minute,
                "recommendation": "monitor for abuse"
            })
    
    def validate_query_security(
        self, 
        sql: str, 
        params: Optional[List[Any]] = None,
        client_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Comprehensive query security validation.
        
        Returns:
            Dictionary with security validation results
        """
        # Analyze query security
        security_analysis = self.query_analyzer.analyze_query_security(sql, params)
        
        # Add client context
        security_analysis["client_id"] = client_id
        security_analysis["timestamp"] = time.time()
        
        # Log high-risk queries
        if security_analysis["risk_level"] in ["high", "critical"]:
            self.audit_logger.log_security_event(
                "HIGH_RISK_QUERY",
                f"High-risk query detected from client",
                client_id=client_id,
                severity="ERROR",
                risk_level=security_analysis["risk_level"],
                threats=security_analysis["threats_detected"]
            )
        
        return security_analysis
    
    def validate_connection_security(
        self, 
        client_id: str = "default", 
        client_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Validate connection security including rate limiting.
        
        Returns:
            Dictionary with connection validation results
        """
        return self.connection_manager.validate_connection_attempt(client_id, client_info)
    
    def record_authentication_event(
        self, 
        client_id: str, 
        success: bool, 
        reason: str = ""
    ) -> None:
        """Record authentication events for monitoring."""
        if success:
            self.connection_manager.record_successful_connection(client_id)
        else:
            self.connection_manager.record_authentication_failure(client_id, reason)
    
    def get_comprehensive_security_report(self) -> Dict[str, Any]:
        """Get a comprehensive security status report."""
        return {
            "timestamp": time.time(),
            "security_config": {
                "readonly_mode": self.config.mcp.readonly_mode,
                "rate_limiting_enabled": self.config.mcp.enable_rate_limiting,
                "ssl_enabled": self.config.database.use_ssl,
                "max_query_length": self.config.database.max_query_length,
                "query_timeout": self.config.database.query_timeout,
                "allowed_query_types": self.config.mcp.allowed_query_types
            },
            "connection_security": self.connection_manager.get_security_stats(),
            "recommendations": [
                "Monitor audit logs for suspicious patterns",
                "Regularly review and update security configurations",
                "Implement network-level security controls",
                "Keep database and dependencies updated",
                "Use strong authentication mechanisms"
            ]
        }

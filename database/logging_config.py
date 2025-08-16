import json
import logging
import logging.handlers
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path
import contextvars

# Context variable for trace ID
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('trace_id', default='')

class TraceCodeLogger:
    """Custom logger that supports trace code based logging with JSON formatting."""
    
    def __init__(self, name: str, logger: logging.Logger):
        self.name = name
        self.logger = logger
    
    def _log(self, level: int, trace_code: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: Optional[bool] = None):
        """Internal logging method with trace code support."""
        if not self.logger.isEnabledFor(level):
            return
            
        # Get or generate trace ID
        trace_id = trace_id_var.get()
        if not trace_id:
            trace_id = str(uuid.uuid4())[:8]
            trace_id_var.set(trace_id)
        
        # Prepare log data
        log_data = {
            'trace_code': trace_code,
            'trace_id': trace_id,
            'logger_name': self.name,
            'level': logging.getLevelName(level),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add extra data if provided
        if extra_data:
            # Safely serialize extra data
            safe_extra = self._make_json_safe(extra_data)
            log_data.update(safe_extra)
        
        # Log the message
        self.logger.log(level, json.dumps(log_data, default=str), exc_info=exc_info)
    
    def _make_json_safe(self, obj):
        """Convert object to JSON-safe format."""
        try:
            json.dumps(obj)
            return obj
        except TypeError:
            if isinstance(obj, dict):
                return {k: self._make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [self._make_json_safe(item) for item in obj]
            else:
                return str(obj)
    
    def debug(self, trace_code: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message with trace code."""
        self._log(logging.DEBUG, trace_code, extra_data)
    
    def info(self, trace_code: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message with trace code."""
        self._log(logging.INFO, trace_code, extra_data)
    
    def warning(self, trace_code: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message with trace code."""
        self._log(logging.WARNING, trace_code, extra_data)
    
    def error(self, trace_code: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message with trace code."""
        self._log(logging.ERROR, trace_code, extra_data, exc_info)
    
    def critical(self, trace_code: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical message with trace code."""
        self._log(logging.CRITICAL, trace_code, extra_data, exc_info)
    
    # Convenience methods for backward compatibility
    def warn(self, trace_code: str, extra_data: Optional[Dict[str, Any]] = None):
        """Alias for warning."""
        self.warning(trace_code, extra_data)
    
    def exception(self, trace_code: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log error with exception info."""
        self.error(trace_code, extra_data, exc_info=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def __init__(self, include_timestamp: bool = True, include_trace_id: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_trace_id = include_trace_id
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        try:
            # Try to parse message as JSON (for trace code logs)
            log_data = json.loads(record.getMessage())
        except (json.JSONDecodeError, TypeError):
            # Fall back to standard message format
            log_data = {
                'message': record.getMessage(),
                'level': record.levelname,
                'logger_name': record.name
            }
            
            if self.include_timestamp:
                log_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            
            if self.include_trace_id:
                trace_id = trace_id_var.get()
                if trace_id:
                    log_data['trace_id'] = trace_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info'):
                log_data[f'extra_{key}'] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)

class TextFormatter(logging.Formatter):
    """Enhanced text formatter for human-readable logs."""
    
    def __init__(self, include_trace_id: bool = True):
        self.include_trace_id = include_trace_id
        format_string = "%(asctime)s - %(levelname)s - %(name)s"
        
        if include_trace_id:
            format_string += " - [%(trace_id)s]"
            
        format_string += " - %(message)s"
        
        super().__init__(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text."""
        try:
            # Try to parse message as JSON and extract trace code
            log_data = json.loads(record.getMessage())
            if 'trace_code' in log_data:
                message_parts = [log_data['trace_code']]
                
                # Add extra data if present
                extra_data = {k: v for k, v in log_data.items() 
                             if k not in ('trace_code', 'trace_id', 'logger_name', 'level', 'timestamp')}
                if extra_data:
                    message_parts.append(json.dumps(extra_data, default=str))
                
                record.msg = ' - '.join(message_parts)
                record.args = ()
                
                # Add trace_id to record for formatting
                if self.include_trace_id and 'trace_id' in log_data:
                    record.trace_id = log_data['trace_id']
        except (json.JSONDecodeError, TypeError):
            # Standard message, add trace_id if available
            if self.include_trace_id:
                trace_id = trace_id_var.get()
                if trace_id:
                    record.trace_id = trace_id
                else:
                    record.trace_id = "--------"
        
        return super().format(record)

def setup_logging(config) -> Dict[str, TraceCodeLogger]:
    """
    Setup logging based on configuration.
    
    Args:
        config: Application configuration object
        
    Returns:
        Dictionary of configured trace code loggers
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    log_level = getattr(logging, config.server.log_level.upper())
    root_logger.setLevel(log_level)
    
    # Create formatters
    if config.server.log_format == "json":
        formatter = JSONFormatter(
            include_timestamp=config.server.log_include_timestamp,
            include_trace_id=config.server.log_include_trace_id
        )
    else:
        formatter = TextFormatter(
            include_trace_id=config.server.log_include_trace_id
        )
    
    # Configure handlers based on destination
    if config.server.log_destination in ("stdout", "both"):
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(log_level)
        root_logger.addHandler(stdout_handler)
    
    if config.server.log_destination in ("stderr", "both"):
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        stderr_handler.setLevel(logging.ERROR)  # Only errors to stderr
        root_logger.addHandler(stderr_handler)
    
    if config.server.log_destination in ("file", "both"):
        # Create log directory if it doesn't exist
        log_file_path = Path(config.server.log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse file size
        max_bytes = _parse_file_size(config.server.log_max_file_size)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=max_bytes,
            backupCount=config.server.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    # Create trace code loggers for different modules
    loggers = {
        'main': TraceCodeLogger('database.main', logging.getLogger('database.main')),
        'server': TraceCodeLogger('database.server', logging.getLogger('database.server')),
        'database': TraceCodeLogger('database.manager', logging.getLogger('database.manager')),
        'security': TraceCodeLogger('database.security', logging.getLogger('database.security')),
        'transport': TraceCodeLogger('database.transport', logging.getLogger('database.transport')),
        'config': TraceCodeLogger('database.config', logging.getLogger('database.config')),
        'schema': TraceCodeLogger('database.schema', logging.getLogger('database.schema')),
        'monitoring': TraceCodeLogger('database.monitoring', logging.getLogger('database.monitoring'))
    }
    
    # Log configuration
    config_logger = loggers['config']
    config_logger.info("LOGGING_CONFIGURED", {
        "log_level": config.server.log_level,
        "log_format": config.server.log_format,
        "log_destination": config.server.log_destination,
        "log_file_path": str(config.server.log_file_path) if config.server.log_destination in ("file", "both") else None
    })
    
    return loggers

def _parse_file_size(size_str: str) -> int:
    """Parse file size string (e.g., '100MB') to bytes."""
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # Assume bytes
        return int(size_str)

def get_trace_id() -> str:
    """Get current trace ID."""
    return trace_id_var.get()

def set_trace_id(trace_id: str):
    """Set trace ID for current context."""
    trace_id_var.set(trace_id)

def generate_trace_id() -> str:
    """Generate and set a new trace ID."""
    trace_id = str(uuid.uuid4())[:8]
    trace_id_var.set(trace_id)
    return trace_id

# Convenience function to get logger
def get_logger(name: str = 'main') -> TraceCodeLogger:
    """Get a trace code logger by name."""
    # This will be populated by setup_logging
    return TraceCodeLogger(f'database.{name}', logging.getLogger(f'database.{name}'))

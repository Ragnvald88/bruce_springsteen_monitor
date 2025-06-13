"""
Enhanced logging system for StealthMaster.
Provides structured logging with rich formatting, context tracking, and performance metrics.
"""

import asyncio
import json
import logging
import sys
import time
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Callable
from functools import wraps
import traceback

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.text import Text
from rich.traceback import Traceback


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


class ContextualLogger:
    """Logger with context tracking capabilities."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._context: Dict[str, Any] = {}
        self._timers: Dict[str, float] = {}
    
    def add_context(self, **kwargs):
        """Add context that will be included in all subsequent logs."""
        self._context.update(kwargs)
    
    def remove_context(self, *keys):
        """Remove context keys."""
        for key in keys:
            self._context.pop(key, None)
    
    def clear_context(self):
        """Clear all context."""
        self._context.clear()
    
    @contextmanager
    def context(self, **kwargs):
        """Temporarily add context for logs within the context manager."""
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield
        finally:
            self._context = old_context
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        """Internal log method that adds context."""
        extra = kwargs.get('extra', {})
        extra['extra_fields'] = {**self._context, **kwargs.get('data', {})}
        kwargs['extra'] = extra
        
        # Remove 'data' from kwargs to avoid duplicate
        kwargs.pop('data', None)
        
        self.logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with context."""
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message with context."""
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with context."""
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message with context."""
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with context."""
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def start_timer(self, name: str):
        """Start a named timer."""
        self._timers[name] = time.time()
    
    def stop_timer(self, name: str) -> Optional[float]:
        """Stop a named timer and return elapsed time."""
        if name not in self._timers:
            return None
        
        elapsed = time.time() - self._timers[name]
        del self._timers[name]
        return elapsed
    
    @contextmanager
    def timer(self, operation: str, log_level: int = logging.INFO):
        """Context manager to time an operation."""
        start = time.time()
        self._log(log_level, f"Starting {operation}")
        
        try:
            yield
            elapsed = time.time() - start
            self._log(
                log_level,
                f"Completed {operation}",
                data={"duration_ms": elapsed * 1000, "status": "success"}
            )
        except Exception as e:
            elapsed = time.time() - start
            self._log(
                logging.ERROR,
                f"Failed {operation}",
                data={
                    "duration_ms": elapsed * 1000,
                    "status": "failed",
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    @asynccontextmanager
    async def async_timer(self, operation: str, log_level: int = logging.INFO):
        """Async context manager to time an operation."""
        start = time.time()
        self._log(log_level, f"Starting {operation}")
        
        try:
            yield
            elapsed = time.time() - start
            self._log(
                log_level,
                f"Completed {operation}",
                data={"duration_ms": elapsed * 1000, "status": "success"}
            )
        except Exception as e:
            elapsed = time.time() - start
            self._log(
                logging.ERROR,
                f"Failed {operation}",
                data={
                    "duration_ms": elapsed * 1000,
                    "status": "failed",
                    "error": str(e)
                },
                exc_info=True
            )
            raise


class PerformanceLogger:
    """Logger specialized for performance metrics."""
    
    def __init__(self, logger: ContextualLogger):
        self.logger = logger
        self._metrics: Dict[str, List[float]] = {}
    
    def log_metric(self, name: str, value: float, unit: str = "ms", **tags):
        """Log a performance metric."""
        # Store for aggregation
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(value)
        
        # Log immediately
        self.logger.info(
            f"Performance metric: {name}",
            data={
                "metric_name": name,
                "value": value,
                "unit": unit,
                **tags
            }
        )
    
    def log_operation(self, operation: str, duration_ms: float, success: bool = True, **tags):
        """Log an operation with its duration."""
        self.log_metric(
            f"{operation}_duration",
            duration_ms,
            unit="ms",
            success=success,
            **tags
        )
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if metric_name not in self._metrics:
            return {}
        
        values = self._metrics[metric_name]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "total": sum(values)
        }
    
    def log_summary(self):
        """Log summary of all collected metrics."""
        for metric_name, values in self._metrics.items():
            stats = self.get_stats(metric_name)
            self.logger.info(
                f"Metric summary: {metric_name}",
                data={"metric_name": metric_name, "stats": stats}
            )


class SecurityLogger:
    """Logger for security-sensitive operations."""
    
    def __init__(self, logger: ContextualLogger):
        self.logger = logger
        self._redact_patterns = [
            "password", "token", "api_key", "secret", "auth", "credential"
        ]
    
    def _redact_sensitive(self, data: Any) -> Any:
        """Redact sensitive information from data."""
        if isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                if any(pattern in key.lower() for pattern in self._redact_patterns):
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = self._redact_sensitive(value)
            return redacted
        elif isinstance(data, list):
            return [self._redact_sensitive(item) for item in data]
        elif isinstance(data, str):
            # Redact potential credentials in strings
            if len(data) > 20 and data.isalnum():
                return f"{data[:4]}...[REDACTED]"
            return data
        else:
            return data
    
    def log_auth_attempt(self, platform: str, username: str, success: bool, **extra):
        """Log authentication attempt."""
        self.logger.info(
            f"Authentication attempt on {platform}",
            data=self._redact_sensitive({
                "platform": platform,
                "username": username,
                "success": success,
                **extra
            })
        )
    
    def log_proxy_usage(self, proxy_host: str, success: bool, **extra):
        """Log proxy usage."""
        self.logger.info(
            f"Proxy usage: {proxy_host}",
            data=self._redact_sensitive({
                "proxy_host": proxy_host,
                "success": success,
                **extra
            })
        )
    
    def log_detection_event(self, platform: str, detection_type: str, **extra):
        """Log detection event."""
        self.logger.warning(
            f"Detection event on {platform}",
            data={
                "platform": platform,
                "detection_type": detection_type,
                **extra
            }
        )


def log_function_call(logger: ContextualLogger):
    """Decorator to log function calls with arguments and results."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(
                f"Calling {func_name}",
                data={
                    "function": func_name,
                    "args": str(args)[:100],  # Truncate for readability
                    "kwargs": str(kwargs)[:100]
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                logger.debug(
                    f"Completed {func_name}",
                    data={
                        "function": func_name,
                        "result": str(result)[:100] if result is not None else None
                    }
                )
                return result
            except Exception as e:
                logger.error(
                    f"Failed {func_name}",
                    data={
                        "function": func_name,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(
                f"Calling {func_name}",
                data={
                    "function": func_name,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                }
            )
            
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"Completed {func_name}",
                    data={
                        "function": func_name,
                        "result": str(result)[:100] if result is not None else None
                    }
                )
                return result
            except Exception as e:
                logger.error(
                    f"Failed {func_name}",
                    data={
                        "function": func_name,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class LogManager:
    """Central log management system."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._loggers: Dict[str, ContextualLogger] = {}
        self._console = Console()
        self._log_dir = Path("logs")
        self._log_dir.mkdir(exist_ok=True)
        
        # Setup root logger
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Setup root logger with handlers."""
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        root.handlers = []
        
        # Console handler with Rich
        console_handler = RichHandler(
            console=self._console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        console_handler.setLevel(logging.INFO)
        root.addHandler(console_handler)
        
        # File handler for all logs (JSON format)
        all_logs_path = self._log_dir / f"stealthmaster_{datetime.now():%Y%m%d}.log"
        file_handler = logging.FileHandler(all_logs_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        root.addHandler(file_handler)
        
        # Error file handler
        error_logs_path = self._log_dir / "errors.log"
        error_handler = logging.FileHandler(error_logs_path)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root.addHandler(error_handler)
    
    def get_logger(self, name: str) -> ContextualLogger:
        """Get or create a contextual logger."""
        if name not in self._loggers:
            self._loggers[name] = ContextualLogger(name)
        return self._loggers[name]
    
    def get_performance_logger(self, name: str) -> PerformanceLogger:
        """Get a performance logger."""
        base_logger = self.get_logger(f"{name}.performance")
        return PerformanceLogger(base_logger)
    
    def get_security_logger(self, name: str) -> SecurityLogger:
        """Get a security logger."""
        base_logger = self.get_logger(f"{name}.security")
        return SecurityLogger(base_logger)
    
    def log_table(self, title: str, headers: List[str], rows: List[List[str]]):
        """Log a formatted table to console."""
        table = Table(title=title)
        for header in headers:
            table.add_column(header)
        for row in rows:
            table.add_row(*row)
        self._console.print(table)
    
    def log_statistics(self, stats: Dict[str, Any], title: str = "Statistics"):
        """Log statistics in a nice format."""
        table = Table(title=title)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in stats.items():
            if isinstance(value, float):
                table.add_row(key, f"{value:.2f}")
            else:
                table.add_row(key, str(value))
        
        self._console.print(table)
    
    def set_log_level(self, level: Union[str, int]):
        """Set global log level."""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        
        root = logging.getLogger()
        root.setLevel(level)
        
        # Update console handler
        for handler in root.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(level)


# Singleton instance
log_manager = LogManager()

# Convenience functions
def get_logger(name: str) -> ContextualLogger:
    """Get a contextual logger."""
    return log_manager.get_logger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger."""
    return log_manager.get_performance_logger(name)


def get_security_logger(name: str) -> SecurityLogger:
    """Get a security logger."""
    return log_manager.get_security_logger(name)
# stealthmaster/utils/logging.py
"""Advanced logging configuration for StealthMaster."""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

from rich.logging import RichHandler
from rich.console import Console

from config import LoggingConfig


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "levelno", "lineno", "module", "msecs",
                          "pathname", "process", "processName", "relativeCreated",
                          "thread", "threadName", "exc_info", "exc_text", "stack_info"]:
                log_obj[key] = value
        
        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        # Get color for level
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        
        # Build formatted message
        formatted = f"{color}[{timestamp}] {record.levelname:<8}{self.RESET} "
        formatted += f"{record.name:<30} | {record.getMessage()}"
        
        # Add exception if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class PerformanceLogger:
    """Specialized logger for performance metrics."""
    
    def __init__(self, log_file: Path):
        """Initialize performance logger."""
        self.log_file = log_file
        self._ensure_file()
    
    def _ensure_file(self) -> None:
        """Ensure log file exists with headers."""
        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                f.write("timestamp,metric,value,unit,context\n")
    
    def log_metric(
        self,
        metric: str,
        value: float,
        unit: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a performance metric."""
        timestamp = datetime.utcnow().isoformat()
        context_str = json.dumps(context) if context else ""
        
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp},{metric},{value},{unit},{context_str}\n")


class DetectionLogger:
    """Specialized logger for detection events."""
    
    def __init__(self, log_file: Path):
        """Initialize detection logger."""
        self.log_file = log_file
    
    def log_detection(
        self,
        detection_type: str,
        url: str,
        confidence: float,
        indicators: list,
        recovery_attempted: bool = False,
        recovery_success: bool = False
    ) -> None:
        """Log a detection event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": detection_type,
            "url": url,
            "confidence": confidence,
            "indicators": indicators,
            "recovery_attempted": recovery_attempted,
            "recovery_success": recovery_success,
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + "\n")


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    settings: Optional[LoggingConfig] = None
) -> None:
    """
    Setup comprehensive logging configuration.
    
    Args:
        level: Logging level
        log_dir: Directory for log files
        settings: Logging configuration
    """
    # Default log directory
    if log_dir is None:
        log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with Rich
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=False,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    console_handler.setLevel(getattr(logging, level))
    root_logger.addHandler(console_handler)
    
    # File handlers
    if settings:
        # Main log file
        main_handler = logging.handlers.RotatingFileHandler(
            log_dir / settings.main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        main_handler.setFormatter(JSONFormatter())
        main_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(main_handler)
        
        # Error log file
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / settings.error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        error_handler.setFormatter(JSONFormatter())
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
    
    # Module-specific loggers
    module_loggers = {
        "stealthmaster.stealth": logging.DEBUG if level == "DEBUG" else logging.INFO,
        "stealthmaster.detection": logging.INFO,
        "stealthmaster.profiles": logging.INFO,
        "stealthmaster.browser": logging.INFO,
        "stealthmaster.network": logging.INFO,
        "playwright": logging.WARNING,
        "urllib3": logging.WARNING,
        "asyncio": logging.WARNING,
    }
    
    for module, module_level in module_loggers.items():
        module_logger = logging.getLogger(module)
        module_logger.setLevel(module_level)
    
    # Create specialized loggers if settings provided
    if settings:
        if settings.performance_logging.enabled:
            perf_logger = PerformanceLogger(
                log_dir / settings.performance_logging.log_file
            )
            # Store in logging module for global access
            logging.performance_logger = perf_logger
        
        if settings.detection_logging.enabled:
            detection_logger = DetectionLogger(
                log_dir / settings.detection_logging.log_file
            )
            logging.detection_logger = detection_logger
    
    # Log startup
    logging.info(f"Logging initialized - Level: {level}, Directory: {log_dir}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def log_performance(metric: str, value: float, unit: str = "", **context) -> None:
    """Log a performance metric."""
    if hasattr(logging, "performance_logger"):
        logging.performance_logger.log_metric(metric, value, unit, context)


def log_detection(detection_type: str, url: str, confidence: float, indicators: list, **kwargs) -> None:
    """Log a detection event."""
    if hasattr(logging, "detection_logger"):
        logging.detection_logger.log_detection(
            detection_type, url, confidence, indicators, **kwargs
        )
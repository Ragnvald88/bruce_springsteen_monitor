# src/utils/enhanced_logger.py
"""
Enhanced logging utilities for better monitoring and debugging
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

class TicketDetectionLogger:
    """Specialized logger for ticket detections"""
    
    def __init__(self, log_file: Path):
        self.logger = logging.getLogger('ticket_detection')
        self.logger.setLevel(logging.INFO)
        
        # Create handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # JSON format for easy parsing
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.propagate = False  # Don't propagate to root logger
    
    def log_detection(self, 
                     platform: str,
                     event_name: str,
                     url: str,
                     price: float,
                     section: Optional[str] = None,
                     quantity: Optional[int] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Log a ticket detection event"""
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': 'ticket_detection',
            'platform': platform,
            'event_name': event_name,
            'url': url,
            'price': price,
            'section': section,
            'quantity': quantity,
            'metadata': metadata or {}
        }
        
        self.logger.info(json.dumps(event))
    
    def log_reservation_attempt(self,
                               platform: str,
                               event_name: str,
                               success: bool,
                               error: Optional[str] = None):
        """Log a reservation attempt"""
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': 'reservation_attempt',
            'platform': platform,
            'event_name': event_name,
            'success': success,
            'error': error
        }
        
        self.logger.info(json.dumps(event))


class PerformanceLogger:
    """Specialized logger for performance metrics"""
    
    def __init__(self, log_file: Path):
        self.logger = logging.getLogger('performance')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def log_metrics(self,
                   cpu_percent: float,
                   memory_percent: float,
                   active_tasks: int,
                   queue_size: int,
                   success_rate: float,
                   detection_events: int,
                   response_time_ms: Optional[float] = None):
        """Log performance metrics"""
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': round(cpu_percent, 2),
            'memory_percent': round(memory_percent, 2),
            'active_tasks': active_tasks,
            'queue_size': queue_size,
            'success_rate': round(success_rate, 4),
            'detection_events': detection_events,
            'response_time_ms': round(response_time_ms, 2) if response_time_ms else None
        }
        
        self.logger.info(json.dumps(metrics))
    
    def log_platform_performance(self,
                                platform: str,
                                requests: int,
                                successes: int,
                                failures: int,
                                avg_response_time: float):
        """Log platform-specific performance"""
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'type': 'platform_performance',
            'platform': platform,
            'requests': requests,
            'successes': successes,
            'failures': failures,
            'success_rate': round(successes / max(requests, 1), 4),
            'avg_response_time_ms': round(avg_response_time, 2)
        }
        
        self.logger.info(json.dumps(metrics))


class VerboseLogger:
    """Enhanced verbose logging with color coding and structured output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'TICKET': '\033[92m',    # Bright Green
        'RESET': '\033[0m'
    }
    
    @classmethod
    def setup_console_handler(cls, logger: logging.Logger, use_colors: bool = True):
        """Setup enhanced console handler with colors"""
        
        console_handler = logging.StreamHandler()
        
        if use_colors:
            # Custom formatter with colors
            class ColoredFormatter(logging.Formatter):
                def format(self, record):
                    levelname = record.levelname
                    
                    # Special handling for ticket-related logs
                    if 'TICKET' in record.getMessage().upper():
                        color = cls.COLORS['TICKET']
                    else:
                        color = cls.COLORS.get(levelname, cls.COLORS['RESET'])
                    
                    record.levelname = f"{color}{levelname}{cls.COLORS['RESET']}"
                    record.msg = f"{color}{record.msg}{cls.COLORS['RESET']}"
                    
                    return super().format(record)
            
            formatter = ColoredFormatter(
                '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)


# Global instances
_ticket_logger: Optional[TicketDetectionLogger] = None
_performance_logger: Optional[PerformanceLogger] = None


def setup_enhanced_logging(config: Dict[str, Any], log_dir: Path):
    """Setup enhanced logging based on configuration"""
    
    global _ticket_logger, _performance_logger
    
    # Setup ticket detection logger
    if config.get('log_ticket_detections', True):
        ticket_log_file = log_dir / config.get('ticket_log_file', 'ticket_detections.log')
        _ticket_logger = TicketDetectionLogger(ticket_log_file)
        logging.getLogger(__name__).info(f"📝 Ticket detection logging enabled: {ticket_log_file}")
    
    # Setup performance logger
    if config.get('log_performance_metrics', True):
        perf_log_file = log_dir / config.get('performance_log_file', 'performance.log')
        _performance_logger = PerformanceLogger(perf_log_file)
        logging.getLogger(__name__).info(f"📊 Performance logging enabled: {perf_log_file}")
    
    # Enhanced console logging if verbose
    if config.get('level', 'INFO') == 'DEBUG':
        root_logger = logging.getLogger()
        VerboseLogger.setup_console_handler(root_logger, use_colors=True)


def log_ticket_detection(platform: str, event_name: str, url: str, price: float, **kwargs):
    """Log a ticket detection event"""
    if _ticket_logger:
        _ticket_logger.log_detection(platform, event_name, url, price, **kwargs)
    
    # Also log to main logger at CRITICAL level
    logger = logging.getLogger(__name__)
    logger.critical(f"🎟️ TICKET DETECTED: {event_name} on {platform} - €{price}")


def log_reservation_attempt(platform: str, event_name: str, success: bool, error: Optional[str] = None):
    """Log a reservation attempt"""
    if _ticket_logger:
        _ticket_logger.log_reservation_attempt(platform, event_name, success, error)
    
    logger = logging.getLogger(__name__)
    if success:
        logger.critical(f"✅ RESERVATION SUCCESS: {event_name} on {platform}")
    else:
        logger.error(f"❌ RESERVATION FAILED: {event_name} on {platform} - {error}")


def log_performance_metrics(**metrics):
    """Log performance metrics"""
    if _performance_logger:
        _performance_logger.log_metrics(**metrics)


def log_platform_performance(platform: str, **metrics):
    """Log platform-specific performance"""
    if _performance_logger:
        _performance_logger.log_platform_performance(platform, **metrics)
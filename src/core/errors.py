from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TicketSystemError(Exception):
    """Base exception for ticket system errors"""
    
    def __init__(self, message: str, error_code: str = None, metadata: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN"
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        
    def __str__(self):
        return f"[{self.error_code}] {self.message}"

class BlockedError(TicketSystemError):
    """Raised when bot detection occurs"""
    
    def __init__(self, message: str, platform: str = None, profile_id: str = None):
        super().__init__(message, "BLOCKED")
        self.platform = platform
        self.profile_id = profile_id
        self.metadata.update({
            'platform': platform,
            'profile_id': profile_id,
            'severity': 'HIGH'
        })

class PlatformError(TicketSystemError):
    """Raised when platform-specific errors occur"""
    
    def __init__(self, message: str, platform: str = None, error_type: str = None):
        super().__init__(message, "PLATFORM_ERROR")
        self.platform = platform
        self.error_type = error_type or "UNKNOWN"
        self.metadata.update({
            'platform': platform,
            'error_type': error_type
        })

class ConfigurationError(TicketSystemError):
    """Raised when configuration is invalid"""
    
    def __init__(self, message: str, config_section: str = None):
        super().__init__(message, "CONFIG_ERROR")
        self.config_section = config_section
        self.metadata.update({
            'config_section': config_section
        })

class ProfileError(TicketSystemError):
    """Raised when profile operations fail"""
    
    def __init__(self, message: str, profile_id: str = None):
        super().__init__(message, "PROFILE_ERROR")
        self.profile_id = profile_id
        self.metadata.update({
            'profile_id': profile_id
        })

class NetworkError(TicketSystemError):
    """Raised when network operations fail"""
    
    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(message, "NETWORK_ERROR")
        self.url = url
        self.status_code = status_code
        self.metadata.update({
            'url': url,
            'status_code': status_code
        })

class RateLimitError(TicketSystemError):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message, "RATE_LIMIT")
        self.retry_after = retry_after
        self.metadata.update({
            'retry_after': retry_after
        })

class AuthenticationError(TicketSystemError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str, platform: str = None):
        super().__init__(message, "AUTH_ERROR")
        self.platform = platform
        self.metadata.update({
            'platform': platform
        })

class ValidationError(TicketSystemError):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value
        self.metadata.update({
            'field': field,
            'value': str(value) if value is not None else None
        })

class StrikeError(TicketSystemError):
    """Raised when strike operations fail"""
    
    def __init__(self, message: str, opportunity_id: str = None, attempt_count: int = None):
        super().__init__(message, "STRIKE_ERROR")
        self.opportunity_id = opportunity_id
        self.attempt_count = attempt_count
        self.metadata.update({
            'opportunity_id': opportunity_id,
            'attempt_count': attempt_count
        })

class ResourceError(TicketSystemError):
    """Raised when system resources are exhausted"""
    
    def __init__(self, message: str, resource_type: str = None):
        super().__init__(message, "RESOURCE_ERROR")
        self.resource_type = resource_type
        self.metadata.update({
            'resource_type': resource_type
        })

# Error handler utility functions
class ErrorHandler:
    """Centralized error handling and logging"""
    
    @staticmethod
    def log_error(error: Exception, context: str = None, extra_data: Dict[str, Any] = None):
        """Log error with proper context and metadata"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        if isinstance(error, TicketSystemError):
            error_data.update({
                'error_code': error.error_code,
                'timestamp': error.timestamp.isoformat(),
                'metadata': error.metadata
            })
        
        if extra_data:
            error_data.update(extra_data)
        
        logger.error(f"Error in {context}: {error}", extra=error_data)
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """Determine if an error is retryable"""
        if isinstance(error, (NetworkError, RateLimitError)):
            return True
        
        if isinstance(error, BlockedError):
            return False  # Don't retry blocked errors immediately
        
        if isinstance(error, PlatformError):
            # Retry some platform errors
            retryable_types = ['TIMEOUT', 'CONNECTION', 'TEMPORARY']
            return hasattr(error, 'error_type') and error.error_type in retryable_types
        
        return False
    
    @staticmethod
    def get_retry_delay(error: Exception, attempt_count: int) -> float:
        """Get appropriate retry delay based on error type"""
        base_delay = 1.0
        
        if isinstance(error, RateLimitError) and error.retry_after:
            return float(error.retry_after)
        
        if isinstance(error, BlockedError):
            return 300.0  # 5 minutes for blocked errors
        
        if isinstance(error, NetworkError):
            return min(base_delay * (2 ** attempt_count), 60.0)  # Exponential backoff
        
        return base_delay * attempt_count

# Error metrics tracking
class ErrorMetrics:
    """Track error statistics for monitoring"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.last_errors: List[Dict[str, Any]] = []
        self.max_recent_errors = 100
    
    def record_error(self, error: Exception, context: str = None):
        """Record error occurrence"""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': str(error),
            'context': context
        }
        
        if isinstance(error, TicketSystemError):
            error_record.update({
                'error_code': error.error_code,
                'metadata': error.metadata
            })
        
        self.last_errors.append(error_record)
        
        # Keep only recent errors
        if len(self.last_errors) > self.max_recent_errors:
            self.last_errors = self.last_errors[-self.max_recent_errors:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error statistics summary"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts.copy(),
            'recent_errors_count': len(self.last_errors),
            'most_common_errors': sorted(
                self.error_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }

# Global error metrics instance
error_metrics = ErrorMetrics()

# Custom exception for specific use cases
class CaptchaError(BlockedError):
    """Raised when CAPTCHA is encountered"""
    
    def __init__(self, message: str = "CAPTCHA detected", platform: str = None):
        super().__init__(message, platform)
        self.error_code = "CAPTCHA_DETECTED"

class GeoblockError(BlockedError):
    """Raised when geographic blocking is detected"""
    
    def __init__(self, message: str = "Geographic blocking detected", platform: str = None):
        super().__init__(message, platform)
        self.error_code = "GEOBLOCKED"

class MaintenanceError(PlatformError):
    """Raised when platform is under maintenance"""
    
    def __init__(self, message: str = "Platform under maintenance", platform: str = None):
        super().__init__(message, platform, "MAINTENANCE")
        self.error_code = "PLATFORM_MAINTENANCE"

class InventoryError(PlatformError):
    """Raised when inventory-related errors occur"""
    
    def __init__(self, message: str, platform: str = None, item_id: str = None):
        super().__init__(message, platform, "INVENTORY")
        self.item_id = item_id
        self.metadata.update({'item_id': item_id})

# Context managers for error handling
class ErrorContext:
    """Context manager for handling errors in specific contexts"""
    
    def __init__(self, context_name: str, suppress_errors: bool = False):
        self.context_name = context_name
        self.suppress_errors = suppress_errors
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            ErrorHandler.log_error(exc_val, self.context_name)
            error_metrics.record_error(exc_val, self.context_name)
            
            if self.suppress_errors:
                return True  # Suppress the exception
        
        return False  # Let the exception propagate
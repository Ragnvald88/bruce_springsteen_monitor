"""
Enhanced Error Handler with Context and Recovery Suggestions
Provides structured error analysis and actionable solutions
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ErrorContext:
    """Structured error handling with recovery suggestions"""
    
    ERROR_PATTERNS = {
        # Network errors
        'timeout': {
            'patterns': ['timeout', 'timed out', 'navigation timeout'],
            'category': 'NETWORK',
            'message': 'Network timeout occurred',
            'suggestion': 'Check your internet connection and proxy settings'
        },
        'connection_refused': {
            'patterns': ['connection refused', 'ECONNREFUSED', 'failed to connect'],
            'category': 'NETWORK',
            'message': 'Connection refused by server',
            'suggestion': 'Server may be down or blocking your IP. Try using a proxy.'
        },
        'dns_failed': {
            'patterns': ['dns', 'ENOTFOUND', 'getaddrinfo', 'name resolution'],
            'category': 'NETWORK',
            'message': 'DNS resolution failed',
            'suggestion': 'Check the URL is correct and your DNS settings'
        },
        
        # Detection/blocking errors
        'akamai_block': {
            'patterns': ['akamai', 'edgesuite', '_abck', 'sensor_data'],
            'category': 'DETECTION',
            'message': 'Akamai bot protection triggered',
            'suggestion': 'Applying enhanced stealth measures...'
        },
        'cloudflare_block': {
            'patterns': ['cloudflare', 'cf-ray', 'checking your browser'],
            'category': 'DETECTION',
            'message': 'Cloudflare challenge detected',
            'suggestion': 'Waiting for challenge to complete...'
        },
        'access_denied': {
            'patterns': ['403', 'forbidden', 'access denied', 'blocked'],
            'category': 'DETECTION',
            'message': 'Access denied by website',
            'suggestion': 'Rotating browser fingerprint and retrying...'
        },
        'rate_limit': {
            'patterns': ['429', 'rate limit', 'too many requests'],
            'category': 'DETECTION',
            'message': 'Rate limited by server',
            'suggestion': 'Backing off and reducing request frequency'
        },
        
        # Authentication errors
        'login_failed': {
            'patterns': ['login failed', 'invalid credentials', 'authentication failed'],
            'category': 'AUTH',
            'message': 'Login failed',
            'suggestion': 'Check your credentials in config.yaml'
        },
        'session_expired': {
            'patterns': ['session expired', 'please log in', 'not authenticated'],
            'category': 'AUTH',
            'message': 'Session has expired',
            'suggestion': 'Re-authenticating automatically...'
        },
        
        # Browser errors
        'page_crash': {
            'patterns': ['page crashed', 'target closed', 'disconnected'],
            'category': 'BROWSER',
            'message': 'Browser page crashed',
            'suggestion': 'Restarting browser...'
        },
        'element_not_found': {
            'patterns': ['element not found', 'no such element', 'waiting for selector'],
            'category': 'BROWSER',
            'message': 'Required element not found on page',
            'suggestion': 'Page structure may have changed. Updating selectors...'
        }
    }
    
    @classmethod
    def analyze_error(cls, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze error and provide actionable feedback
        
        Args:
            error: The exception that occurred
            context: Additional context (platform, url, etc)
            
        Returns:
            Analysis result with category, message, and suggestion
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Try to match error patterns
        for key, pattern_info in cls.ERROR_PATTERNS.items():
            if any(pattern in error_str for pattern in pattern_info['patterns']):
                return {
                    'error_key': key,
                    'category': pattern_info['category'],
                    'message': pattern_info['message'],
                    'suggestion': pattern_info['suggestion'],
                    'original_error': str(error),
                    'error_type': error_type,
                    'context': context or {},
                    'timestamp': datetime.now().isoformat()
                }
        
        # Default response for unknown errors
        return {
            'error_key': 'unknown',
            'category': 'UNKNOWN',
            'message': f'Unexpected error: {error_type}',
            'suggestion': 'Check logs for details. This may be a new issue.',
            'original_error': str(error),
            'error_type': error_type,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
    
    @classmethod
    def get_recovery_action(cls, error_analysis: Dict[str, Any]) -> Optional[str]:
        """
        Get specific recovery action based on error analysis
        
        Args:
            error_analysis: Result from analyze_error
            
        Returns:
            Recovery action identifier or None
        """
        recovery_map = {
            'akamai_block': 'apply_akamai_bypass',
            'cloudflare_block': 'wait_for_challenge',
            'access_denied': 'rotate_fingerprint',
            'rate_limit': 'backoff_retry',
            'session_expired': 're_authenticate',
            'page_crash': 'restart_browser',
            'connection_refused': 'switch_proxy',
            'timeout': 'increase_timeout'
        }
        
        return recovery_map.get(error_analysis['error_key'])
    
    @classmethod
    def format_error_message(cls, error_analysis: Dict[str, Any], platform: str = None) -> str:
        """
        Format error message for console output
        
        Args:
            error_analysis: Result from analyze_error
            platform: Platform name for context
            
        Returns:
            Formatted error message
        """
        icon_map = {
            'NETWORK': '🌐',
            'DETECTION': '🚫',
            'AUTH': '🔐',
            'BROWSER': '💥',
            'UNKNOWN': '❓'
        }
        
        icon = icon_map.get(error_analysis['category'], '❌')
        platform_str = f"[{platform}] " if platform else ""
        
        return (
            f"{icon} {platform_str}{error_analysis['message']}\n"
            f"    💡 {error_analysis['suggestion']}"
        )
    
    @classmethod
    def should_retry(cls, error_analysis: Dict[str, Any], retry_count: int) -> Tuple[bool, int]:
        """
        Determine if operation should be retried and suggested delay
        
        Args:
            error_analysis: Result from analyze_error
            retry_count: Current retry attempt number
            
        Returns:
            Tuple of (should_retry, delay_seconds)
        """
        # Errors that should always retry (with backoff)
        always_retry = {
            'timeout': (True, min(30, 5 * (2 ** retry_count))),
            'rate_limit': (True, min(300, 60 * (2 ** retry_count))),
            'page_crash': (True, 10),
            'session_expired': (True, 5)
        }
        
        # Errors that should retry up to a limit
        limited_retry = {
            'akamai_block': (retry_count < 3, 30),
            'cloudflare_block': (retry_count < 3, 20),
            'access_denied': (retry_count < 5, 60),
            'connection_refused': (retry_count < 3, 15)
        }
        
        error_key = error_analysis['error_key']
        
        if error_key in always_retry:
            return always_retry[error_key]
        elif error_key in limited_retry:
            should_retry, delay = limited_retry[error_key]
            return (should_retry, delay if should_retry else 0)
        else:
            # Unknown errors: retry up to 2 times
            return (retry_count < 2, 10)


class ErrorRecovery:
    """Implement specific recovery strategies"""
    
    @staticmethod
    async def apply_akamai_bypass(page, browser_manager) -> bool:
        """Apply enhanced Akamai bypass techniques"""
        try:
            from ..stealth.akamai_bypass import AkamaiBypass
            await AkamaiBypass.apply_bypass(page)
            await page.reload()
            return True
        except Exception as e:
            logger.error(f"Failed to apply Akamai bypass: {e}")
            return False
    
    @staticmethod
    async def rotate_fingerprint(browser_id: str, browser_manager) -> bool:
        """Rotate browser fingerprint"""
        try:
            # Implementation would regenerate fingerprint
            logger.info("Rotating browser fingerprint...")
            return True
        except Exception as e:
            logger.error(f"Failed to rotate fingerprint: {e}")
            return False
    
    @staticmethod
    async def backoff_retry(delay: int) -> bool:
        """Implement exponential backoff"""
        import asyncio
        logger.info(f"Backing off for {delay} seconds...")
        await asyncio.sleep(delay)
        return True


# Global error handler instance
error_handler = ErrorContext()

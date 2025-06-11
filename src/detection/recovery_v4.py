"""
V4 Recovery System - Simplified and Reliable
Based on V1's proven approach with V4 enhancements
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
from enum import Enum

from ..utils.logging import get_logger
from ..database.statistics import stats_manager

logger = get_logger(__name__)


class DetectionType(Enum):
    """Types of bot detection"""
    CAPTCHA = "captcha"
    RATE_LIMIT = "rate_limit"
    SESSION_EXPIRED = "session_expired"
    IP_BLOCK = "ip_block"
    BROWSER_CHALLENGE = "browser_challenge"
    UNKNOWN = "unknown"


class RecoveryStrategy:
    """Base recovery strategy"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Execute recovery strategy"""
        raise NotImplementedError


class CaptchaRecovery(RecoveryStrategy):
    """Simple CAPTCHA recovery - V1 style"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        try:
            page = context.get("page")
            
            # Wait for user to solve CAPTCHA manually
            logger.info("CAPTCHA detected - waiting for manual solve...")
            
            # Simple approach: wait and check periodically
            for i in range(30):  # 30 second timeout
                await asyncio.sleep(1)
                
                # Check if CAPTCHA is still present
                if hasattr(page, "query_selector"):
                    # Playwright
                    captcha = await page.query_selector("[class*='captcha'], [id*='captcha']")
                    if not captcha:
                        logger.info("CAPTCHA solved!")
                        return True
                else:
                    # Selenium
                    try:
                        page.find_element("css selector", "[class*='captcha'], [id*='captcha']")
                    except:
                        logger.info("CAPTCHA solved!")
                        return True
            
            logger.warning("CAPTCHA timeout")
            return False
            
        except Exception as e:
            logger.error(f"CAPTCHA recovery failed: {e}")
            return False


class RateLimitRecovery(RecoveryStrategy):
    """Rate limit recovery - simple backoff"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        try:
            wait_time = context.get("wait_time", 5)
            logger.info(f"Rate limit detected - waiting {wait_time}s...")
            
            await asyncio.sleep(wait_time)
            
            # Exponential backoff for next attempt
            context["wait_time"] = min(wait_time * 2, 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit recovery failed: {e}")
            return False


class SessionRecovery(RecoveryStrategy):
    """Session recovery - refresh and retry"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        try:
            page = context.get("page")
            platform = context.get("platform")
            
            logger.info("Session expired - refreshing...")
            
            # Simple page refresh
            if hasattr(page, "reload"):
                await page.reload()
            else:
                page.refresh()
            
            await asyncio.sleep(2)
            
            # Trigger re-login through platform handler
            if platform and hasattr(platform, "ensure_logged_in"):
                return await platform.ensure_logged_in(page)
            
            return True
            
        except Exception as e:
            logger.error(f"Session recovery failed: {e}")
            return False


class IPBlockRecovery(RecoveryStrategy):
    """IP block recovery - switch proxy if available"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        try:
            logger.warning("IP block detected")
            
            # In V4, we rely on proxy rotation in nodriver_core
            # For now, just wait and hope proxy rotates
            await asyncio.sleep(10)
            
            return True
            
        except Exception as e:
            logger.error(f"IP block recovery failed: {e}")
            return False


class V4RecoveryEngine:
    """
    Simplified recovery engine based on V1's reliable approach
    """
    
    def __init__(self):
        self.strategies = {
            DetectionType.CAPTCHA: CaptchaRecovery(),
            DetectionType.RATE_LIMIT: RateLimitRecovery(),
            DetectionType.SESSION_EXPIRED: SessionRecovery(),
            DetectionType.IP_BLOCK: IPBlockRecovery()
        }
        
        self._recovery_stats = {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "by_type": {}
        }
    
    def detect_issue(self, page: Any, error: Optional[Exception] = None) -> Optional[DetectionType]:
        """Detect what type of issue occurred"""
        try:
            # Check error message
            if error:
                error_str = str(error).lower()
                
                if "captcha" in error_str:
                    return DetectionType.CAPTCHA
                elif "rate" in error_str or "too many" in error_str:
                    return DetectionType.RATE_LIMIT
                elif "session" in error_str or "expired" in error_str:
                    return DetectionType.SESSION_EXPIRED
                elif "blocked" in error_str or "forbidden" in error_str:
                    return DetectionType.IP_BLOCK
            
            # Check page content
            if hasattr(page, "content"):
                # Playwright
                content = asyncio.run(page.content())
            else:
                # Selenium
                content = page.page_source
            
            content_lower = content.lower()
            
            # Pattern matching
            if "captcha" in content_lower or "recaptcha" in content_lower:
                return DetectionType.CAPTCHA
            elif "rate limit" in content_lower or "too many requests" in content_lower:
                return DetectionType.RATE_LIMIT
            elif "session expired" in content_lower or "please login" in content_lower:
                return DetectionType.SESSION_EXPIRED
            elif "access denied" in content_lower or "blocked" in content_lower:
                return DetectionType.IP_BLOCK
            
            return None
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return DetectionType.UNKNOWN
    
    async def recover(self, page: Any, detection_type: DetectionType, 
                     platform: Optional[Any] = None) -> bool:
        """
        Attempt recovery from detected issue
        
        Args:
            page: Browser page
            detection_type: Type of detection
            platform: Platform handler for context
            
        Returns:
            Success status
        """
        start_time = time.time()
        self._recovery_stats["attempts"] += 1
        
        try:
            strategy = self.strategies.get(detection_type)
            if not strategy:
                logger.warning(f"No recovery strategy for {detection_type}")
                return False
            
            # Create context
            context = {
                "page": page,
                "platform": platform,
                "detection_type": detection_type,
                "attempt": 1
            }
            
            # Execute recovery
            success = await strategy.execute(context)
            
            # Update stats
            recovery_time = (time.time() - start_time) * 1000
            
            if success:
                self._recovery_stats["successes"] += 1
                logger.info(f"Recovery successful for {detection_type.value} in {recovery_time:.0f}ms")
            else:
                self._recovery_stats["failures"] += 1
                logger.warning(f"Recovery failed for {detection_type.value}")
            
            # Track in database
            stats_manager.record_performance_metric(
                f"recovery_{detection_type.value}",
                "recovery",
                recovery_time,
                success=success,
                platform=platform.__class__.__name__ if platform else None
            )
            
            # Update type-specific stats
            if detection_type.value not in self._recovery_stats["by_type"]:
                self._recovery_stats["by_type"][detection_type.value] = {
                    "attempts": 0, "successes": 0
                }
            
            self._recovery_stats["by_type"][detection_type.value]["attempts"] += 1
            if success:
                self._recovery_stats["by_type"][detection_type.value]["successes"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Recovery error: {e}")
            self._recovery_stats["failures"] += 1
            return False
    
    async def auto_recover(self, page: Any, error: Optional[Exception] = None,
                          platform: Optional[Any] = None) -> bool:
        """
        Automatically detect and recover from issues
        
        Args:
            page: Browser page
            error: Optional error that occurred
            platform: Platform handler
            
        Returns:
            Success status
        """
        detection_type = self.detect_issue(page, error)
        
        if detection_type:
            logger.info(f"Auto-detected issue: {detection_type.value}")
            return await self.recover(page, detection_type, platform)
        
        logger.warning("No issue detected for recovery")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        stats = self._recovery_stats.copy()
        
        # Calculate success rate
        if stats["attempts"] > 0:
            stats["success_rate"] = (stats["successes"] / stats["attempts"]) * 100
        else:
            stats["success_rate"] = 0
        
        return stats
    
    def reset_stats(self):
        """Reset recovery statistics"""
        self._recovery_stats = {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "by_type": {}
        }
        logger.info("Recovery stats reset")


# Global instance
recovery_engine = V4RecoveryEngine()
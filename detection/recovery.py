# stealthmaster/detection/recovery.py
"""Recovery strategies for detection events."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import random

from playwright.async_api import Page, BrowserContext

from detection.monitor import DetectionType, DetectionEvent

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Types of recovery actions."""
    
    WAIT = "wait"
    REFRESH = "refresh"
    CLEAR_COOKIES = "clear_cookies"
    ROTATE_PROXY = "rotate_proxy"
    ROTATE_PROFILE = "rotate_profile"
    SWITCH_CONTEXT = "switch_context"
    HUMAN_SIMULATION = "human_simulation"
    STEALTH_UPGRADE = "stealth_upgrade"
    CAPTCHA_SOLVE = "captcha_solve"
    ABORT = "abort"


class RecoveryStatus(Enum):
    """Status of recovery attempt."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class RecoveryStrategy:
    """Implements recovery strategies for various detection scenarios."""
    
    def __init__(self):
        """Initialize recovery strategy system."""
        self._strategies = self._load_strategies()
        self._recovery_history: List[Dict[str, Any]] = []
        self._cooldowns: Dict[str, datetime] = {}
    
    def _load_strategies(self) -> Dict[DetectionType, List[Dict[str, Any]]]:
        """Load recovery strategies for each detection type."""
        return {
            DetectionType.CAPTCHA: [
                {
                    "action": RecoveryAction.CAPTCHA_SOLVE,
                    "priority": 1,
                    "timeout": 300,
                    "description": "Attempt to solve CAPTCHA"
                },
                {
                    "action": RecoveryAction.HUMAN_SIMULATION,
                    "priority": 2,
                    "timeout": 30,
                    "description": "Simulate human behavior before retry"
                }
            ],
            DetectionType.CLOUDFLARE: [
                {
                    "action": RecoveryAction.WAIT,
                    "priority": 1,
                    "duration": 5,
                    "description": "Wait for challenge to complete"
                },
                {
                    "action": RecoveryAction.STEALTH_UPGRADE,
                    "priority": 2,
                    "description": "Enhance stealth measures"
                },
                {
                    "action": RecoveryAction.ROTATE_PROXY,
                    "priority": 3,
                    "description": "Switch to different proxy"
                }
            ],
            DetectionType.RATE_LIMIT: [
                {
                    "action": RecoveryAction.WAIT,
                    "priority": 1,
                    "duration": 60,
                    "description": "Wait for rate limit to clear"
                },
                {
                    "action": RecoveryAction.ROTATE_PROXY,
                    "priority": 2,
                    "description": "Switch IP address"
                },
                {
                    "action": RecoveryAction.ROTATE_PROFILE,
                    "priority": 3,
                    "description": "Switch browser profile"
                }
            ],
            DetectionType.FINGERPRINT: [
                {
                    "action": RecoveryAction.ROTATE_PROFILE,
                    "priority": 1,
                    "description": "Change browser fingerprint"
                },
                {
                    "action": RecoveryAction.STEALTH_UPGRADE,
                    "priority": 2,
                    "description": "Enhance fingerprint spoofing"
                },
                {
                    "action": RecoveryAction.SWITCH_CONTEXT,
                    "priority": 3,
                    "description": "Create new browser context"
                }
            ],
            DetectionType.BEHAVIORAL: [
                {
                    "action": RecoveryAction.HUMAN_SIMULATION,
                    "priority": 1,
                    "timeout": 60,
                    "description": "Extensive human behavior simulation"
                },
                {
                    "action": RecoveryAction.WAIT,
                    "priority": 2,
                    "duration": 30,
                    "description": "Random wait period"
                }
            ],
            DetectionType.CDP_DETECTION: [
                {
                    "action": RecoveryAction.STEALTH_UPGRADE,
                    "priority": 1,
                    "description": "Apply CDP bypass techniques"
                },
                {
                    "action": RecoveryAction.SWITCH_CONTEXT,
                    "priority": 2,
                    "description": "Create CDP-free context"
                }
            ],
            DetectionType.IP_BLOCK: [
                {
                    "action": RecoveryAction.ROTATE_PROXY,
                    "priority": 1,
                    "description": "Change to new IP address"
                },
                {
                    "action": RecoveryAction.WAIT,
                    "priority": 2,
                    "duration": 300,
                    "description": "Wait for block to expire"
                }
            ]
        }
    
    async def attempt_recovery(
        self,
        page: Page,
        detection_type: DetectionType,
        detection_details: Dict[str, Any],
        custom_strategies: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Attempt recovery from detection.
        
        Args:
            page: Page that triggered detection
            detection_type: Type of detection
            detection_details: Detection event details
            custom_strategies: Optional custom recovery strategies
            
        Returns:
            Success status
        """
        logger.info(f"Attempting recovery from {detection_type.value} detection")
        
        # Check cooldown
        if self._is_in_cooldown(page.url, detection_type):
            logger.warning("Recovery in cooldown period, skipping")
            return False
        
        # Get strategies
        strategies = custom_strategies or self._strategies.get(detection_type, [])
        if not strategies:
            logger.warning(f"No recovery strategies for {detection_type.value}")
            return False
        
        # Sort by priority
        strategies = sorted(strategies, key=lambda s: s.get("priority", 999))
        
        # Try each strategy
        for strategy in strategies:
            record = {
                "timestamp": datetime.now(),
                "detection_type": detection_type,
                "url": page.url,
                "action": strategy["action"],
                "status": RecoveryStatus.PENDING
            }
            self._recovery_history.append(record)
            
            try:
                success = await self._execute_strategy(
                    page,
                    strategy,
                    detection_details
                )
                
                record["status"] = RecoveryStatus.SUCCESS if success else RecoveryStatus.FAILED
                
                if success:
                    logger.info(f"Recovery successful using {strategy['action'].value}")
                    self._set_cooldown(page.url, detection_type)
                    return True
                    
            except Exception as e:
                logger.error(f"Recovery strategy error: {e}")
                record["status"] = RecoveryStatus.FAILED
                record["error"] = str(e)
        
        logger.error(f"All recovery strategies failed for {detection_type.value}")
        return False
    
    async def _execute_strategy(
        self,
        page: Page,
        strategy: Dict[str, Any],
        detection_details: Dict[str, Any]
    ) -> bool:
        """Execute a specific recovery strategy."""
        action = strategy["action"]
        
        logger.info(f"Executing recovery action: {action.value}")
        
        if action == RecoveryAction.WAIT:
            duration = strategy.get("duration", 30)
            await self._action_wait(page, duration)
            return True
            
        elif action == RecoveryAction.REFRESH:
            return await self._action_refresh(page)
            
        elif action == RecoveryAction.CLEAR_COOKIES:
            return await self._action_clear_cookies(page)
            
        elif action == RecoveryAction.HUMAN_SIMULATION:
            timeout = strategy.get("timeout", 30)
            return await self._action_human_simulation(page, timeout)
            
        elif action == RecoveryAction.CAPTCHA_SOLVE:
            return await self._action_captcha_solve(page, detection_details)
            
        elif action == RecoveryAction.STEALTH_UPGRADE:
            return await self._action_stealth_upgrade(page)
            
        elif action == RecoveryAction.ROTATE_PROXY:
            return await self._action_rotate_proxy(page)
            
        elif action == RecoveryAction.ROTATE_PROFILE:
            return await self._action_rotate_profile(page)
            
        elif action == RecoveryAction.SWITCH_CONTEXT:
            return await self._action_switch_context(page)
            
        else:
            logger.warning(f"Unknown recovery action: {action}")
            return False
    
    async def _action_wait(self, page: Page, duration: int) -> None:
        """Wait for specified duration with randomization."""
        # Add 20% randomization
        actual_duration = duration + random.uniform(-duration * 0.2, duration * 0.2)
        
        logger.info(f"Waiting {actual_duration:.1f} seconds...")
        await asyncio.sleep(actual_duration)
    
    async def _action_refresh(self, page: Page) -> bool:
        """Refresh the page."""
        try:
            await page.reload(wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            return True
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            return False
    
    async def _action_clear_cookies(self, page: Page) -> bool:
        """Clear cookies for current domain."""
        try:
            # Get current domain
            domain = await page.evaluate("window.location.hostname")
            
            # Clear cookies
            context = page.context
            cookies = await context.cookies()
            
            for cookie in cookies:
                if domain in cookie.get("domain", ""):
                    await context.clear_cookies()
                    break
            
            logger.info(f"Cleared cookies for {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Cookie clearing failed: {e}")
            return False
    
    async def _action_human_simulation(self, page: Page, timeout: int) -> bool:
        """Simulate human behavior patterns."""
        try:
            end_time = datetime.now() + timedelta(seconds=timeout)
            
            while datetime.now() < end_time:
                # Random mouse movements
                viewport = page.viewport_size
                if viewport:
                    x = random.randint(100, viewport["width"] - 100)
                    y = random.randint(100, viewport["height"] - 100)
                    await page.mouse.move(x, y)
                
                # Random scrolling
                if random.random() < 0.3:
                    scroll_amount = random.randint(-200, 200)
                    await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                
                # Random clicking on safe elements
                if random.random() < 0.1:
                    safe_elements = await page.query_selector_all("a, button")
                    if safe_elements:
                        element = random.choice(safe_elements[:5])
                        box = await element.bounding_box()
                        if box:
                            await page.mouse.move(
                                box["x"] + box["width"] / 2,
                                box["y"] + box["height"] / 2
                            )
                
                # Variable delays
                await asyncio.sleep(random.uniform(0.5, 3))
            
            return True
            
        except Exception as e:
            logger.error(f"Human simulation failed: {e}")
            return False
    
    async def _action_captcha_solve(self, page: Page, detection_details: Dict[str, Any]) -> bool:
        """Handle CAPTCHA solving."""
        try:
            # Import here to avoid circular dependency
            from detection.captcha import CaptchaHandler
            
            handler = CaptchaHandler()
            result = await handler.handle(page)
            
            return result["status"].value == "solved"
            
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return False
    
    async def _action_stealth_upgrade(self, page: Page) -> bool:
        """Enhance stealth measures."""
        try:
            # Inject additional evasion scripts
            await page.add_init_script("""
                // Enhanced CDP evasion
                (() => {
                    // Override console methods that might leak CDP
                    const methods = ['debug', 'log', 'warn', 'error'];
                    methods.forEach(method => {
                        const original = console[method];
                        console[method] = function(...args) {
                            // Filter out CDP-related logs
                            const stack = new Error().stack;
                            if (stack && stack.includes('Runtime.')) return;
                            return original.apply(console, args);
                        };
                    });
                    
                    // Additional fingerprint randomization
                    const randomOffset = () => Math.random() * 0.0001;
                    
                    if (window.screen) {
                        Object.defineProperty(window.screen, 'width', {
                            get: function() { return 1920 + Math.floor(randomOffset() * 100); }
                        });
                    }
                })();
            """)
            
            logger.info("Applied enhanced stealth measures")
            return True
            
        except Exception as e:
            logger.error(f"Stealth upgrade failed: {e}")
            return False
    
    async def _action_rotate_proxy(self, page: Page) -> bool:
        """Rotate to a different proxy."""
        # This would integrate with proxy management
        logger.warning("Proxy rotation not implemented in recovery")
        return False
    
    async def _action_rotate_profile(self, page: Page) -> bool:
        """Rotate browser profile."""
        # This would integrate with profile management
        logger.warning("Profile rotation not implemented in recovery")
        return False
    
    async def _action_switch_context(self, page: Page) -> bool:
        """Switch to new browser context."""
        # This would create a new context
        logger.warning("Context switching not implemented in recovery")
        return False
    
    def _is_in_cooldown(self, url: str, detection_type: DetectionType) -> bool:
        """Check if recovery is in cooldown."""
        key = f"{url}:{detection_type.value}"
        
        if key in self._cooldowns:
            cooldown_until = self._cooldowns[key]
            if datetime.now() < cooldown_until:
                remaining = (cooldown_until - datetime.now()).seconds
                logger.info(f"Recovery cooldown active for {remaining}s")
                return True
            else:
                del self._cooldowns[key]
        
        return False
    
    def _set_cooldown(self, url: str, detection_type: DetectionType) -> None:
        """Set recovery cooldown."""
        key = f"{url}:{detection_type.value}"
        
        # Cooldown duration based on detection type
        cooldown_durations = {
            DetectionType.RATE_LIMIT: 300,  # 5 minutes
            DetectionType.IP_BLOCK: 600,    # 10 minutes
            DetectionType.CLOUDFLARE: 120,  # 2 minutes
            DetectionType.CAPTCHA: 60,      # 1 minute
        }
        
        duration = cooldown_durations.get(detection_type, 180)
        self._cooldowns[key] = datetime.now() + timedelta(seconds=duration)
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        total = len(self._recovery_history)
        
        if total == 0:
            return {
                "total_recoveries": 0,
                "success_rate": 0.0,
                "by_type": {},
                "by_action": {}
            }
        
        # Calculate success rate
        successful = sum(
            1 for r in self._recovery_history
            if r["status"] == RecoveryStatus.SUCCESS
        )
        success_rate = successful / total
        
        # Group by detection type
        by_type = {}
        for record in self._recovery_history:
            det_type = record["detection_type"].value
            if det_type not in by_type:
                by_type[det_type] = {"total": 0, "success": 0}
            
            by_type[det_type]["total"] += 1
            if record["status"] == RecoveryStatus.SUCCESS:
                by_type[det_type]["success"] += 1
        
        # Group by action
        by_action = {}
        for record in self._recovery_history:
            action = record["action"].value
            if action not in by_action:
                by_action[action] = {"total": 0, "success": 0}
            
            by_action[action]["total"] += 1
            if record["status"] == RecoveryStatus.SUCCESS:
                by_action[action]["success"] += 1
        
        return {
            "total_recoveries": total,
            "success_rate": success_rate,
            "by_type": by_type,
            "by_action": by_action,
            "active_cooldowns": len(self._cooldowns),
            "recent_recoveries": self._recovery_history[-10:]
        }
    
    def register_custom_action(
        self,
        action_name: str,
        handler: Callable,
        description: str = ""
    ) -> None:
        """
        Register a custom recovery action.
        
        Args:
            action_name: Name for the action
            handler: Async function to handle recovery
            description: Action description
        """
        # Create custom action enum value
        custom_action = RecoveryAction(action_name)
        
        # Store handler
        setattr(self, f"_action_{action_name}", handler)
        
        logger.info(f"Registered custom recovery action: {action_name}")
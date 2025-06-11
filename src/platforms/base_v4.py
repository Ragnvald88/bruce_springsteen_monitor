"""
V4 Base Platform Handler
Abstract base class for all platform implementations with V4 enhancements
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import time
from datetime import datetime

from ..browser.pool_v4 import v4_pool
from ..database.statistics import stats_manager
from ..detection.recovery_v4 import recovery_engine
from ..utils.logging import get_logger
from ..config import TargetConfig

logger = get_logger(__name__)


class V4PlatformHandler(ABC):
    """
    Base class for V4 platform handlers with enhanced features
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = self.__class__.__name__.replace("Handler", "").lower()
        self._session_id = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Platform-specific selectors (to be defined by subclasses)
        self.selectors = {}
        
        # Performance tracking
        self._operation_times = []
        self._success_count = 0
        self._failure_count = 0
        
        logger.info(f"V4 {self.name} handler initialized")
    
    @abstractmethod
    async def search_tickets(self, page: Any, event_name: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for available tickets
        
        Args:
            page: Browser page (Selenium or Playwright)
            event_name: Event to search for
            **kwargs: Additional search parameters
            
        Returns:
            List of available tickets with metadata
        """
        pass
    
    @abstractmethod
    async def select_tickets(self, page: Any, tickets: List[Dict[str, Any]], 
                           quantity: int = 1) -> bool:
        """
        Select tickets for purchase
        
        Args:
            page: Browser page
            tickets: List of available tickets
            quantity: Number of tickets to select
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def complete_purchase(self, page: Any, payment_info: Dict[str, Any]) -> bool:
        """
        Complete the ticket purchase
        
        Args:
            page: Browser page
            payment_info: Payment details
            
        Returns:
            Success status
        """
        pass
    
    async def login(self, page: Any, credentials: Dict[str, str]) -> bool:
        """
        Login to the platform
        
        Args:
            page: Browser page
            credentials: Login credentials
            
        Returns:
            Success status
        """
        logger.info(f"Logging into {self.name}")
        # Default implementation - override in subclasses
        return True
    
    async def ensure_logged_in(self, page: Any) -> bool:
        """
        Ensure user is logged in, login if necessary
        
        Args:
            page: Browser page
            
        Returns:
            Success status
        """
        # Check if already logged in (platform-specific)
        if await self.is_logged_in(page):
            return True
        
        # Get credentials from config
        credentials = self.config.get("credentials", {})
        if not credentials:
            logger.warning(f"No credentials configured for {self.name}")
            return False
        
        return await self.login(page, credentials)
    
    @abstractmethod
    async def is_logged_in(self, page: Any) -> bool:
        """Check if currently logged in"""
        pass
    
    async def execute_workflow(self, target: TargetConfig) -> Dict[str, Any]:
        """
        Execute complete ticket purchase workflow with V4 enhancements
        
        Args:
            target: Target configuration
            
        Returns:
            Workflow result with statistics
        """
        start_time = time.time()
        result = {
            "success": False,
            "tickets_found": 0,
            "tickets_reserved": 0,
            "error": None,
            "duration_ms": 0
        }
        
        try:
            # Acquire browser from V4 pool
            async with v4_pool.acquire(platform=self.name) as context:
                page = context.page
                
                # Navigate to platform
                await self.navigate_to_platform(page)
                
                # Ensure logged in
                if not await self.ensure_logged_in(page):
                    raise Exception("Login failed")
                
                # Search for tickets
                search_start = time.time()
                tickets = await self.search_tickets(page, target.event_name)
                search_time = (time.time() - search_start) * 1000
                
                if tickets:
                    result["tickets_found"] = len(tickets)
                    
                    # Record tickets found
                    stats_manager.record_ticket_found(
                        self.name,
                        target.event_name,
                        target.ticket_type,
                        search_time
                    )
                    
                    # Select tickets
                    if await self.select_tickets(page, tickets, target.quantity):
                        
                        # Complete purchase (if not dry run)
                        if not self.config.get("dry_run", False):
                            purchase_start = time.time()
                            
                            if await self.complete_purchase(page, {}):
                                purchase_time = (time.time() - purchase_start) * 1000
                                
                                result["success"] = True
                                result["tickets_reserved"] = target.quantity
                                self._success_count += 1
                                
                                # Record reservation
                                stats_manager.record_ticket_reserved(
                                    self.name,
                                    target.event_name,
                                    target.ticket_type,
                                    purchase_time
                                )
                            else:
                                raise Exception("Purchase failed")
                        else:
                            # Dry run success
                            result["success"] = True
                            result["tickets_reserved"] = target.quantity
                            logger.info("Dry run - skipping actual purchase")
                else:
                    logger.info(f"No tickets found for {target.event_name}")
                
        except Exception as e:
            result["error"] = str(e)
            self._failure_count += 1
            
            # Record failure
            stats_manager.record_ticket_failed(
                self.name,
                target.event_name,
                target.ticket_type,
                str(e)
            )
            
            # Try recovery
            if 'page' in locals():
                recovered = await recovery_engine.auto_recover(page, e, self)
                if recovered:
                    logger.info("Successfully recovered from error")
                    # Could retry the workflow here
            
            logger.error(f"Workflow error: {e}")
        
        # Calculate duration
        result["duration_ms"] = (time.time() - start_time) * 1000
        self._operation_times.append(result["duration_ms"])
        
        # Log performance metric
        stats_manager.record_performance_metric(
            self._session_id,
            "workflow_execution",
            result["duration_ms"],
            success=result["success"],
            platform=self.name
        )
        
        return result
    
    async def navigate_to_platform(self, page: Any) -> None:
        """Navigate to platform homepage"""
        url = self.config.get("base_url", f"https://www.{self.name}.com")
        
        if hasattr(page, "goto"):
            # Playwright
            await page.goto(url, wait_until="domcontentloaded")
        else:
            # Selenium
            page.get(url)
            await asyncio.sleep(2)
    
    async def wait_for_element(self, page: Any, selector: str, timeout: int = 10) -> Any:
        """
        Wait for element to appear
        
        Args:
            page: Browser page
            selector: CSS selector
            timeout: Wait timeout in seconds
            
        Returns:
            Element if found, None otherwise
        """
        try:
            if hasattr(page, "wait_for_selector"):
                # Playwright
                return await page.wait_for_selector(selector, timeout=timeout * 1000)
            else:
                # Selenium
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                wait = WebDriverWait(page, timeout)
                return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
        except Exception as e:
            logger.debug(f"Element not found: {selector}")
            return None
    
    async def click_element(self, page: Any, selector: str) -> bool:
        """
        Click an element
        
        Args:
            page: Browser page
            selector: CSS selector
            
        Returns:
            Success status
        """
        try:
            element = await self.wait_for_element(page, selector)
            if element:
                if hasattr(element, "click"):
                    await element.click()
                else:
                    element.click()
                return True
            return False
        except Exception as e:
            logger.error(f"Click failed for {selector}: {e}")
            return False
    
    async def fill_input(self, page: Any, selector: str, value: str) -> bool:
        """
        Fill an input field
        
        Args:
            page: Browser page
            selector: CSS selector
            value: Value to fill
            
        Returns:
            Success status
        """
        try:
            element = await self.wait_for_element(page, selector)
            if element:
                if hasattr(element, "fill"):
                    await element.fill(value)
                else:
                    element.clear()
                    element.send_keys(value)
                return True
            return False
        except Exception as e:
            logger.error(f"Fill failed for {selector}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get handler statistics"""
        avg_time = sum(self._operation_times) / len(self._operation_times) if self._operation_times else 0
        
        return {
            "platform": self.name,
            "total_operations": len(self._operation_times),
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": (self._success_count / (self._success_count + self._failure_count) * 100) 
                          if (self._success_count + self._failure_count) > 0 else 0,
            "avg_operation_ms": avg_time
        }
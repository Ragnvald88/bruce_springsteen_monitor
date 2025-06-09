# stealthmaster/browser/context.py
"""Browser context management with stealth enhancements."""

import logging
from typing import Optional, Dict, Any

from playwright.async_api import BrowserContext, Page

from stealth.core import StealthCore

logger = logging.getLogger(__name__)


class StealthContext:
    """Manages browser contexts with stealth protection."""
    
    def __init__(self, context: BrowserContext, fingerprint: Dict[str, Any]):
        """
        Initialize stealth context wrapper.
        
        Args:
            context: Playwright browser context
            fingerprint: Browser fingerprint configuration
        """
        self.context = context
        self.fingerprint = fingerprint
        self.stealth_core = StealthCore()
        self._pages: Dict[str, Page] = {}
    
    async def new_page(self, url: Optional[str] = None) -> Page:
        """
        Create a new page with full stealth protection.
        
        Args:
            url: Optional URL to navigate to
            
        Returns:
            Protected page instance
        """
        # Create page
        page = await self.context.new_page()
        
        # Apply page-level stealth
        await self.stealth_core.apply_page_stealth(page, self.fingerprint)
        
        # Store page reference
        page_id = str(id(page))
        self._pages[page_id] = page
        
        # Navigate if URL provided
        if url:
            await self.safe_goto(page, url)
        
        logger.debug(f"Created stealth page {page_id}")
        
        return page
    
    async def safe_goto(
        self,
        page: Page,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: int = 30000,
    ) -> bool:
        """
        Safely navigate to URL with error handling.
        
        Args:
            page: Page instance
            url: Target URL
            wait_until: Wait condition
            timeout: Navigation timeout
            
        Returns:
            Success status
        """
        try:
            response = await page.goto(
                url,
                wait_until=wait_until,
                timeout=timeout,
            )
            
            if response and response.status >= 400:
                logger.warning(f"Navigation returned status {response.status} for {url}")
                return False
            
            # Check for detection
            if await self._check_detection(page):
                logger.warning(f"Detection encountered on {url}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False
    
    async def _check_detection(self, page: Page) -> bool:
        """Check if page shows signs of bot detection."""
        try:
            content = await page.content()
            detection_keywords = [
                "captcha",
                "challenge",
                "verify you are human",
                "access denied",
                "suspicious activity",
            ]
            
            content_lower = content.lower()
            return any(keyword in content_lower for keyword in detection_keywords)
            
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close all pages and context."""
        # Close all pages
        for page in self._pages.values():
            try:
                await page.close()
            except Exception:
                pass
        
        # Close context
        try:
            await self.context.close()
        except Exception:
            pass
        
        logger.debug("Closed stealth context")
    
    @property
    def storage_state(self) -> Dict[str, Any]:
        """Get current storage state (cookies, localStorage)."""
        return self.context.storage_state()
    
    async def apply_storage_state(self, state: Dict[str, Any]) -> None:
        """Apply storage state to context."""
        # This would need to be done at context creation time
        # Keeping for API completeness
        logger.warning("Storage state should be applied at context creation")
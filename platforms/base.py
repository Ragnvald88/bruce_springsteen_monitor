# stealthmaster/platforms/base.py
"""Base platform handler with common functionality."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from playwright.async_api import Page

from stealthmaster.config import TargetEvent, UserProfile
from stealthmaster.constants import PurchaseStatus, COMMON_SELECTORS
from stealthmaster.stealth.behaviors import HumanBehavior

logger = logging.getLogger(__name__)


class BasePlatformHandler(ABC):
    """Abstract base class for platform-specific handlers."""
    
    def __init__(self):
        """Initialize base handler."""
        self.name = self.__class__.__name__.replace("Handler", "")
        self.human_behavior = HumanBehavior()
        self._initialized = False
    
    @abstractmethod
    async def initialize(self, page: Page) -> bool:
        """
        Initialize platform-specific setup.
        
        Args:
            page: Page instance
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def login(self, page: Page, profile: UserProfile) -> bool:
        """
        Perform platform-specific login.
        
        Args:
            page: Page instance
            profile: User profile with credentials
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def search_tickets(
        self,
        page: Page,
        event: TargetEvent
    ) -> List[Dict[str, Any]]:
        """
        Search for available tickets.
        
        Args:
            page: Page instance
            event: Target event configuration
            
        Returns:
            List of available tickets
        """
        pass
    
    @abstractmethod
    async def select_tickets(
        self,
        page: Page,
        tickets: List[Dict[str, Any]],
        quantity: int
    ) -> bool:
        """
        Select specific tickets.
        
        Args:
            page: Page instance
            tickets: Available tickets
            quantity: Number to select
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def complete_purchase(
        self,
        page: Page,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """
        Complete ticket purchase.
        
        Args:
            page: Page instance
            profile: User profile with payment info
            
        Returns:
            Purchase confirmation details
        """
        pass
    
    async def handle_cookies(self, page: Page) -> bool:
        """
        Handle cookie consent banners.
        
        Args:
            page: Page instance
            
        Returns:
            Success status
        """
        try:
            # Try common cookie selectors
            for selector in COMMON_SELECTORS["accept_cookies"]:
                try:
                    element = await page.wait_for_selector(
                        selector,
                        timeout=3000,
                        state="visible"
                    )
                    if element:
                        await self.human_behavior.click_with_behavior(page, selector)
                        logger.debug(f"Accepted cookies on {self.name}")
                        return True
                except Exception:
                    continue
            
            return True  # No cookie banner found
            
        except Exception as e:
            logger.error(f"Cookie handling error on {self.name}: {e}")
            return False
    
    async def wait_for_element(
        self,
        page: Page,
        selector: str,
        timeout: int = 30000,
        state: str = "visible"
    ) -> Optional[Any]:
        """
        Wait for element with error handling.
        
        Args:
            page: Page instance
            selector: Element selector
            timeout: Wait timeout
            state: Expected state
            
        Returns:
            Element or None
        """
        try:
            element = await page.wait_for_selector(
                selector,
                timeout=timeout,
                state=state
            )
            return element
        except Exception as e:
            logger.debug(f"Element not found: {selector} - {e}")
            return None
    
    async def safe_click(
        self,
        page: Page,
        selector: str,
        timeout: int = 5000
    ) -> bool:
        """
        Safely click an element.
        
        Args:
            page: Page instance
            selector: Element selector
            timeout: Wait timeout
            
        Returns:
            Success status
        """
        try:
            element = await self.wait_for_element(page, selector, timeout)
            if element:
                return await self.human_behavior.click_with_behavior(page, selector)
            return False
        except Exception as e:
            logger.error(f"Safe click error: {e}")
            return False
    
    async def safe_type(
        self,
        page: Page,
        selector: str,
        text: str,
        clear_first: bool = True
    ) -> bool:
        """
        Safely type text into element.
        
        Args:
            page: Page instance
            selector: Element selector
            text: Text to type
            clear_first: Whether to clear first
            
        Returns:
            Success status
        """
        try:
            element = await self.wait_for_element(page, selector)
            if element:
                await self.human_behavior.type_like_human(
                    page,
                    selector,
                    text,
                    clear_first
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Safe type error: {e}")
            return False
    
    async def extract_ticket_info(
        self,
        page: Page,
        ticket_selector: str
    ) -> List[Dict[str, Any]]:
        """
        Extract ticket information from page.
        
        Args:
            page: Page instance
            ticket_selector: Selector for ticket elements
            
        Returns:
            List of ticket information
        """
        try:
            tickets = await page.query_selector_all(ticket_selector)
            ticket_info = []
            
            for ticket in tickets:
                try:
                    info = await ticket.evaluate("""
                        (element) => {
                            const getText = (selector) => {
                                const el = element.querySelector(selector);
                                return el ? el.textContent.trim() : '';
                            };
                            
                            return {
                                section: getText('.section, [class*="section"]'),
                                row: getText('.row, [class*="row"]'),
                                seat: getText('.seat, [class*="seat"]'),
                                price: getText('.price, [class*="price"]'),
                                available: !element.classList.contains('unavailable') &&
                                          !element.classList.contains('sold')
                            };
                        }
                    """)
                    
                    if info["available"]:
                        # Parse price
                        price_text = info["price"]
                        price = self._parse_price(price_text)
                        
                        ticket_info.append({
                            "section": info["section"],
                            "row": info["row"],
                            "seat": info["seat"],
                            "price": price,
                            "price_text": price_text,
                            "element": ticket,
                        })
                        
                except Exception as e:
                    logger.debug(f"Error extracting ticket info: {e}")
            
            return ticket_info
            
        except Exception as e:
            logger.error(f"Ticket extraction error: {e}")
            return []
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text."""
        try:
            # Remove currency symbols and spaces
            price_clean = price_text.replace("€", "").replace("$", "")
            price_clean = price_clean.replace(",", "").strip()
            
            # Extract numeric value
            import re
            match = re.search(r"[\d.]+", price_clean)
            if match:
                return float(match.group())
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def filter_tickets_by_preferences(
        self,
        tickets: List[Dict[str, Any]],
        event: TargetEvent
    ) -> List[Dict[str, Any]]:
        """
        Filter tickets based on user preferences.
        
        Args:
            tickets: Available tickets
            event: Event configuration with preferences
            
        Returns:
            Filtered tickets
        """
        filtered = tickets
        
        # Filter by max price
        if event.max_price:
            filtered = [
                t for t in filtered
                if t["price"] <= event.max_price
            ]
        
        # Filter by seat preferences
        if event.seat_preferences:
            preferred = []
            for ticket in filtered:
                for pref in event.seat_preferences:
                    if (pref.lower() in ticket["section"].lower() or
                        pref.lower() in ticket["row"].lower()):
                        preferred.append(ticket)
                        break
            
            if preferred:
                filtered = preferred
        
        # Sort by price (lowest first)
        filtered.sort(key=lambda x: x["price"])
        
        return filtered
    
    def get_status_message(self, status: PurchaseStatus) -> str:
        """Get user-friendly status message."""
        messages = {
            PurchaseStatus.PENDING: "Waiting to start...",
            PurchaseStatus.SEARCHING: "Searching for tickets...",
            PurchaseStatus.FOUND: "Tickets found!",
            PurchaseStatus.RESERVED: "Tickets reserved",
            PurchaseStatus.PURCHASING: "Completing purchase...",
            PurchaseStatus.COMPLETED: "Purchase completed!",
            PurchaseStatus.FAILED: "Purchase failed",
            PurchaseStatus.TIMEOUT: "Operation timed out",
        }
        return messages.get(status, "Unknown status")

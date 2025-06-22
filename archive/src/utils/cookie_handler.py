"""
Universal Cookie Consent Handler
Handles cookie popups across all platforms intelligently
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


class UniversalCookieHandler:
    """Handle cookie popups across all platforms"""
    
    # Comprehensive list of cookie consent selectors
    COOKIE_SELECTORS = [
        # English variants
        'button:has-text("Accept all")',
        'button:has-text("Accept All")',
        'button:has-text("Accept cookies")',
        'button:has-text("Accept Cookies")',
        'button:has-text("I agree")',
        'button:has-text("I Agree")',
        'button:has-text("Agree")',
        'button:has-text("Allow all")',
        'button:has-text("Allow All")',
        
        # Italian variants (for Italian ticket sites)
        'button:has-text("Accetta tutti")',
        'button:has-text("Accetta Tutti")',
        'button:has-text("Accetta")',
        'button:has-text("Consenti tutti")',
        'button:has-text("Consenti Tutti")',
        'button:has-text("Accetto")',
        'button:has-text("Accetta tutto")',
        'button:has-text("Accetta i cookie")',
        
        # ID/Class based selectors
        'button[id*="accept"][id*="cookie"]',
        'button[class*="accept"][class*="cookie"]',
        'button[id*="accept-all"]',
        'button[class*="accept-all"]',
        'button[id*="consent"]',
        'button[class*="consent"]',
        
        # Common cookie consent frameworks
        '#onetrust-accept-btn-handler',
        '#accept-recommended-btn-handler',
        '.onetrust-accept-btn-handler',
        '[data-testid="cookie-accept"]',
        '[data-testid="accept-cookies"]',
        '.cookie-consent-accept',
        '.cookie-accept-button',
        '.accept-cookies-button',
        '#cookie-accept',
        '#cookies-accept',
        
        # More specific selectors
        'button[aria-label*="Accept"]',
        'button[aria-label*="accept"]',
        'button[title*="Accept"]',
        'button[title*="accept"]',
        
        # Generic but common patterns
        '.btn-accept-cookies',
        '.btn-accept-all',
        '.accept-btn',
        '.acceptAll',
        '#acceptAll',
        
        # Platform specific (Fansale, Ticketmaster, etc)
        '.cookie-banner__button--accept',
        '.js-cookie-accept',
        '[data-cookie-accept]',
        '[data-qa="accept-cookies"]'
    ]
    
    # Selectors to check if cookie banner is present
    COOKIE_BANNER_SELECTORS = [
        '[class*="cookie-banner"]',
        '[class*="cookie-popup"]',
        '[class*="cookie-consent"]',
        '[class*="cookie-notice"]',
        '[class*="cookie-modal"]',
        '[id*="cookie-banner"]',
        '[id*="cookie-popup"]',
        '[id*="cookie-consent"]',
        '#onetrust-banner-sdk',
        '.onetrust-pc-dark-filter',
        '[data-testid="cookie-banner"]',
        '.cookie-disclaimer',
        '.privacy-banner'
    ]
    
    def __init__(self):
        self.handled_domains = set()
        self.selector_success_rate = {}
        
    async def check_for_cookie_banner(self, page) -> bool:
        """
        Check if a cookie banner is present on the page
        
        Args:
            page: Browser page object
            
        Returns:
            True if cookie banner detected
        """
        for selector in self.COOKIE_BANNER_SELECTORS:
            try:
                if hasattr(page, 'query_selector'):
                    # Playwright
                    element = await page.query_selector(selector)
                else:
                    # Selenium
                    elements = page.find_elements_by_css_selector(selector)
                    element = elements[0] if elements else None
                
                if element:
                    logger.debug(f"Cookie banner detected with selector: {selector}")
                    return True
            except:
                continue
        
        return False
    
    async def dismiss_cookie_banner(self, page, platform: str = None) -> bool:
        """
        Intelligently dismiss cookie banners
        
        Args:
            page: Browser page object
            platform: Optional platform name for specific handling
            
        Returns:
            True if successfully dismissed
        """
        try:
            # Get current domain
            current_url = page.url if hasattr(page, 'url') else page.current_url
            domain = self._extract_domain(current_url)
            
            # Skip if already handled for this domain
            if domain in self.handled_domains:
                logger.debug(f"Cookie already handled for domain: {domain}")
                return True
            
            # Check if banner exists first
            if not await self.check_for_cookie_banner(page):
                logger.debug("No cookie banner detected")
                return True
            
            logger.info(f"Cookie banner detected on {domain}, attempting to dismiss...")
            
            # Try selectors in order of success rate
            sorted_selectors = self._get_sorted_selectors()
            
            for selector in sorted_selectors:
                try:
                    success = await self._try_selector(page, selector)
                    if success:
                        logger.info(f"Successfully dismissed cookie banner with: {selector[:50]}...")
                        self.handled_domains.add(domain)
                        self._update_selector_stats(selector, True)
                        return True
                    else:
                        self._update_selector_stats(selector, False)
                except Exception as e:
                    logger.debug(f"Selector failed: {selector[:30]}... - {str(e)}")
                    continue
            
            # Fallback: Try to find any button with accept-like text
            if await self._try_fuzzy_accept(page):
                self.handled_domains.add(domain)
                return True
            
            logger.warning(f"Could not dismiss cookie banner on {domain}")
            return False
            
        except Exception as e:
            logger.error(f"Error in cookie handler: {e}")
            return False
    
    async def _try_selector(self, page, selector: str) -> bool:
        """Try a specific selector to dismiss cookies"""
        try:
            if hasattr(page, 'wait_for_selector'):
                # Playwright
                element = await page.wait_for_selector(selector, timeout=3000)
                if element and await element.is_visible():
                    await element.click()
                    await page.wait_for_timeout(1000)
                    return True
            else:
                # Selenium
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                # Convert Playwright selector to Selenium
                selenium_selector = self._convert_selector(selector)
                
                element = WebDriverWait(page, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selenium_selector))
                )
                element.click()
                await asyncio.sleep(1)
                return True
                
        except:
            return False
    
    async def _try_fuzzy_accept(self, page) -> bool:
        """Fallback: Find any button that looks like an accept button"""
        try:
            if hasattr(page, 'evaluate'):
                # Playwright
                result = await page.evaluate("""
                    () => {
                        const buttons = document.querySelectorAll('button, a[role="button"], input[type="button"], input[type="submit"]');
                        const acceptPatterns = /accept|agree|consent|allow|accetta|consenti|ok|continue/i;
                        
                        for (const button of buttons) {
                            const text = button.textContent || button.value || '';
                            if (acceptPatterns.test(text) && button.offsetParent !== null) {
                                button.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                return result
            else:
                # Selenium
                buttons = page.find_elements_by_css_selector('button, a[role="button"], input[type="button"], input[type="submit"]')
                accept_patterns = re.compile(r'accept|agree|consent|allow|accetta|consenti|ok|continue', re.I)
                
                for button in buttons:
                    try:
                        text = button.text or button.get_attribute('value') or ''
                        if accept_patterns.search(text) and button.is_displayed():
                            button.click()
                            return True
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Fuzzy accept failed: {e}")
            
        return False
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url
    
    def _convert_selector(self, selector: str) -> str:
        """Convert Playwright selector to Selenium compatible"""
        # Remove :has-text() pseudo-selector
        if ':has-text(' in selector:
            # Extract the tag and text
            match = re.match(r'(\w+):has-text\("([^"]+)"\)', selector)
            if match:
                tag, text = match.groups()
                # Return XPath equivalent
                return f"//{tag}[contains(text(), '{text}')]"
        
        return selector
    
    def _get_sorted_selectors(self) -> List[str]:
        """Get selectors sorted by success rate"""
        # Sort by success rate, with untracked selectors at the end
        return sorted(
            self.COOKIE_SELECTORS,
            key=lambda s: self.selector_success_rate.get(s, {}).get('rate', 0),
            reverse=True
        )
    
    def _update_selector_stats(self, selector: str, success: bool):
        """Update selector success statistics"""
        if selector not in self.selector_success_rate:
            self.selector_success_rate[selector] = {'success': 0, 'total': 0, 'rate': 0}
        
        stats = self.selector_success_rate[selector]
        stats['total'] += 1
        if success:
            stats['success'] += 1
        stats['rate'] = stats['success'] / stats['total']
    
    async def ensure_cookies_handled(self, page, max_attempts: int = 3) -> bool:
        """
        Ensure cookies are handled with retries
        
        Args:
            page: Browser page object
            max_attempts: Maximum attempts to handle cookies
            
        Returns:
            True if handled or no banner present
        """
        for attempt in range(max_attempts):
            if not await self.check_for_cookie_banner(page):
                return True
            
            if await self.dismiss_cookie_banner(page):
                return True
            
            await asyncio.sleep(1)
        
        return False


# Global cookie handler instance
cookie_handler = UniversalCookieHandler()

"""
Intelligent Session Management with Cookie Persistence
Maintains authentication state across browser restarts
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiofiles

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PersistentSessionManager:
    """Maintain sessions across browser restarts with cookie storage"""
    
    def __init__(self):
        self.cookie_storage = Path("data/cookies")
        self.cookie_storage.mkdir(parents=True, exist_ok=True)
        self.session_states = {}
        self.login_handlers = {
            'fansale': self._login_fansale,
            'ticketmaster': self._login_ticketmaster,
            'vivaticket': self._login_vivaticket
        }
        
    async def initialize_session(self, page, platform: str, credentials: Dict[str, str]) -> bool:
        """Load saved cookies and verify session"""
        cookie_file = self.cookie_storage / f"{platform}_cookies.json"
        
        # Load existing cookies
        if cookie_file.exists():
            try:
                async with aiofiles.open(cookie_file, 'r') as f:
                    cookies_data = await f.read()
                    cookies = json.loads(cookies_data)
                    
                if hasattr(page, 'context'):
                    await page.context.add_cookies(cookies)
                else:
                    # For Selenium, add cookies one by one
                    for cookie in cookies:
                        page.add_cookie(cookie)
                        
                logger.info(f"Loaded {len(cookies)} cookies for {platform}")
            except Exception as e:
                logger.error(f"Failed to load cookies for {platform}: {e}")
        
        # Verify if we're logged in
        is_authenticated = await self._verify_authentication(page, platform)
        
        if not is_authenticated:
            logger.info(f"Session expired for {platform}, re-authenticating...")
            success = await self._perform_login(page, platform, credentials)
            if success:
                # Save new cookies
                await self._save_cookies(page, platform)
            return success
        
        return True
    
    async def _verify_authentication(self, page, platform: str) -> bool:
        """Platform-specific authentication check"""
        auth_indicators = {
            'fansale': {
                'logged_in': ['user-menu', 'logout-button', 'mio-account', 'esci'],
                'logged_out': ['accedi', 'registrati', 'login']
            },
            'ticketmaster': {
                'logged_in': ['my-account', 'sign-out', 'user-profile'],
                'logged_out': ['sign-in', 'create-account', 'login']
            },
            'vivaticket': {
                'logged_in': ['area-personale', 'esci', 'il-mio-account'],
                'logged_out': ['accedi', 'registrati', 'login']
            }
        }
        
        indicators = auth_indicators.get(platform, {})
        
        # Quick check without loading full page
        for selector in indicators.get('logged_in', []):
            try:
                if hasattr(page, 'wait_for_selector'):
                    element = await page.wait_for_selector(
                        f'[class*="{selector}"], [id*="{selector}"], a[href*="{selector}"]',
                        timeout=3000
                    )
                else:
                    # Selenium
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    element = WebDriverWait(page, 3).until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR,
                            f'[class*="{selector}"], [id*="{selector}"], a[href*="{selector}"]'
                        ))
                    )
                
                if element:
                    logger.info(f"Authentication verified for {platform}")
                    return True
            except:
                continue
        
        # Check for logged out indicators
        for selector in indicators.get('logged_out', []):
            try:
                if hasattr(page, 'query_selector'):
                    element = await page.query_selector(f'[class*="{selector}"]')
                else:
                    elements = page.find_elements_by_css_selector(f'[class*="{selector}"]')
                    element = elements[0] if elements else None
                
                if element:
                    logger.info(f"Not authenticated on {platform}")
                    return False
            except:
                continue
        
        # Default to not authenticated if uncertain
        return False
    
    async def _perform_login(self, page, platform: str, credentials: Dict[str, str]) -> bool:
        """Automated login with platform-specific flows"""
        login_func = self.login_handlers.get(platform)
        if login_func:
            return await login_func(page, credentials)
        
        logger.error(f"No login handler for platform: {platform}")
        return False
    
    async def _save_cookies(self, page, platform: str):
        """Save cookies to persistent storage"""
        try:
            cookie_file = self.cookie_storage / f"{platform}_cookies.json"
            
            if hasattr(page, 'context'):
                cookies = await page.context.cookies()
            else:
                # Selenium
                cookies = page.get_cookies()
            
            async with aiofiles.open(cookie_file, 'w') as f:
                await f.write(json.dumps(cookies, indent=2))
            
            logger.info(f"Saved {len(cookies)} cookies for {platform}")
            
        except Exception as e:
            logger.error(f"Failed to save cookies for {platform}: {e}")
    
    # Platform-specific login implementations
    async def _login_fansale(self, page, credentials: Dict[str, str]) -> bool:
        """Fansale login flow"""
        try:
            # Navigate to login page
            login_url = "https://www.fansale.it/fansale/login"
            if hasattr(page, 'goto'):
                await page.goto(login_url, wait_until='networkidle')
            else:
                page.get(login_url)
                await asyncio.sleep(3)
            
            # Fill login form
            if hasattr(page, 'fill'):
                # Playwright
                await page.fill('input[name="email"], input[type="email"]', credentials['username'])
                await page.fill('input[name="password"], input[type="password"]', credentials['password'])
                
                # Click login button
                await page.click('button[type="submit"], input[type="submit"]')
            else:
                # Selenium
                email_input = page.find_element_by_css_selector('input[name="email"], input[type="email"]')
                email_input.send_keys(credentials['username'])
                
                password_input = page.find_element_by_css_selector('input[name="password"], input[type="password"]')
                password_input.send_keys(credentials['password'])
                
                login_button = page.find_element_by_css_selector('button[type="submit"], input[type="submit"]')
                login_button.click()
            
            # Wait for login to complete
            await asyncio.sleep(5)
            
            # Verify login success
            return await self._verify_authentication(page, 'fansale')
            
        except Exception as e:
            logger.error(f"Fansale login failed: {e}")
            return False
    
    async def _login_ticketmaster(self, page, credentials: Dict[str, str]) -> bool:
        """Ticketmaster login flow"""
        try:
            # Navigate to login page
            login_url = "https://www.ticketmaster.it/member/login"
            if hasattr(page, 'goto'):
                await page.goto(login_url, wait_until='networkidle')
            else:
                page.get(login_url)
                await asyncio.sleep(3)
            
            # Fill login form
            if hasattr(page, 'fill'):
                await page.fill('#email, input[name="email"]', credentials['username'])
                await page.fill('#password, input[name="password"]', credentials['password'])
                
                # Click login button
                await page.click('#sign-in-button, button[type="submit"]')
            else:
                # Selenium implementation
                email_input = page.find_element_by_id('email')
                email_input.send_keys(credentials['username'])
                
                password_input = page.find_element_by_id('password')
                password_input.send_keys(credentials['password'])
                
                login_button = page.find_element_by_id('sign-in-button')
                login_button.click()
            
            # Wait for login
            await asyncio.sleep(5)
            
            return await self._verify_authentication(page, 'ticketmaster')
            
        except Exception as e:
            logger.error(f"Ticketmaster login failed: {e}")
            return False
    
    async def _login_vivaticket(self, page, credentials: Dict[str, str]) -> bool:
        """Vivaticket login flow"""
        try:
            # Navigate to login page
            login_url = "https://www.vivaticket.com/it/login"
            if hasattr(page, 'goto'):
                await page.goto(login_url, wait_until='networkidle')
            else:
                page.get(login_url)
                await asyncio.sleep(3)
            
            # Fill login form
            if hasattr(page, 'fill'):
                await page.fill('input[name="username"], #username', credentials['username'])
                await page.fill('input[name="password"], #password', credentials['password'])
                
                # Click login button
                await page.click('button[type="submit"]')
            else:
                # Selenium
                username_input = page.find_element_by_name('username')
                username_input.send_keys(credentials['username'])
                
                password_input = page.find_element_by_name('password')
                password_input.send_keys(credentials['password'])
                
                login_button = page.find_element_by_css_selector('button[type="submit"]')
                login_button.click()
            
            # Wait for login
            await asyncio.sleep(5)
            
            return await self._verify_authentication(page, 'vivaticket')
            
        except Exception as e:
            logger.error(f"Vivaticket login failed: {e}")
            return False


# Global instance
session_manager = PersistentSessionManager()

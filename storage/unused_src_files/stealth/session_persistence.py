"""
Session Persistence for Ticketing Platforms
Saves and reuses authenticated sessions to bypass repeated captchas
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class SessionPersistence:
    """Manages session persistence for ticketing platforms"""
    
    def __init__(self, session_dir: str = "storage/sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Session persistence initialized at {self.session_dir}")
        
    def get_session_path(self, platform: str, profile_id: str) -> Path:
        """Get session file path for platform and profile"""
        return self.session_dir / f"{platform}_{profile_id}_session.json"
        
    async def save_session(self, context: BrowserContext, platform: str, profile_id: str) -> bool:
        """Save browser session state"""
        try:
            session_path = self.get_session_path(platform, profile_id)
            
            # Save storage state (cookies, localStorage, etc.)
            await context.storage_state(path=str(session_path))
            
            # Save metadata
            metadata_path = session_path.with_suffix('.meta.json')
            metadata = {
                'platform': platform,
                'profile_id': profile_id,
                'saved_at': str(Path.ctime(session_path)),
                'success': True
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"✅ Session saved for {platform} ({profile_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
            
    async def load_session(
        self, 
        browser: Browser, 
        platform: str, 
        profile_id: str,
        context_options: Optional[Dict[str, Any]] = None
    ) -> Optional[BrowserContext]:
        """Load saved session if available"""
        try:
            session_path = self.get_session_path(platform, profile_id)
            
            if not session_path.exists():
                logger.info(f"No saved session for {platform} ({profile_id})")
                return None
                
            # Check session age
            age_hours = (Path.ctime(Path.cwd()) - Path.ctime(session_path)) / 3600
            if age_hours > 24:
                logger.warning(f"Session older than 24 hours, may be expired")
                
            # Create context with saved state
            options = context_options or {}
            options['storage_state'] = str(session_path)
            
            context = await browser.new_context(**options)
            
            logger.info(f"✅ Session loaded for {platform} ({profile_id})")
            return context
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
            
    def clear_session(self, platform: str, profile_id: str) -> bool:
        """Clear saved session"""
        try:
            session_path = self.get_session_path(platform, profile_id)
            metadata_path = session_path.with_suffix('.meta.json')
            
            if session_path.exists():
                session_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
                
            logger.info(f"Cleared session for {platform} ({profile_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False
            
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """List all saved sessions"""
        sessions = {}
        
        for meta_file in self.session_dir.glob("*.meta.json"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                    
                session_file = meta_file.with_suffix('').with_suffix('.json')
                if session_file.exists():
                    metadata['file_size'] = session_file.stat().st_size
                    metadata['exists'] = True
                else:
                    metadata['exists'] = False
                    
                key = f"{metadata['platform']}_{metadata['profile_id']}"
                sessions[key] = metadata
                
            except Exception as e:
                logger.debug(f"Error reading {meta_file}: {e}")
                
        return sessions


async def perform_authenticated_login(
    page: Page, 
    platform: str,
    credentials: Dict[str, str],
    session_manager: SessionPersistence,
    profile_id: str
) -> bool:
    """Perform login and save session"""
    
    login_configs = {
        'ticketmaster': {
            'url': 'https://www.ticketmaster.it/member/sign-in',
            'username_selector': 'input[name="email"], input[type="email"]',
            'password_selector': 'input[name="password"], input[type="password"]',
            'submit_selector': 'button[type="submit"]',
            'success_indicator': 'a[href*="logout"], button[aria-label*="account"]'
        },
        'fansale': {
            'url': 'https://www.fansale.it/fansale/login',
            'username_selector': 'input[name="email"]',
            'password_selector': 'input[name="password"]',
            'submit_selector': 'button[type="submit"]',
            'success_indicator': 'a[href*="logout"], .user-menu'
        }
    }
    
    config = login_configs.get(platform)
    if not config:
        logger.error(f"No login config for {platform}")
        return False
        
    try:
        # Navigate to login page
        logger.info(f"Navigating to {platform} login page...")
        await page.goto(config['url'], wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        
        # Check if already logged in
        if await page.query_selector(config['success_indicator']):
            logger.info(f"Already logged in to {platform}")
            await session_manager.save_session(page.context, platform, profile_id)
            return True
            
        # Fill login form
        logger.info("Filling login form...")
        
        # Username
        await page.fill(config['username_selector'], credentials['username'])
        await page.wait_for_timeout(1000)
        
        # Password
        await page.fill(config['password_selector'], credentials['password'])
        await page.wait_for_timeout(1000)
        
        # Check for captcha
        if await page.query_selector('iframe[src*="recaptcha"], div[class*="captcha"]'):
            logger.warning("⚠️ CAPTCHA detected - manual intervention required!")
            logger.info("Please solve the captcha in the browser window...")
            
            # Wait for manual solving (timeout after 5 minutes)
            try:
                await page.wait_for_selector(
                    config['success_indicator'],
                    timeout=300000  # 5 minutes
                )
            except:
                logger.error("Login timeout - captcha not solved")
                return False
        else:
            # Submit form
            await page.click(config['submit_selector'])
            
        # Wait for login to complete
        try:
            await page.wait_for_selector(
                config['success_indicator'],
                timeout=30000
            )
            
            logger.info(f"✅ Successfully logged in to {platform}")
            
            # Save session
            await session_manager.save_session(page.context, platform, profile_id)
            
            return True
            
        except:
            logger.error(f"Login failed for {platform}")
            return False
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return False
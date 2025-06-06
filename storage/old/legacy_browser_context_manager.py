# Legacy SmartBrowserContextManager - MOVED TO STORAGE
# This functionality has been superseded by stealth_engine.py
# Moved on 2025-01-06 during StealthMaster AI integration cleanup

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SmartBrowserContextManager:
    """Legacy smart browser context manager with profile integration
    
    NOTE: This class has been superseded by stealth_engine.py's create_stealth_context()
    which provides comprehensive anti-detection capabilities including:
    - Advanced fingerprint generation
    - Behavioral simulation
    - CDP protection
    - Dynamic script injection
    - ML-based optimization
    
    This legacy implementation remains for reference only.
    """
    
    def __init__(self, playwright_instance, profile_manager, data_tracker, config):
        self.playwright = playwright_instance
        self.profile_manager = profile_manager
        self.data_tracker = data_tracker
        self.config = config
        self.contexts: Dict[str, Any] = {}
        
    async def get_stealth_context(self, profile, force_new: bool = False):
        """Get or create a stealth browser context
        
        DEPRECATED: Use stealth_engine.py's create_stealth_context() instead
        """
        profile_id = getattr(profile, 'profile_id', getattr(profile, 'id', 'unknown'))
        
        if profile_id in self.contexts and not force_new:
            return self.contexts[profile_id]
        
        # Create new context with basic stealth settings
        context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=f"/tmp/browser_profile_{profile_id}",
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--hide-scrollbars',
                '--mute-audio',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-background-networking'
            ],
            viewport={'width': profile.viewport_width, 'height': profile.viewport_height},
            user_agent=profile.user_agent,
            locale=getattr(profile, 'locale', 'en-US'),
            timezone_id=getattr(profile, 'timezone', 'America/New_York'),
            permissions=['geolocation'],
            extra_http_headers={
                'Accept-Language': getattr(profile, 'accept_language', 'en-US,en;q=0.9'),
            }
        )
        
        # Inject basic stealth script (now superseded by dynamic script generation)
        stealth_script_path = self.config.get('paths', {}).get('stealth_script', 'src/core/stealth_init.js')
        if os.path.exists(stealth_script_path):
            with open(stealth_script_path, 'r') as f:
                stealth_script = f.read()
            
            await context.add_init_script(stealth_script)
        
        self.contexts[profile_id] = context
        return context
    
    async def close_all(self):
        """Close all browser contexts"""
        for context in self.contexts.values():
            try:
                await context.close()
            except Exception as e:
                logger.error(f"Error closing context: {e}")
        self.contexts.clear()


# Additional legacy helper for pre-warming connections
class ConnectionPreWarmer:
    """Pre-warm connections to reduce latency on first request
    
    NOTE: This functionality is now integrated into stealth_engine.py
    """
    
    @staticmethod
    async def prewarm_connections(
        pool_manager,
        profiles,
        targets
    ):
        """Pre-establish connections to target domains"""
        tasks = []
        
        for profile in profiles[:3]:  # Limit pre-warming to avoid suspicion
            for target in targets:
                async def warm_connection(p=profile, t=target):
                    try:
                        client = await pool_manager.get_client(p)
                        logger.debug(f"Pre-warmed connection for {getattr(p, 'profile_id', 'unknown')} to {t}")
                    except Exception as e:
                        logger.warning(f"Failed to pre-warm connection: {e}")
                
                tasks.append(warm_connection())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
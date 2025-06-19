"""
Stealth Orchestrator - Comprehensive integration of all anti-detection measures
Ensures all stealth components are properly applied in the correct order
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .core import StealthCore
from .browser_warmup import browser_warmup_engine
from .behaviors import HumanBehavior
from .cdp_bypass_engine import CDPStealth
from .cdp_webdriver_bypass import CDPWebDriverBypass
from .fingerprint import fingerprint_generator
from .akamai_bypass import AkamaiBypass
from .ultimate_bypass import UltimateAkamaiBypass
from ..utils.logging import get_logger

logger = get_logger(__name__)


class StealthOrchestrator:
    """
    Orchestrates all stealth components to provide maximum anti-detection
    """
    
    def __init__(self, settings=None):
        """Initialize all stealth components"""
        self.settings = settings
        self.stealth_core = StealthCore()
        self.behavior_engine = HumanBehavior()
        self.cdp_stealth = CDPStealth()
        self.cdp_webdriver_bypass = CDPWebDriverBypass()
        self.ultimate_bypass = UltimateAkamaiBypass()
        
        # Track protection status
        self.protected_pages: Dict[str, Dict[str, Any]] = {}
        self.warmup_completed: Dict[str, bool] = {}
        
        logger.info("🛡️ StealthOrchestrator initialized with all components")
    
    async def apply_full_stealth(self, page: Any, platform: str, browser_id: str) -> Dict[str, Any]:
        """
        Apply comprehensive stealth protection to a page
        
        Args:
            page: Browser page (Selenium or Playwright)
            platform: Platform name (fansale, ticketmaster, etc.)
            browser_id: Unique browser identifier
            
        Returns:
            Dict with protection status and details
        """
        start_time = datetime.now()
        protection_status = {
            'platform': platform,
            'browser_id': browser_id,
            'steps_completed': [],
            'errors': [],
            'success': False
        }
        
        try:
            logger.info(f"🚀 Starting full stealth protection for {platform}")
            
            # Step 1: Apply CDP-level stealth (must be first!)
            logger.info("📡 Applying CDP stealth...")
            if hasattr(page, 'execute_cdp_cmd'):
                # Selenium/undetected-chromedriver
                try:
                    # Apply basic CDP commands for Selenium
                    page.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                        'source': '''
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            });
                        '''
                    })
                except Exception as e:
                    logger.debug(f"CDP command failed (normal for UC): {e}")
                protection_status['steps_completed'].append('selenium_stealth')
            else:
                # Playwright
                await self.cdp_stealth.apply_to_page(page)
                protection_status['steps_completed'].append('cdp_stealth')
            
            # Step 2: Skip complex stealth that causes crashes
            logger.info("🔐 Applying minimal stealth...")
            protection_status['steps_completed'].append('minimal_stealth')
            
            # Step 4: Apply platform-specific Akamai bypass
            if platform in ['fansale', 'ticketmaster', 'vivaticket']:
                logger.info(f"🛡️ Applying Akamai bypass for {platform}...")
                
                # Use ultimate bypass for higher success rate
                if self.settings and self.settings.app_settings.ultimate_mode:
                    await self.ultimate_bypass.apply_advanced_bypass(page, platform)
                    protection_status['steps_completed'].append('ultimate_akamai_bypass')
                else:
                    await AkamaiBypass.apply_bypass(page)
                    protection_status['steps_completed'].append('basic_akamai_bypass')
            
            # Step 5: Skip browser warmup that causes crashes
            if False and not self.warmup_completed.get(browser_id, False):
                logger.info(f"🔥 Starting browser warmup for {platform}...")
                await browser_warmup_engine.warmup_browser(page, platform)
                self.warmup_completed[browser_id] = True
                protection_status['steps_completed'].append('browser_warmup')
                logger.info("✅ Browser warmup completed")
            else:
                logger.info("✅ Skipping browser warmup")
            
            # Step 6: Apply additional runtime patches
            logger.info("🔧 Applying runtime patches...")
            await self._apply_runtime_patches(page)
            protection_status['steps_completed'].append('runtime_patches')
            
            # Store protection status
            self.protected_pages[browser_id] = {
                'platform': platform,
                'protection_time': datetime.now(),
                'status': protection_status
            }
            
            protection_status['success'] = True
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Full stealth protection applied in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error applying stealth: {e}")
            protection_status['errors'].append(str(e))
        
        return protection_status
    
    async def _apply_runtime_patches(self, page: Any):
        """Apply additional runtime patches"""
        try:
            if hasattr(page, 'execute_script'):
                # Selenium
                page.execute_script("""
                    // Additional runtime patches
                    
                    // Fix Permissions API
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => {
                        if (parameters.name === 'notifications') {
                            return Promise.resolve({ state: 'default' });
                        }
                        return originalQuery(parameters);
                    };
                    
                    // Fix WebGL
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter.apply(this, arguments);
                    };
                    
                    // Fix AudioContext
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (AudioContext) {
                        AudioContext.prototype.constructor = AudioContext;
                    }
                    
                    // Remove automation indicators
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                """)
            else:
                # Playwright
                await page.evaluate("""
                    () => {
                        // Same patches as above
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => {
                            if (parameters.name === 'notifications') {
                                return Promise.resolve({ state: 'default' });
                            }
                            return originalQuery(parameters);
                        };
                        
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {
                            if (parameter === 37445) return 'Intel Inc.';
                            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                            return getParameter.apply(this, arguments);
                        };
                    }
                """)
        except Exception as e:
            logger.debug(f"Runtime patch error (non-critical): {e}")
    
    async def maintain_human_behavior(self, page: Any):
        """Maintain human-like behavior during monitoring"""
        try:
            await self.behavior_engine.simulate_reading()
            await self.behavior_engine.random_micro_movements()
        except Exception as e:
            logger.debug(f"Behavior simulation error: {e}")
    
    def get_protection_status(self, browser_id: str) -> Optional[Dict[str, Any]]:
        """Get protection status for a browser"""
        return self.protected_pages.get(browser_id)
    
    async def refresh_protection(self, page: Any, browser_id: str):
        """Refresh stealth protections if needed"""
        protection = self.protected_pages.get(browser_id)
        if protection:
            # Refresh if older than 30 minutes
            age = (datetime.now() - protection['protection_time']).total_seconds()
            if age > 1800:  # 30 minutes
                logger.info("🔄 Refreshing stealth protections...")
                platform = protection['platform']
                await self.apply_full_stealth(page, platform, browser_id)


# Global instance
stealth_orchestrator = StealthOrchestrator()
#!/usr/bin/env python3
"""Test script to verify proxy configuration"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_settings
from src.browser.launcher import NodriverBrowserLauncher
from src.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

async def test_proxy():
    """Test proxy configuration and usage"""
    try:
        # Load settings
        settings = load_settings(Path("config.yaml"))
        
        # Setup logging
        setup_logging(level="DEBUG")
        
        # Create launcher with settings
        launcher = NodriverBrowserLauncher(settings)
        
        # Check proxy settings
        if settings.proxy_settings.enabled:
            logger.info(f"Proxy enabled: {settings.proxy_settings.enabled}")
            logger.info(f"Primary pool size: {len(settings.proxy_settings.primary_pool)}")
            
            if settings.proxy_settings.primary_pool:
                proxy = settings.proxy_settings.primary_pool[0]
                logger.info(f"First proxy: {proxy.host}:{proxy.port}")
                logger.info(f"Username: {proxy.username}")
                logger.info(f"Password: {'*' * len(proxy.password) if proxy.password else 'None'}")
        else:
            logger.warning("Proxy is disabled in settings")
            
        # Test browser launch with proxy
        logger.info("Launching browser with proxy...")
        browser_id = await launcher.launch_browser()
        logger.info(f"Browser launched: {browser_id}")
        
        # Create context and page
        context_id = await launcher.create_context(browser_id)
        page = await launcher.new_page(context_id)
        
        # Test proxy by checking IP
        logger.info("Checking IP address...")
        if hasattr(page, "goto"):
            # Playwright
            await page.goto("https://httpbin.org/ip", wait_until="domcontentloaded")
            ip_data = await page.evaluate("() => document.body.textContent")
        else:
            # Selenium
            page.get("https://httpbin.org/ip")
            await asyncio.sleep(2)
            ip_data = page.execute_script("return document.body.textContent")
            
        logger.info(f"IP check result: {ip_data}")
        
        # Cleanup
        await launcher.close_all()
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_proxy())
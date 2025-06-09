#!/usr/bin/env python3
"""
Test proxy and stealth setup
"""

import asyncio
import os
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_stealth():
    """Test basic connectivity with stealth"""
    
    logger.info("Testing basic stealth setup...")
    
    async with async_playwright() as p:
        # Browser args for stealth
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
        ]
        
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,  # Show browser for debugging
            args=browser_args,
            channel='chrome'
        )
        
        # Create context with proxy
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        # Add proxy if configured
        if os.getenv('IPROYAL_HOSTNAME'):
            context_options['proxy'] = {
                'server': f"http://{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT', 12321)}",
                'username': os.getenv('IPROYAL_USERNAME'),
                'password': os.getenv('IPROYAL_PASSWORD')
            }
            logger.info("Using proxy")
        
        context = await browser.new_context(**context_options)
        page = await context.new_page()
        
        # Apply basic stealth
        await page.add_init_script("""
        // Basic stealth
        delete Object.getPrototypeOf(navigator).webdriver;
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """)
        
        try:
            # Test 1: Check IP and location
            logger.info("\nTest 1: Checking IP location...")
            response = await page.goto('https://httpbin.org/ip', timeout=30000)
            ip_data = await page.content()
            logger.info(f"IP Check Response: {response.status}")
            logger.info(f"Content preview: {ip_data[:200]}")
            
            # Test 2: Check headers
            logger.info("\nTest 2: Checking headers...")
            await page.goto('https://httpbin.org/headers', timeout=30000)
            headers_data = await page.content()
            logger.info(f"Headers preview: {headers_data[:300]}")
            
            # Test 3: Try Fansale homepage (not event page)
            logger.info("\nTest 3: Testing Fansale homepage...")
            response = await page.goto('https://www.fansale.it', timeout=30000)
            logger.info(f"Fansale Response: {response.status}")
            
            if response.status == 403:
                logger.error("Still blocked on Fansale homepage")
                content = await page.content()
                logger.info(f"Page content preview: {content[:500]}")
            else:
                logger.info("Successfully accessed Fansale!")
                
            # Keep browser open for inspection
            logger.info("\nBrowser will stay open for 30 seconds for inspection...")
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error during test: {e}")
            
        finally:
            await browser.close()


async def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    await test_basic_stealth()


if __name__ == "__main__":
    asyncio.run(main())
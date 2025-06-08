#!/usr/bin/env python3
"""
Test Ultra Stealth Implementation
Verifies that our enhanced stealth measures work
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from playwright.async_api import async_playwright
from stealth.ultra_stealth import UltraStealthEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('UltraStealthTest')


async def test_stealth_detection():
    """Test if we can pass bot detection"""
    logger.info("🛡️ TESTING ULTRA STEALTH MODE...")
    
    async with async_playwright() as p:
        # Launch with stealth args
        browser = await p.chromium.launch(
            headless=False,  # Use headful for better results
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-http2',
                '--force-http1',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--disable-features=ImprovedCookieControls',
                '--aggressive-cache-discard',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--password-store=basic',
                '--use-mock-keychain',
                '--force-color-profile=srgb',
                '--disable-features=UserAgentClientHint',
                '--disable-features=CalculateNativeWinOcclusion',
            ]
        )
        
        # Create stealth context
        proxy_config = None
        if os.getenv('IPROYAL_USERNAME'):
            proxy_config = {
                'server': f"http://{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}@{os.getenv('IPROYAL_HOSTNAME', 'geo.iproyal.com')}:{os.getenv('IPROYAL_PORT', '12321')}"
            }
            
        context = await UltraStealthEngine.create_stealth_context(browser, proxy_config)
        page = await context.new_page()
        
        # Apply ultra stealth
        await UltraStealthEngine.apply_ultra_stealth(page)
        
        # Test 1: Bot detection site
        logger.info("\n📍 Testing on bot.sannysoft.com...")
        try:
            await page.goto('https://bot.sannysoft.com/', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Check results
            results = await page.evaluate("""
                () => {
                    const tests = {};
                    const rows = document.querySelectorAll('table tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            const testName = cells[0]?.textContent?.trim();
                            const result = cells[1]?.textContent?.trim();
                            if (testName) {
                                tests[testName] = !result.includes('failed') && !result.includes('missing');
                            }
                        }
                    });
                    return tests;
                }
            """)
            
            # Log results
            failed = [name for name, passed in results.items() if not passed]
            if failed:
                logger.warning(f"❌ Failed tests: {', '.join(failed)}")
            else:
                logger.info("✅ ALL DETECTION TESTS PASSED!")
                
            # Take screenshot
            await page.screenshot(path='ultra_stealth_test.png')
            logger.info("📸 Screenshot saved: ultra_stealth_test.png")
            
        except Exception as e:
            logger.error(f"Bot detection test error: {e}")
            
        # Test 2: Platform access
        logger.info("\n📍 Testing platform access...")
        
        platforms = [
            ('Fansale', 'https://www.fansale.it'),
            ('Ticketmaster', 'https://www.ticketmaster.it'),
            ('Vivaticket', 'https://www.vivaticket.com/it')
        ]
        
        for name, url in platforms:
            logger.info(f"\nTesting {name}...")
            try:
                # Apply human behavior before navigation
                await UltraStealthEngine.simulate_human_behavior(page)
                
                response = await page.goto(url, timeout=45000, wait_until='domcontentloaded')
                status = response.status if response else 0
                title = await page.title()
                
                # Check for blocks
                content = await page.content()
                blocked = any(word in content.lower() for word in ['blocked', 'forbidden', 'captcha', 'challenge'])
                
                if not blocked and status == 200:
                    logger.info(f"✅ {name}: ACCESSIBLE (Status: {status}, Title: {title[:50]}...)")
                else:
                    logger.warning(f"❌ {name}: BLOCKED (Status: {status})")
                    
                # Wait a bit between requests
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ {name}: ERROR - {str(e)[:100]}")
                
        await browser.close()
        
        
async def test_login_capabilities():
    """Test if we can access login pages"""
    logger.info("\n🔐 TESTING LOGIN PAGE ACCESS...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-http2',
                '--no-sandbox',
            ]
        )
        
        proxy_config = None
        if os.getenv('IPROYAL_USERNAME'):
            proxy_config = {
                'server': f"http://{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}@{os.getenv('IPROYAL_HOSTNAME', 'geo.iproyal.com')}:{os.getenv('IPROYAL_PORT', '12321')}"
            }
            
        context = await UltraStealthEngine.create_stealth_context(browser, proxy_config)
        page = await context.new_page()
        await UltraStealthEngine.apply_ultra_stealth(page)
        
        # Test login pages
        login_pages = [
            ('Fansale', 'https://www.fansale.it/fansale/login'),
            ('Ticketmaster', 'https://www.ticketmaster.it/member/sign-in')
        ]
        
        for name, url in login_pages:
            logger.info(f"\nTesting {name} login page...")
            try:
                await page.goto(url, timeout=45000)
                await page.wait_for_timeout(2000)
                
                # Check if login form is present
                has_email = await page.query_selector('input[type="email"], input[name*="email"], input[name*="user"]') is not None
                has_password = await page.query_selector('input[type="password"]') is not None
                
                if has_email and has_password:
                    logger.info(f"✅ {name}: Login form accessible!")
                else:
                    logger.warning(f"⚠️ {name}: Login form not found")
                    
                # Take screenshot
                await page.screenshot(path=f'{name.lower()}_login_test.png')
                
            except Exception as e:
                logger.error(f"❌ {name} login test error: {e}")
                
        await browser.close()


async def main():
    """Run all ultra stealth tests"""
    logger.info("="*80)
    logger.info("🛡️ ULTRA STEALTH TEST SUITE")
    logger.info("="*80)
    
    # Test stealth detection
    await test_stealth_detection()
    
    # Test login capabilities
    await test_login_capabilities()
    
    logger.info("\n" + "="*80)
    logger.info("✅ ULTRA STEALTH TESTS COMPLETE")
    logger.info("="*80)
    
    
if __name__ == "__main__":
    asyncio.run(main())
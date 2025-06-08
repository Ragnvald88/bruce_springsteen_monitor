#!/usr/bin/env python3
"""
Test CDP Stealth Implementation
Tests if we can finally bypass WebDriver detection
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from playwright.async_api import async_playwright
from stealth.cdp_stealth import CDPStealthEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('CDPStealthTest')


async def test_webdriver_detection():
    """Test if we can pass WebDriver detection"""
    logger.info("🛡️ TESTING CDP STEALTH MODE...")
    
    async with async_playwright() as p:
        # Create undetectable browser
        browser = await CDPStealthEngine.create_undetectable_browser(p)
        
        # Setup proxy if available
        proxy_config = None
        if os.getenv('IPROYAL_USERNAME'):
            proxy_config = {
                'server': f"http://{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}@{os.getenv('IPROYAL_HOSTNAME', 'geo.iproyal.com')}:{os.getenv('IPROYAL_PORT', '12321')}"
            }
            
        # Create stealth context
        context = await CDPStealthEngine.create_stealth_context(browser, proxy_config)
        page = await context.new_page()
        
        # Apply CDP stealth
        await CDPStealthEngine.apply_page_stealth(page)
        
        # Test WebDriver detection
        logger.info("\n📍 Testing WebDriver detection...")
        
        # First, let's check navigator.webdriver directly
        is_webdriver = await page.evaluate("() => navigator.webdriver")
        logger.info(f"navigator.webdriver = {is_webdriver}")
        
        # Test on bot.sannysoft.com
        logger.info("\n📍 Testing on bot.sannysoft.com...")
        try:
            await page.goto('https://bot.sannysoft.com/', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Get all test results
            results = await page.evaluate("""
                () => {
                    const results = {};
                    const rows = document.querySelectorAll('table tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            const testName = cells[0]?.textContent?.trim();
                            const testResult = cells[1]?.textContent?.trim();
                            if (testName && testName !== 'Test Name') {
                                results[testName] = testResult;
                            }
                        }
                    });
                    return results;
                }
            """)
            
            logger.info("\nDetection Test Results:")
            for test, result in results.items():
                if 'failed' in result.lower() or 'missing' in result.lower():
                    logger.error(f"  ❌ {test}: {result}")
                else:
                    logger.info(f"  ✅ {test}: {result}")
                    
            # Take screenshot
            await page.screenshot(path='cdp_stealth_test.png')
            logger.info("\n📸 Screenshot saved: cdp_stealth_test.png")
            
            # Specific WebDriver test
            webdriver_test = results.get('WebDriver (New)', 'Not found')
            if 'passed' in webdriver_test.lower() or 'present' not in webdriver_test.lower():
                logger.info("\n🎉 WEBDRIVER DETECTION BYPASSED!")
            else:
                logger.warning(f"\n⚠️ WebDriver still detected: {webdriver_test}")
                
        except Exception as e:
            logger.error(f"Bot detection test error: {e}")
            
        await browser.close()


async def test_platform_access_with_cdp():
    """Test platform access with CDP stealth"""
    logger.info("\n🌐 TESTING PLATFORM ACCESS WITH CDP STEALTH...")
    
    async with async_playwright() as p:
        browser = await CDPStealthEngine.create_undetectable_browser(p)
        
        proxy_config = None
        if os.getenv('IPROYAL_USERNAME'):
            proxy_config = {
                'server': f"http://{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}@{os.getenv('IPROYAL_HOSTNAME', 'geo.iproyal.com')}:{os.getenv('IPROYAL_PORT', '12321')}"
            }
            
        context = await CDPStealthEngine.create_stealth_context(browser, proxy_config)
        
        platforms = [
            ('Fansale', 'https://www.fansale.it'),
            ('Ticketmaster', 'https://www.ticketmaster.it'),
            ('Vivaticket', 'https://www.vivaticket.com/it')
        ]
        
        for name, url in platforms:
            logger.info(f"\nTesting {name}...")
            
            page = await context.new_page()
            await CDPStealthEngine.apply_page_stealth(page)
            
            try:
                # Simulate human behavior before navigation
                await CDPStealthEngine.simulate_human_mouse(page)
                
                response = await page.goto(url, timeout=45000, wait_until='domcontentloaded')
                status = response.status if response else 0
                
                # Wait a bit for JavaScript to load
                await page.wait_for_timeout(3000)
                
                # Check page content
                title = await page.title()
                content = await page.content()
                
                # Detection checks
                has_captcha = 'captcha' in content.lower() or 'challenge' in content.lower()
                has_block = 'blocked' in content.lower() or 'forbidden' in content.lower()
                has_cloudflare = 'cloudflare' in content.lower()
                
                if status == 200 and not has_captcha and not has_block:
                    logger.info(f"✅ {name}: ACCESSIBLE (Title: {title[:50]}...)")
                else:
                    issues = []
                    if status != 200:
                        issues.append(f"Status {status}")
                    if has_captcha:
                        issues.append("Captcha")
                    if has_block:
                        issues.append("Blocked")
                    if has_cloudflare:
                        issues.append("Cloudflare")
                    logger.warning(f"❌ {name}: ISSUES - {', '.join(issues)}")
                    
                # Take screenshot
                await page.screenshot(path=f'cdp_{name.lower()}_test.png')
                
                await page.close()
                
                # Wait between sites
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ {name}: ERROR - {str(e)[:100]}")
                await page.close()
                
        await browser.close()


async def test_login_pages_with_cdp():
    """Test login page access with CDP stealth"""
    logger.info("\n🔐 TESTING LOGIN PAGES WITH CDP STEALTH...")
    
    async with async_playwright() as p:
        browser = await CDPStealthEngine.create_undetectable_browser(p)
        
        proxy_config = None
        if os.getenv('IPROYAL_USERNAME'):
            proxy_config = {
                'server': f"http://{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}@{os.getenv('IPROYAL_HOSTNAME', 'geo.iproyal.com')}:{os.getenv('IPROYAL_PORT', '12321')}"
            }
            
        context = await CDPStealthEngine.create_stealth_context(browser, proxy_config)
        
        login_tests = [
            {
                'name': 'Fansale',
                'url': 'https://www.fansale.it/fansale/login',
                'email_selector': 'input[name="email"], input[type="email"]',
                'password_selector': 'input[name="password"], input[type="password"]'
            }
        ]
        
        for test in login_tests:
            logger.info(f"\nTesting {test['name']} login page...")
            
            page = await context.new_page()
            await CDPStealthEngine.apply_page_stealth(page)
            
            try:
                # Navigate to login page
                await page.goto(test['url'], timeout=45000)
                await page.wait_for_timeout(3000)
                
                # Check for login form elements
                has_email = await page.query_selector(test['email_selector']) is not None
                has_password = await page.query_selector(test['password_selector']) is not None
                
                if has_email and has_password:
                    logger.info(f"✅ {test['name']}: Login form accessible!")
                    
                    # Test typing if we have credentials
                    username = os.getenv(f"{test['name'].upper()}_EMAIL") or os.getenv("FANSALE_EMAIL")
                    if username:
                        logger.info(f"   Testing human-like typing...")
                        await CDPStealthEngine.type_like_human(page, test['email_selector'], username)
                        logger.info(f"   ✅ Successfully typed username")
                else:
                    logger.warning(f"⚠️ {test['name']}: Login form not found")
                    
                # Take screenshot
                await page.screenshot(path=f'cdp_{test["name"].lower()}_login.png')
                
                await page.close()
                
            except Exception as e:
                logger.error(f"❌ {test['name']} login test error: {e}")
                await page.close()
                
        await browser.close()


async def main():
    """Run all CDP stealth tests"""
    logger.info("="*80)
    logger.info("🛡️ CDP STEALTH TEST SUITE")
    logger.info("="*80)
    
    # Test WebDriver detection
    await test_webdriver_detection()
    
    # Test platform access
    await test_platform_access_with_cdp()
    
    # Test login pages
    await test_login_pages_with_cdp()
    
    logger.info("\n" + "="*80)
    logger.info("✅ CDP STEALTH TESTS COMPLETE")
    logger.info("="*80)
    
    # Summary
    logger.info("\n📊 SUMMARY:")
    logger.info("- Check cdp_stealth_test.png for WebDriver detection results")
    logger.info("- Check cdp_*_test.png for platform access results")
    logger.info("- If WebDriver is still detected, we may need to use undetected-chromedriver")
    
    
if __name__ == "__main__":
    asyncio.run(main())
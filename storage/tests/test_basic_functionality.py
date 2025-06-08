#!/usr/bin/env python3
"""Test basic functionality without requiring proxy credentials"""

import sys
import asyncio
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.stealth.stealth_engine import StealthMasterEngine
from src.profiles.manager import ProfileManagerV2
from playwright.async_api import async_playwright
import logging
from colorama import init, Fore, Style

init(autoreset=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """Test basic system functionality"""
    
    logger.info("🔬 Running Basic Functionality Tests")
    logger.info("=" * 60)
    
    results = {
        "imports": False,
        "stealth_engine": False,
        "profile_manager": False,
        "browser_launch": False,
        "cdp_stealth": False
    }
    
    # Test 1: Core imports
    logger.info("\n✅ Test 1: Core imports successful")
    results["imports"] = True
    
    # Test 2: Stealth engine initialization
    logger.info("\n🛡️ Test 2: Stealth Engine Initialization")
    try:
        stealth_engine = StealthMasterEngine()
        logger.info("✅ StealthMasterEngine initialized")
        results["stealth_engine"] = True
    except Exception as e:
        logger.error(f"❌ StealthMasterEngine failed: {e}")
    
    # Test 3: Profile manager initialization
    logger.info("\n👤 Test 3: Profile Manager Initialization")
    try:
        profile_manager = ProfileManagerV2()
        profiles = profile_manager.get_all_profiles()
        logger.info(f"✅ ProfileManager initialized with {len(profiles)} profiles")
        results["profile_manager"] = True
        
        # Show profile distribution
        tier_counts = {}
        for profile in profiles:
            tier = profile.quality_tier
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        logger.info("Profile distribution by tier:")
        for tier, count in sorted(tier_counts.items(), reverse=True):
            logger.info(f"  Tier {tier}: {count} profiles")
            
    except Exception as e:
        logger.error(f"❌ ProfileManager failed: {e}")
    
    # Test 4: Browser launch with CDP
    logger.info("\n🌐 Test 4: Browser Launch with CDP Stealth")
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=False,
                channel="chrome",
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            logger.info("✅ Browser launched successfully")
            
            # Create context with CDP
            context = await browser.new_context()
            
            # Get CDP session
            page = await context.new_page()
            client = await context.new_cdp_session(page)
            
            # Apply basic CDP stealth
            await client.send('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
            
            logger.info("✅ CDP session created and stealth applied")
            results["browser_launch"] = True
            results["cdp_stealth"] = True
            
            # Test navigation
            await page.goto("https://httpbin.org/headers")
            await page.wait_for_timeout(2000)
            
            # Check if we're detected
            content = await page.content()
            if "webdriver" not in content.lower():
                logger.info("✅ WebDriver not detected in headers")
            else:
                logger.warning("⚠️  WebDriver may be detected")
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Browser launch failed: {e}")
    
    # Test 5: Memory and performance check
    logger.info("\n⚡ Test 5: Quick Performance Check")
    
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    logger.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB")
    logger.info(f"CPU percent: {process.cpu_percent(interval=1):.1f}%")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Results Summary:")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed < total:
        logger.warning("\n⚠️  Some tests failed. Check the logs above for details.")
    else:
        logger.info("\n🎉 All basic functionality tests passed!")
    
    return passed == total


async def main():
    """Main test runner"""
    try:
        success = await test_basic_functionality()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n👋 Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
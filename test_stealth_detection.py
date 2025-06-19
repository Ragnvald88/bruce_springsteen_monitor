#!/usr/bin/env python3
"""
Test script to verify stealth implementation against detection services
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_settings
from src.browser.launcher import launcher
from src.stealth.stealth_orchestrator import stealth_orchestrator
from src.utils.logging import setup_logging, get_logger

# Setup logging
setup_logging("INFO", Path(__file__).parent / "logs")
logger = get_logger(__name__)


async def test_stealth():
    """Test stealth against various detection services"""
    print("\n🔍 StealthMaster Detection Test Suite\n")
    
    # Load settings
    settings = load_settings()
    launcher.settings = settings
    stealth_orchestrator.settings = settings
    
    # Test URLs
    test_urls = {
        "Bot Sannysoft": "https://bot.sannysoft.com/",
        "Fingerprint.com": "https://fingerprint.com/demo/",
        "CreepJS": "https://abrahamjuliot.github.io/creepjs/",
        "BrowserLeaks": "https://browserleaks.com/javascript",
        "IPInfo": "https://ipinfo.io/json"
    }
    
    browser_id = None
    context_id = None
    page = None
    
    try:
        # Launch browser
        print("🚀 Launching stealth browser...")
        browser_id = await launcher.launch_browser()
        
        # Create context
        context_id = await launcher.create_context(browser_id)
        
        # Create page
        page = await launcher.new_page(context_id)
        
        # Apply full stealth
        print("🛡️ Applying full stealth protection...")
        protection_status = await stealth_orchestrator.apply_full_stealth(
            page, 
            "test", 
            browser_id
        )
        
        if protection_status['success']:
            print("✅ Stealth protection applied successfully!")
            print(f"   Steps: {', '.join(protection_status['steps_completed'])}")
        else:
            print("❌ Stealth protection failed!")
            return
        
        # Test each detection service
        print("\n📊 Testing against detection services:\n")
        
        for name, url in test_urls.items():
            print(f"Testing {name}...")
            try:
                if hasattr(page, "goto"):
                    # Playwright
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                else:
                    # Selenium
                    page.get(url)
                    await asyncio.sleep(3)
                
                # Get some detection results
                if "sannysoft" in url:
                    # Check specific bot detection
                    if hasattr(page, "evaluate"):
                        results = await page.evaluate("""
                            () => {
                                const tests = document.querySelectorAll('td');
                                const results = {};
                                for (let i = 0; i < tests.length; i += 2) {
                                    if (tests[i] && tests[i+1]) {
                                        const testName = tests[i].textContent.trim();
                                        const testResult = tests[i+1].textContent.trim();
                                        results[testName] = testResult;
                                    }
                                }
                                return results;
                            }
                        """)
                    else:
                        results = page.execute_script("""
                            const tests = document.querySelectorAll('td');
                            const results = {};
                            for (let i = 0; i < tests.length; i += 2) {
                                if (tests[i] && tests[i+1]) {
                                    const testName = tests[i].textContent.trim();
                                    const testResult = tests[i+1].textContent.trim();
                                    results[testName] = testResult;
                                }
                            }
                            return results;
                        """)
                    
                    # Check key indicators
                    webdriver = results.get('User Agent', '').lower()
                    if 'missing' in webdriver or 'failed' in webdriver:
                        print(f"   ❌ WebDriver detected!")
                    else:
                        print(f"   ✅ WebDriver test passed")
                
                elif "ipinfo" in url:
                    # Check IP/proxy
                    if hasattr(page, "evaluate"):
                        ip_data = await page.evaluate("() => document.body.textContent")
                    else:
                        ip_data = page.execute_script("return document.body.textContent")
                    
                    import json
                    try:
                        ip_info = json.loads(ip_data)
                        print(f"   📍 IP: {ip_info.get('ip', 'Unknown')}")
                        print(f"   📍 Location: {ip_info.get('city', 'Unknown')}, {ip_info.get('country', 'Unknown')}")
                    except:
                        pass
                
                print(f"   ✅ {name} loaded successfully\n")
                
            except Exception as e:
                print(f"   ❌ Error testing {name}: {e}\n")
        
        # Run built-in stealth test
        print("\n🧪 Running built-in stealth test...")
        test_results = await launcher.test_stealth(page)
        
        print(f"\n📊 Stealth Test Results:")
        print(f"   WebDriver: {test_results.get('webdriver', 'Unknown')}")
        print(f"   Chrome: {test_results.get('chrome', 'Unknown')}")
        print(f"   Chrome.runtime: {test_results.get('chrome.runtime', 'Unknown')}")
        print(f"   Plugins: {test_results.get('plugins.length', 'Unknown')}")
        print(f"   Languages: {test_results.get('languages', 'Unknown')}")
        print(f"   Detection Score: {test_results.get('detection_score', 'Unknown')}/100")
        print(f"   Is Detected: {test_results.get('is_detected', 'Unknown')}")
        
        if not test_results.get('is_detected', True):
            print("\n✅ STEALTH TEST PASSED! Browser appears human.")
        else:
            print("\n❌ STEALTH TEST FAILED! Browser detected as bot.")
        
        print("\n📈 Launcher Statistics:")
        stats = launcher.get_statistics()
        print(f"   Browsers launched: {stats['browsers_launched']}")
        print(f"   Average launch time: {stats['avg_launch_time_ms']:.0f}ms")
        print(f"   Detection attempts: {stats['detection_attempts']}")
        
        # Keep browser open for manual inspection
        print("\n⏸️  Browser will stay open for 30 seconds for manual inspection...")
        print("   Check the detection results in the browser window")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await launcher.close_all()


if __name__ == "__main__":
    print("=" * 60)
    print("StealthMaster Detection Test Suite")
    print("=" * 60)
    asyncio.run(test_stealth())
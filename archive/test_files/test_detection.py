#!/usr/bin/env python3
"""
Detection Test Script - Verify anti-detection measures
Tests the bot against common detection methods
"""

import time
import sys
from datetime import datetime
from stealth_improvements import StealthEnhancements
import undetected_chromedriver as uc
from selenium import webdriver
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_detection_tests():
    """Run comprehensive detection tests"""
    logger.info("🔍 Starting detection tests...")
    
    stealth = StealthEnhancements()
    
    # Create driver with enhanced options
    options = uc.ChromeOptions()
    
    # Add enhanced stealth arguments
    for arg in stealth.get_enhanced_chrome_options():
        try:
            options.add_argument(arg)
        except:
            pass
    
    # Use a common user agent
    options.add_argument(f'--user-agent={stealth.get_random_user_agent()}')
    
    # Window size
    options.add_argument('--window-size=1920,1080')
    
    # Create driver
    driver = uc.Chrome(options=options)
    
    try:
        # Inject stealth JavaScript
        stealth_js = stealth.get_stealth_javascript()
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': stealth_js
        })
        
        # Test 1: Basic detection test page
        logger.info("\n📋 Test 1: Basic Detection Tests")
        driver.get("https://bot.sannysoft.com/")
        time.sleep(3)
        
        # Let user see the results
        logger.info("Check the browser window for bot detection results")
        logger.info("Green = Good, Red = Detected")
        input("Press Enter to continue to next test...")
        
        # Test 2: Fingerprinting test
        logger.info("\n📋 Test 2: Browser Fingerprinting Test")
        driver.get("https://abrahamjuliot.github.io/creepjs/")
        time.sleep(5)
        
        logger.info("Check your browser fingerprint and trust score")
        input("Press Enter to continue to next test...")
        
        # Test 3: WebGL and Canvas test
        logger.info("\n📋 Test 3: Canvas and WebGL Fingerprinting")
        driver.get("https://browserleaks.com/canvas")
        time.sleep(3)
        
        logger.info("Check if canvas fingerprint is unique")
        input("Press Enter to continue to next test...")
        
        # Test 4: Run our custom detection tests
        logger.info("\n📋 Test 4: Custom Detection Tests")
        results = stealth.test_detection(driver)
        analysis = stealth.analyze_detection_results(results)
        
        logger.info(f"\n🎯 Detection Score: {analysis['score']}/100 ({analysis['status']})")
        
        if analysis['issues']:
            logger.warning("\n⚠️ Issues found:")
            for issue in analysis['issues']:
                logger.warning(f"  {issue}")
        else:
            logger.info("\n✅ No major issues detected!")
        
        logger.info("\n📊 Detailed Results:")
        for test, result in results.items():
            status = "✅" if not (result is True and test == 'webdriver') else "❌"
            logger.info(f"  {status} {test}: {result}")
        
        # Test 5: Fansale-specific test
        logger.info("\n📋 Test 5: Fansale Detection Test")
        driver.get("https://www.fansale.it")
        time.sleep(3)
        
        # Check if we trigger any anti-bot measures
        page_source = driver.page_source.lower()
        bot_indicators = ['blocked', 'captcha', 'forbidden', 'denied', 'bot detected']
        
        detected = False
        for indicator in bot_indicators:
            if indicator in page_source:
                logger.warning(f"❌ Possible detection: '{indicator}' found in page")
                detected = True
        
        if not detected:
            logger.info("✅ No obvious bot detection on Fansale")
        
        # Performance test
        logger.info("\n📋 Test 6: Performance Metrics")
        performance = driver.execute_script("""
            const perf = performance.getEntriesByType('navigation')[0];
            return {
                loadTime: perf.loadEventEnd - perf.loadEventStart,
                domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
                totalTime: perf.loadEventEnd - perf.fetchStart
            };
        """)
        
        logger.info(f"  Page load time: {performance['loadTime']:.2f}ms")
        logger.info(f"  DOM content loaded: {performance['domContentLoaded']:.2f}ms")
        logger.info(f"  Total time: {performance['totalTime']:.2f}ms")
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("📝 DETECTION TEST SUMMARY")
        logger.info("="*50)
        
        if analysis['score'] >= 80:
            logger.info("✅ EXCELLENT: Your bot has strong anti-detection measures")
            logger.info("   You should be able to avoid most detection systems")
        elif analysis['score'] >= 60:
            logger.info("⚠️ GOOD: Your bot has decent protection but could be improved")
            logger.info("   You might occasionally trigger detection systems")
        else:
            logger.info("❌ POOR: Your bot is easily detectable")
            logger.info("   High risk of being blocked by anti-bot systems")
        
        logger.info("\n💡 Recommendations:")
        if 'webdriver' in [issue for issue in analysis['issues'] if 'webdriver' in issue]:
            logger.info("  - Update undetected-chromedriver to latest version")
        if 'Chrome object' in str(analysis['issues']):
            logger.info("  - Ensure Chrome object spoofing is working")
        if 'plugins' in str(analysis['issues']):
            logger.info("  - Plugin spoofing may need adjustment")
        
        logger.info("\n✅ Detection tests completed!")
        
    except Exception as e:
        logger.error(f"Error during tests: {e}")
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()


def quick_test():
    """Quick detection test without full browser"""
    logger.info("🚀 Running quick detection analysis...")
    
    stealth = StealthEnhancements()
    
    # Test chrome options
    options = stealth.get_enhanced_chrome_options()
    logger.info(f"\n✅ Enhanced Chrome options: {len(options)} arguments configured")
    
    # Test user agents
    for i in range(3):
        ua = stealth.get_random_user_agent()
        logger.info(f"✅ User Agent {i+1}: {ua[:50]}...")
    
    # Test timing functions
    delays = [stealth.human_like_delay() for _ in range(10)]
    avg_delay = sum(delays) / len(delays)
    logger.info(f"\n✅ Human-like delays: {avg_delay*1000:.1f}ms average")
    
    # Test mouse path generation
    path = stealth.generate_mouse_path((100, 100), (500, 500), num_points=10)
    logger.info(f"✅ Mouse path generation: {len(path)} points")
    
    logger.info("\n✅ Quick test completed!")


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        run_detection_tests()


if __name__ == "__main__":
    main()
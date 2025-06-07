#!/usr/bin/env python3
"""
Test script for Detection Monitoring System
Demonstrates comprehensive anti-detection tracking
"""

import asyncio
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.detection_monitor import get_detection_monitor, DetectionEventType
from src.utils.stealth_tester import StealthTester
from src.core.stealth.stealth_integration import init_bruce_stealth_integration
from src.utils.live_status_logger import init_live_status_logging
from src.utils.enhanced_logger import setup_enhanced_logging
from playwright.async_api import async_playwright

# Setup logging
setup_enhanced_logging(log_level="INFO")
logger = logging.getLogger(__name__)


async def test_detection_monitoring():
    """Run comprehensive detection monitoring tests"""
    logger.info("🚀 Starting Detection Monitoring Test")
    
    # Initialize components
    monitor = get_detection_monitor()
    tester = StealthTester()
    live_logger = init_live_status_logging(enable_gui=False)
    stealth_integration = init_bruce_stealth_integration(live_logger)
    
    # Clear previous metrics for clean test
    monitor.clear_metrics()
    
    async with async_playwright() as playwright:
        # Test with different browser profiles
        test_profiles = [
            {
                'id': 'test_profile_1',
                'device_type': 'desktop',
                'os': 'Windows 11',
                'browser': 'Chrome',
                'browser_version': '121.0.6167.85',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            {
                'id': 'test_profile_2',
                'device_type': 'desktop',
                'os': 'macOS',
                'browser': 'Chrome',
                'browser_version': '120.0.6099.130',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        ]
        
        # Create browser
        browser = await playwright.chromium.launch(
            headless=False,  # Set to True for headless testing
            args=['--disable-blink-features=AutomationControlled']
        )
        
        for profile in test_profiles:
            logger.info(f"\n🔍 Testing profile: {profile['id']}")
            
            try:
                # Create stealth context
                context = await stealth_integration.create_stealth_browser_context(
                    browser=browser,
                    device_profile=profile,
                    proxy_config=None
                )
                
                # Test 1: Platform access
                logger.info("📊 Testing platform access...")
                page = await context.new_page()
                
                # Test FanSale
                await test_platform_access(page, "fansale", profile['id'], monitor)
                
                # Test Ticketmaster
                await test_platform_access(page, "ticketmaster", profile['id'], monitor)
                
                # Test 2: Run comprehensive stealth tests
                logger.info("🛡️ Running comprehensive stealth tests...")
                stealth_score = await tester.run_comprehensive_test(
                    context, profile['id'], "test"
                )
                logger.info(f"Stealth Score: {stealth_score['overall_score']}/100")
                
                # Test 3: Simulate login attempts
                logger.info("🔑 Simulating login attempts...")
                await simulate_login_attempts(page, profile['id'], monitor)
                
                # Test 4: Simulate various detection scenarios
                logger.info("🚨 Simulating detection scenarios...")
                await simulate_detection_scenarios(profile['id'], monitor)
                
                await context.close()
                
            except Exception as e:
                logger.error(f"Error testing profile {profile['id']}: {e}")
                monitor.log_event(
                    event_type=DetectionEventType.ACCESS_DENIED,
                    platform="test",
                    profile_id=profile['id'],
                    success=False,
                    details={"error": str(e)}
                )
        
        await browser.close()
    
    # Display final metrics
    logger.info("\n📊 FINAL DETECTION METRICS:")
    dashboard_data = monitor.get_dashboard_data()
    
    for platform, metrics in dashboard_data['platforms'].items():
        logger.info(f"\n{platform.upper()}:")
        logger.info(f"  - Total Attempts: {metrics['total_attempts']}")
        logger.info(f"  - Success Rate: {metrics['success_rate']:.1f}%")
        logger.info(f"  - Block Rate: {metrics['block_rate']:.1f}%")
        logger.info(f"  - Health Score: {metrics['health_score']:.1f}/100")
        logger.info(f"  - Current Streak: {metrics['current_streak']}")
        logger.info(f"  - Bot Detections: {metrics['bot_detections']}")
        logger.info(f"  - Rate Limits: {metrics['rate_limits_hit']}")
    
    # Show recent blocks
    recent_blocks = dashboard_data['global_metrics']['recent_blocks']
    if recent_blocks:
        logger.warning(f"\n🚫 Recent Blocks: {len(recent_blocks)}")
        for block in recent_blocks[-5:]:
            logger.warning(f"  - {block['datetime']} | {block['platform']} | {block['event_type']}")
    
    logger.info("\n✅ Detection monitoring test completed!")


async def test_platform_access(page, platform: str, profile_id: str, monitor):
    """Test access to a specific platform"""
    urls = {
        "fansale": "https://www.fansale.it/",
        "ticketmaster": "https://www.ticketmaster.com/",
        "vivaticket": "https://www.vivaticket.com/"
    }
    
    url = urls.get(platform)
    if not url:
        return
    
    try:
        start_time = asyncio.get_event_loop().time()
        response = await page.goto(url, wait_until='networkidle', timeout=30000)
        load_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Check response
        if response and response.status == 200:
            # Check for blocking indicators
            content = await page.content()
            
            if any(word in content.lower() for word in ['captcha', 'recaptcha', 'challenge']):
                monitor.log_event(
                    event_type=DetectionEventType.CAPTCHA_TRIGGERED,
                    platform=platform,
                    profile_id=profile_id,
                    success=False,
                    details={"url": url, "load_time_ms": load_time}
                )
                logger.warning(f"  ⚠️ {platform}: CAPTCHA detected")
            elif any(word in content.lower() for word in ['blocked', 'forbidden', 'denied']):
                monitor.log_event(
                    event_type=DetectionEventType.ACCESS_DENIED,
                    platform=platform,
                    profile_id=profile_id,
                    success=False,
                    details={"url": url, "load_time_ms": load_time}
                )
                logger.error(f"  ❌ {platform}: ACCESS DENIED")
            else:
                monitor.log_event(
                    event_type=DetectionEventType.ACCESS_GRANTED,
                    platform=platform,
                    profile_id=profile_id,
                    success=True,
                    details={"url": url, "load_time_ms": load_time}
                )
                logger.info(f"  ✅ {platform}: Access granted ({load_time:.0f}ms)")
        else:
            monitor.log_event(
                event_type=DetectionEventType.ACCESS_DENIED,
                platform=platform,
                profile_id=profile_id,
                success=False,
                details={"status_code": response.status if response else None}
            )
            logger.error(f"  ❌ {platform}: HTTP {response.status if response else 'No response'}")
            
    except Exception as e:
        monitor.log_event(
            event_type=DetectionEventType.ACCESS_DENIED,
            platform=platform,
            profile_id=profile_id,
            success=False,
            details={"error": str(e)}
        )
        logger.error(f"  ❌ {platform}: Error - {str(e)}")


async def simulate_login_attempts(page, profile_id: str, monitor):
    """Simulate login attempts with various outcomes"""
    scenarios = [
        ("fansale", True, "successful login"),
        ("ticketmaster", False, "invalid credentials"),
        ("fansale", True, "successful after retry"),
        ("vivaticket", False, "captcha required")
    ]
    
    for platform, success, reason in scenarios:
        await asyncio.sleep(0.5)  # Simulate time between attempts
        
        if success:
            monitor.log_event(
                event_type=DetectionEventType.LOGIN_SUCCESS,
                platform=platform,
                profile_id=profile_id,
                success=True,
                details={"reason": reason}
            )
            logger.info(f"  ✅ {platform}: Login successful - {reason}")
        else:
            monitor.log_event(
                event_type=DetectionEventType.LOGIN_FAILED,
                platform=platform,
                profile_id=profile_id,
                success=False,
                details={"reason": reason}
            )
            logger.warning(f"  ❌ {platform}: Login failed - {reason}")


async def simulate_detection_scenarios(profile_id: str, monitor):
    """Simulate various detection scenarios"""
    # Simulate rate limiting
    monitor.log_event(
        event_type=DetectionEventType.RATE_LIMITED,
        platform="ticketmaster",
        profile_id=profile_id,
        success=False,
        details={"requests_made": 150, "limit": 100}
    )
    logger.warning("  🚦 Rate limited on Ticketmaster")
    
    # Simulate bot detection
    monitor.log_event(
        event_type=DetectionEventType.BOT_DETECTED,
        platform="vivaticket",
        profile_id=profile_id,
        success=False,
        details={"detection_method": "behavioral_analysis"}
    )
    logger.error("  🤖 Bot detected on Vivaticket")
    
    # Simulate IP block
    monitor.log_event(
        event_type=DetectionEventType.IP_BLOCKED,
        platform="ticketmaster",
        profile_id=profile_id,
        success=False,
        details={"ip": "192.168.1.100", "duration": "temporary"}
    )
    logger.error("  🚫 IP blocked on Ticketmaster")
    
    # Simulate successful stealth check
    monitor.log_event(
        event_type=DetectionEventType.STEALTH_CHECK_PASSED,
        platform="fansale",
        profile_id=profile_id,
        success=True,
        details={"check_type": "fingerprint_validation"}
    )
    logger.info("  ✅ Stealth check passed on FanSale")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🛡️  DETECTION MONITORING TEST - STEALTHMASTER AI  🛡️         ║
║                                                                  ║
║  This test will:                                                 ║
║  1. Test platform access (FanSale, Ticketmaster, Vivaticket)   ║
║  2. Run comprehensive stealth tests                             ║
║  3. Simulate login attempts and detection scenarios             ║
║  4. Display detailed metrics and health scores                  ║
║                                                                  ║
║  Press Ctrl+C to stop at any time                              ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(test_detection_monitoring())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
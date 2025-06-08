#!/usr/bin/env python3
"""
Test Main Application with CDP Stealth Integration
Verifies that the CDP stealth is properly integrated into the main app
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('CDPIntegrationTest')


async def test_single_platform():
    """Test a single platform with CDP stealth"""
    from core.orchestrator import MonitoringOrchestrator
    from core.models import Config
    
    # Create minimal config for testing
    config = Config({
        'targets': [
            {
                'name': 'Fansale Bruce Test',
                'url': 'https://www.fansale.it/tickets/hard-heavy/bruce-springsteen/1',
                'event_name': 'Bruce Springsteen',
                'priority': 'HIGH',
                'desired_sections': ['Prato', 'Tribuna'],
                'max_price_per_ticket': 500,
                'authentication': {
                    'enabled': False  # Skip auth for now
                },
                'headless': True  # Test with headless for Fansale
            }
        ],
        'monitoring': {
            'check_interval': 30,
            'randomize_interval': True,
            'max_workers': 1
        },
        'profiles': {
            'rotation_enabled': False,  # Use single profile
            'stealth_mode': 'maximum'
        },
        'proxy': {
            'enabled': True,
            'provider': 'iproyal',
            'rotation_strategy': 'sticky'
        }
    })
    
    # Initialize orchestrator
    orchestrator = MonitoringOrchestrator(config)
    
    try:
        logger.info("🚀 Starting CDP Stealth Integration Test...")
        
        # Initialize
        await orchestrator.initialize()
        
        # Run single check
        logger.info("\n📍 Running ticket check with CDP stealth...")
        
        # Get the monitor
        monitor = list(orchestrator.active_monitors.values())[0]
        
        # Check page properties
        logger.info("\n🔍 Checking stealth properties...")
        
        # Navigate to bot test page first
        await monitor.page.goto('https://bot.sannysoft.com/', timeout=30000)
        await monitor.page.wait_for_timeout(2000)
        
        # Check webdriver
        is_webdriver = await monitor.page.evaluate("() => navigator.webdriver")
        logger.info(f"navigator.webdriver = {is_webdriver}")
        
        # Take screenshot
        await monitor.page.screenshot(path='cdp_integration_test.png')
        logger.info("📸 Bot test screenshot saved")
        
        # Now navigate to Fansale
        logger.info("\n🎫 Testing Fansale access...")
        await monitor.page.goto(monitor.url, timeout=45000)
        await monitor.page.wait_for_timeout(3000)
        
        # Check for blocks
        content = await monitor.page.content()
        title = await monitor.page.title()
        
        blocked = any(word in content.lower() for word in ['blocked', 'forbidden', 'captcha'])
        
        if not blocked and monitor.page.url != 'about:blank':
            logger.info(f"✅ Fansale ACCESSIBLE! Title: {title}")
            
            # Try to check tickets
            logger.info("\n🔍 Attempting ticket detection...")
            opportunities = await monitor.check_tickets()
            
            if opportunities:
                logger.info(f"🎯 Found {len(opportunities)} ticket opportunities!")
                for opp in opportunities[:3]:
                    logger.info(f"  - {opp.section}: €{opp.price}")
            else:
                logger.info("No tickets found (this is normal if none available)")
                
        else:
            logger.error(f"❌ Fansale BLOCKED or error occurred")
            
        # Take final screenshot
        await monitor.page.screenshot(path='fansale_cdp_test.png')
        logger.info("📸 Fansale screenshot saved")
        
    except Exception as e:
        logger.error(f"Test error: {e}", exc_info=True)
        
    finally:
        # Cleanup
        await orchestrator.cleanup()
        logger.info("\n✅ Test complete")


async def test_all_platforms():
    """Test all platforms with CDP stealth"""
    from core.orchestrator import MonitoringOrchestrator
    from core.models import Config
    
    # Test configurations for each platform
    test_configs = [
        {
            'name': 'Fansale Test',
            'url': 'https://www.fansale.it/tickets/hard-heavy/bruce-springsteen/1',
            'headless': True
        },
        {
            'name': 'Ticketmaster Test', 
            'url': 'https://www.ticketmaster.it/artist/bruce-springsteen-biglietti/736',
            'headless': False  # Force headful for Ticketmaster
        },
        {
            'name': 'Vivaticket Test',
            'url': 'https://www.vivaticket.com/it/search?q=bruce%20springsteen',
            'headless': True
        }
    ]
    
    for test_config in test_configs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {test_config['name']}...")
        logger.info(f"{'='*60}")
        
        config = Config({
            'targets': [{
                **test_config,
                'event_name': 'Bruce Springsteen',
                'priority': 'HIGH',
                'authentication': {'enabled': False}
            }],
            'monitoring': {
                'check_interval': 30,
                'max_workers': 1
            },
            'proxy': {
                'enabled': True,
                'provider': 'iproyal'
            }
        })
        
        orchestrator = MonitoringOrchestrator(config)
        
        try:
            await orchestrator.initialize()
            monitor = list(orchestrator.active_monitors.values())[0]
            
            # Check access
            opportunities = await monitor.check_tickets()
            
            if monitor.scan_metrics['blocks_encountered'] == 0:
                logger.info(f"✅ {test_config['name']}: ACCESSIBLE")
            else:
                logger.warning(f"⚠️ {test_config['name']}: BLOCKED")
                
        except Exception as e:
            logger.error(f"❌ {test_config['name']}: ERROR - {str(e)[:100]}")
            
        finally:
            await orchestrator.cleanup()
            await asyncio.sleep(2)  # Cool down between tests


async def main():
    """Run all integration tests"""
    logger.info("="*80)
    logger.info("🛡️ CDP STEALTH INTEGRATION TEST")
    logger.info("="*80)
    
    # Check environment
    if not os.getenv('IPROYAL_USERNAME'):
        logger.warning("⚠️ No proxy credentials found in environment")
        logger.info("Set IPROYAL_USERNAME, IPROYAL_PASSWORD, etc.")
        
    # Test single platform first
    await test_single_platform()
    
    # Optional: Test all platforms
    # await test_all_platforms()
    
    logger.info("\n" + "="*80)
    logger.info("✅ CDP INTEGRATION TEST COMPLETE")
    logger.info("="*80)
    logger.info("\nCheck screenshots:")
    logger.info("- cdp_integration_test.png (bot detection)")
    logger.info("- fansale_cdp_test.png (platform access)")


if __name__ == "__main__":
    asyncio.run(main())
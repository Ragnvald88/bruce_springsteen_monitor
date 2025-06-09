#!/usr/bin/env python3
"""
Test script for improved StealthMaster system
Tests enhanced stealth and purchase monitoring
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.async_api import async_playwright
from src.stealth.enhanced_stealth_v4 import EnhancedStealthV4
from src.core.purchase_monitor import PurchaseTracker
from src.platforms.unified_handler_v4 import UnifiedHandlerV4
from src.core.human_behavior_engine import HumanBehaviorEngine
from src.profiles.manager import ProfileManager
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

logger = logging.getLogger(__name__)


async def test_platform(platform_config, proxy_config=None):
    """Test a single platform with enhanced stealth"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {platform_config['platform'].upper()}")
    logger.info(f"{'='*60}")
    
    async with async_playwright() as p:
        # Browser args for stealth
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu'
        ]
        
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,  # Set to True for production
            args=browser_args,
            channel='chrome'
        )
        
        # Create context with proxy if available
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': 'en-US',
            'timezone_id': 'Europe/Rome'
        }
        
        if proxy_config:
            context_options['proxy'] = {
                'server': f"http://{proxy_config['host']}:{proxy_config['port']}",
                'username': proxy_config['username'],
                'password': proxy_config['password']
            }
            logger.info("Using proxy for connection")
            
        context = await browser.new_context(**context_options)
        
        # Create page
        page = await context.new_page()
        
        # Apply enhanced stealth
        await EnhancedStealthV4.apply_ultra_stealth(page, context)
        logger.info("Applied Enhanced Stealth v4.0")
        
        # Create components
        behavior_engine = HumanBehaviorEngine()
        purchase_tracker = PurchaseTracker()
        
        # Detection callback
        async def detection_callback(event):
            logger.warning(f"DETECTION EVENT: {event['message']} ({event['severity']})")
            
        # Create handler
        handler = UnifiedHandlerV4(
            config=platform_config,
            browser=browser,
            behavior_engine=behavior_engine,
            fingerprint={},
            page=page,
            context=context,
            detection_callback=detection_callback,
            purchase_tracker=purchase_tracker
        )
        
        # Initialize handler
        await handler.initialize()
        
        # Run tests
        logger.info("Starting ticket search...")
        
        for i in range(3):  # Run 3 checks
            logger.info(f"\nCheck #{i+1}")
            
            try:
                # Check for tickets
                tickets = await handler.check_tickets()
                
                if tickets:
                    logger.info(f"✅ Found {len(tickets)} tickets!")
                    for ticket in tickets[:5]:  # Show first 5
                        logger.info(f"  - {ticket.section}: €{ticket.price} x{ticket.quantity}")
                else:
                    logger.info("❌ No tickets found")
                    
                # Show insights
                insights = purchase_tracker.get_insights()
                if insights:
                    logger.info("\nInsights:")
                    for insight in insights:
                        logger.info(f"  {insight}")
                        
            except Exception as e:
                logger.error(f"Error during check: {e}")
                
            # Wait between checks
            if i < 2:
                logger.info("Waiting 10 seconds before next check...")
                await asyncio.sleep(10)
                
        # Show final summary
        await purchase_tracker.show_dashboard()
        
        # Cleanup
        await page.close()
        await context.close()
        await browser.close()
        
        logger.info("\nTest completed!")


async def main():
    """Main test function"""
    
    logger.info("🎸 StealthMaster Enhanced Test Suite")
    logger.info("Testing improved stealth and monitoring capabilities\n")
    
    # Test configurations
    test_configs = [
        {
            'platform': 'fansale',
            'event_name': 'Bruce Springsteen Milano 2025',
            'url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388',
            'max_price_per_ticket': 800,
            'desired_sections': ['Prato', 'Tribuna', 'Primo Anello']
        },
        {
            'platform': 'ticketmaster',
            'event_name': 'Bruce Springsteen San Siro 2025',
            'url': 'https://www.ticketmaster.it/event/bruce-springsteen-milano-biglietti/31289',
            'max_price_per_ticket': 750,
            'desired_sections': ['Floor', 'Lower Bowl']
        }
    ]
    
    # Load proxy config from environment
    import os
    proxy_config = None
    if os.getenv('IPROYAL_HOSTNAME'):
        proxy_config = {
            'host': os.getenv('IPROYAL_HOSTNAME'),
            'port': int(os.getenv('IPROYAL_PORT', 12321)),
            'username': os.getenv('IPROYAL_USERNAME'),
            'password': os.getenv('IPROYAL_PASSWORD')
        }
        logger.info("Proxy configuration loaded from environment")
    else:
        logger.warning("No proxy configuration found - running without proxy")
    
    # Test each platform
    for config in test_configs:
        try:
            await test_platform(config, proxy_config)
        except Exception as e:
            logger.error(f"Failed to test {config['platform']}: {e}")
            
        # Wait between platforms
        await asyncio.sleep(5)
        
    logger.info("\n✅ All tests completed!")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        
    # Run tests
    asyncio.run(main())
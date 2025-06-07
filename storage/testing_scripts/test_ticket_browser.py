#!/usr/bin/env python3
"""
Test script for ticket detection and browser opening functionality
"""

import asyncio
import webbrowser
import logging
from datetime import datetime
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def test_ticket_detection_and_browser():
    """Test detecting a ticket and opening browser immediately"""
    
    logger.info("🔍 Starting ticket detection test...")
    
    # Simulate ticket detection
    mock_ticket = {
        'id': 'test_123',
        'event': 'Bruce Springsteen - Milano 2025',
        'platform': 'fansale',
        'url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388',
        'price': 250.00,
        'section': 'Prato Gold',
        'quantity': 2
    }
    
    logger.info(f"🎟️ TICKET FOUND! {mock_ticket['event']}")
    logger.info(f"   Price: €{mock_ticket['price']}")
    logger.info(f"   Section: {mock_ticket['section']}")
    logger.info(f"   Quantity: {mock_ticket['quantity']}")
    
    # Test 1: Open in default browser
    logger.info("📱 Opening in default browser...")
    try:
        webbrowser.open(mock_ticket['url'])
        logger.info("✅ Browser opened successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to open browser: {e}")
    
    # Test 2: Open with Playwright for automation
    logger.info("\n🤖 Testing automated browser with Playwright...")
    try:
        async with async_playwright() as p:
            # Launch browser in non-headless mode so user can see it
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            logger.info(f"🌐 Navigating to {mock_ticket['url']}...")
            await page.goto(mock_ticket['url'])
            
            logger.info("⏳ Waiting for page to load...")
            await page.wait_for_load_state('networkidle')
            
            # Look for ticket availability
            logger.info("🔍 Checking for ticket elements...")
            
            # Try to find "Add to cart" or similar buttons
            selectors = [
                'button:has-text("aggiungi")',  # Italian "add"
                'button:has-text("carrello")',   # Italian "cart"
                'button:has-text("acquista")',   # Italian "buy"
                '[data-testid="add-to-cart"]',
                '.btn-add-to-cart',
                'button.buy-button'
            ]
            
            button_found = False
            for selector in selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=5000)
                    if button:
                        logger.info(f"✅ Found button with selector: {selector}")
                        
                        # Highlight the button
                        await page.evaluate('''(element) => {
                            element.style.border = "5px solid red";
                            element.style.backgroundColor = "yellow";
                        }''', button)
                        
                        button_found = True
                        break
                except:
                    continue
            
            if button_found:
                logger.info("🎯 READY TO PURCHASE! Button highlighted in red/yellow")
                logger.info("⚠️  In production, we would click this button immediately")
            else:
                logger.info("⚠️  No purchase button found - ticket might be sold out")
            
            # Keep browser open for manual inspection
            logger.info("\n👀 Browser will stay open for 30 seconds for inspection...")
            await asyncio.sleep(30)
            
            await browser.close()
            logger.info("✅ Test completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Playwright test failed: {e}", exc_info=True)

async def test_multiple_platforms():
    """Test different platform URLs"""
    platforms = [
        {
            'name': 'FanSale',
            'url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388'
        },
        {
            'name': 'Ticketmaster',
            'url': 'https://www.ticketmaster.it/event/bruce-springsteen-and-the-e-street-band-biglietti/19815'
        },
        {
            'name': 'VivaTicket',
            'url': 'https://www.vivaticket.com/it/search?q=bruce+springsteen'
        }
    ]
    
    logger.info("\n🌍 Testing multiple platforms...")
    for platform in platforms:
        logger.info(f"\n📍 Testing {platform['name']}...")
        logger.info(f"   URL: {platform['url']}")
        
        # Just test opening in default browser
        try:
            webbrowser.open(platform['url'])
            logger.info(f"   ✅ {platform['name']} opened successfully!")
            await asyncio.sleep(2)  # Brief pause between openings
        except Exception as e:
            logger.error(f"   ❌ {platform['name']} failed: {e}")

async def main():
    """Run all tests"""
    logger.info("🎸 Bruce Springsteen Ticket Detection & Browser Test")
    logger.info("=" * 60)
    
    # Test 1: Basic ticket detection and browser opening
    await test_ticket_detection_and_browser()
    
    # Test 2: Multiple platforms
    await test_multiple_platforms()
    
    logger.info("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
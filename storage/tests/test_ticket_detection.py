#!/usr/bin/env python3
"""
Test Ticket Detection and Extraction with CDP Stealth
Verifies that the script can detect and extract ticket information
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
logger = logging.getLogger('TicketDetectionTest')


async def test_ticket_detection():
    """Test ticket detection on each platform"""
    logger.info("🎫 TESTING TICKET DETECTION WITH CDP STEALTH...")
    
    test_urls = [
        {
            'name': 'Fansale',
            'urls': [
                'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388',
                'https://www.fansale.it/tickets/hard-heavy/bruce-springsteen/1',
                'https://www.fansale.it/fansale/'
            ],
            'selectors': {
                'ticket_container': 'div[class*="offer-list"] > div[class*="offer"], ul[class*="ticket"] li',
                'price': '[class*="price"], .prezzo, .price',
                'section': '[class*="category"], [class*="section"], .categoria, .settore',
                'search_input': 'input[name="search"], input[placeholder*="Cerca"]',
                'search_term': 'bruce springsteen'
            }
        },
        {
            'name': 'Vivaticket',
            'urls': [
                'https://www.vivaticket.com/it/search?q=bruce%20springsteen',
                'https://www.vivaticket.com/it'
            ],
            'selectors': {
                'ticket_container': 'div[class*="event-card"], div[class*="ticket-option"]',
                'price': '[class*="price"], .prezzo',
                'section': '[class*="venue"], [class*="location"]',
                'search_input': 'input[type="search"], input[name="q"]',
                'search_term': 'bruce springsteen'
            }
        }
    ]
    
    async with async_playwright() as p:
        browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
        
        # Get proxy if available
        proxy_config = None
        if os.getenv('IPROYAL_USERNAME'):
            proxy_config = {
                'server': f"http://{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}@{os.getenv('IPROYAL_HOSTNAME', 'geo.iproyal.com')}:{os.getenv('IPROYAL_PORT', '12321')}"
            }
            
        context = await CDPStealthEngine.create_stealth_context(browser, proxy_config)
        
        for platform in test_urls:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing {platform['name']} ticket detection...")
            logger.info(f"{'='*60}")
            
            page = await context.new_page()
            await CDPStealthEngine.apply_page_stealth(page)
            
            ticket_found = False
            
            for url in platform['urls']:
                try:
                    logger.info(f"\nTrying URL: {url}")
                    
                    # Navigate
                    response = await page.goto(url, timeout=45000, wait_until='domcontentloaded')
                    
                    if response and response.status == 200:
                        logger.info(f"✅ Page loaded successfully (Status: {response.status})")
                        
                        # Wait for content
                        await page.wait_for_timeout(3000)
                        
                        # Try search if on main page
                        if platform['name'].lower() in url and 'search' not in url:
                            try:
                                search_input = await page.query_selector(platform['selectors']['search_input'])
                                if search_input:
                                    logger.info("🔍 Found search box, searching for Bruce Springsteen...")
                                    await CDPStealthEngine.type_like_human(
                                        page, 
                                        platform['selectors']['search_input'], 
                                        platform['selectors']['search_term']
                                    )
                                    await page.keyboard.press('Enter')
                                    await page.wait_for_timeout(3000)
                            except:
                                pass
                        
                        # Look for tickets
                        logger.info(f"🔍 Looking for tickets with selector: {platform['selectors']['ticket_container']}")
                        
                        tickets = await page.query_selector_all(platform['selectors']['ticket_container'])
                        
                        if tickets:
                            logger.info(f"🎯 Found {len(tickets)} potential ticket elements!")
                            
                            # Try to extract data from first few tickets
                            for i, ticket in enumerate(tickets[:5]):
                                try:
                                    # Extract price
                                    price_elem = await ticket.query_selector(platform['selectors']['price'])
                                    price_text = await price_elem.inner_text() if price_elem else 'N/A'
                                    
                                    # Extract section/venue
                                    section_elem = await ticket.query_selector(platform['selectors']['section'])
                                    section_text = await section_elem.inner_text() if section_elem else 'N/A'
                                    
                                    # Get all text
                                    all_text = await ticket.inner_text()
                                    
                                    logger.info(f"\n  Ticket {i+1}:")
                                    logger.info(f"    Price: {price_text}")
                                    logger.info(f"    Section/Venue: {section_text}")
                                    logger.info(f"    Full text: {all_text[:100]}...")
                                    
                                    ticket_found = True
                                    
                                except Exception as e:
                                    logger.debug(f"    Error extracting ticket {i+1}: {e}")
                                    
                        else:
                            logger.info("No tickets found with primary selector")
                            
                            # Try alternative detection
                            all_links = await page.query_selector_all('a[href*="ticket"], a[href*="event"]')
                            if all_links:
                                logger.info(f"Found {len(all_links)} ticket/event links")
                                for link in all_links[:3]:
                                    href = await link.get_attribute('href')
                                    text = await link.inner_text()
                                    logger.info(f"  Link: {text[:50]}... -> {href}")
                                    
                        # Take screenshot
                        await page.screenshot(path=f'{platform["name"].lower()}_detection_test.png')
                        logger.info(f"📸 Screenshot saved: {platform['name'].lower()}_detection_test.png")
                        
                        if ticket_found:
                            break  # Found tickets, no need to try other URLs
                            
                    else:
                        logger.warning(f"❌ Failed to load page (Status: {response.status if response else 'No response'})")
                        
                except Exception as e:
                    logger.error(f"Error testing {url}: {str(e)[:100]}")
                    
            await page.close()
            
            if ticket_found:
                logger.info(f"\n✅ {platform['name']}: TICKET DETECTION SUCCESSFUL!")
            else:
                logger.warning(f"\n⚠️ {platform['name']}: No tickets detected (may be none available)")
                
        await browser.close()


async def test_api_interception():
    """Test API response interception for ticket data"""
    logger.info("\n🌐 TESTING API INTERCEPTION...")
    
    api_responses = []
    
    async with async_playwright() as p:
        browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
        context = await CDPStealthEngine.create_stealth_context(browser, None)
        page = await context.new_page()
        await CDPStealthEngine.apply_page_stealth(page)
        
        # Set up response interception
        async def handle_response(response):
            url = response.url
            if any(pattern in url for pattern in ['/api/', '/ajax/', 'ticket', 'offer']):
                try:
                    data = await response.json()
                    api_responses.append({
                        'url': url,
                        'status': response.status,
                        'data': data
                    })
                    logger.info(f"📡 Intercepted API: {url}")
                except:
                    pass
                    
        page.on('response', handle_response)
        
        # Visit a page likely to have API calls
        try:
            await page.goto('https://www.vivaticket.com/it/search?q=bruce%20springsteen', timeout=30000)
            await page.wait_for_timeout(5000)
            
            if api_responses:
                logger.info(f"\n✅ Intercepted {len(api_responses)} API responses!")
                for resp in api_responses[:3]:
                    logger.info(f"  - {resp['url'][:80]}...")
                    if 'data' in resp and isinstance(resp['data'], dict):
                        logger.info(f"    Keys: {list(resp['data'].keys())[:5]}")
            else:
                logger.info("\n⚠️ No API responses intercepted")
                
        except Exception as e:
            logger.error(f"API interception error: {e}")
            
        await browser.close()


async def main():
    """Run all ticket detection tests"""
    logger.info("="*80)
    logger.info("🎫 TICKET DETECTION TEST SUITE")
    logger.info("="*80)
    
    # Test direct ticket detection
    await test_ticket_detection()
    
    # Test API interception
    await test_api_interception()
    
    logger.info("\n" + "="*80)
    logger.info("✅ TICKET DETECTION TESTS COMPLETE")
    logger.info("="*80)
    
    logger.info("\n📊 Summary:")
    logger.info("- Check *_detection_test.png screenshots for visual confirmation")
    logger.info("- If tickets were found, extraction is working")
    logger.info("- If no tickets found, it may be due to no availability")
    logger.info("- API interception can provide alternative data sources")


if __name__ == "__main__":
    asyncio.run(main())
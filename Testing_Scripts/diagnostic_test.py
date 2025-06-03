# Create test_with_real_profiles.py
import asyncio
from playwright.async_api import async_playwright
import yaml
import os

async def test_with_real_profile():
    """Test using your actual configured profiles"""
    
    # Load your browser profiles
    with open('config/browser_profiles.yaml', 'r') as f:
        profiles_config = yaml.safe_load(f)
    
    profile = profiles_config['browser_profiles'][0]  # Use first profile
    print(f"Testing with profile: {profile['name']}")
    
    async with async_playwright() as p:
        # Launch with profile settings
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=f"storage/profiles/{profile['name']}",
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
            ],
            viewport={'width': profile.get('viewport_width', 1920), 
                     'height': profile.get('viewport_height', 1080)},
            user_agent=profile.get('user_agent', None),
            locale=profile.get('locale', 'nl-NL'),
            timezone_id=profile.get('timezone', 'Europe/Amsterdam')
        )
        
        page = await browser.new_page() if hasattr(browser, 'new_page') else browser.pages()[0]
        
        # Apply stealth
        with open('src/core/stealth_init.js', 'r') as f:
            await page.add_init_script(f.read())
        
        # Test Ticketmaster
        print("\nTesting Ticketmaster with real profile...")
        await page.goto('https://www.ticketmaster.nl')
        await page.wait_for_timeout(5000)
        
        title = await page.title()
        print(f"Page loaded: {title}")
        
        # Try searching for an event
        print("\nTrying to search for events...")
        try:
            search_box = await page.wait_for_selector('input[type="search"], input[placeholder*="Search"]', timeout=5000)
            await search_box.type("Bruce Springsteen", delay=100)
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(3000)
            
            print("Search completed successfully!")
        except:
            print("Could not find search box")
        
        input("\nPress Enter to close...")
        await browser.close()

asyncio.run(test_with_real_profile())
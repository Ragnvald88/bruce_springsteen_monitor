#!/usr/bin/env python3
"""Run bot with better error handling"""

import os
import sys
import subprocess

# Clean Chrome processes
print("🧹 Cleaning Chrome processes...")
subprocess.run(["pkill", "-f", "Google Chrome"], capture_output=True)
subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True)

# Set environment
os.environ['FANSALE_TARGET_URL'] = 'https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388'
os.environ['TWOCAPTCHA_API_KEY'] = 'c58050aca5076a2a26ba2eff1c429d4d'

from fansale_check import FanSaleBotV7, BotConfig

print("\n🤖 Starting FanSale Bot V7")
print("="*60)

# Configure bot
config = BotConfig()
config.browsers_count = 1  # Start with just 1
config.max_tickets = 2

# Create bot
bot = FanSaleBotV7(config)

# Set ticket types directly
bot.ticket_types_to_hunt = {'prato_a', 'prato_b', 'settore', 'other'}
bot.num_browsers = 1
bot.max_tickets = 2

print(f"✅ Bot configured:")
print(f"   • Browsers: {bot.num_browsers}")
print(f"   • Max tickets: {bot.max_tickets}")
print(f"   • Hunting: {bot.ticket_types_to_hunt}")
print(f"   • URL: {bot.target_url[:50]}...")

# Skip the configure method and go straight to browser creation
print("\n🚀 Creating browser...")

try:
    # Manually start hunting without the full run() method
    driver = bot.create_browser(1)
    print("✅ Browser created!")
    
    # Navigate to page
    print(f"\n📍 Navigating to target URL...")
    driver.get(bot.target_url)
    print("✅ Page loaded!")
    
    # Check for tickets
    print("\n🔍 Looking for tickets...")
    import time
    time.sleep(3)
    
    # Find tickets using bot's selectors
    ticket_selectors = [
        "div[data-qa='ticketToBuy']",
        "div[class*='ticket'][class*='available']",
        "div[class*='biglietto'][class*='disponibile']",
        "article[class*='ticket']",
        "div[data-testid*='ticket']"
    ]
    
    tickets_found = False
    for selector in ticket_selectors:
        try:
            tickets = driver.find_elements("css selector", selector)
            if tickets:
                print(f"✅ Found {len(tickets)} tickets with selector: {selector}")
                tickets_found = True
                break
        except:
            continue
    
    if not tickets_found:
        print("❌ No tickets found on page")
    
    # Keep browser open for inspection
    print("\n⏸️  Browser will stay open for 10 seconds...")
    time.sleep(10)
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        if 'driver' in locals():
            driver.quit()
            print("\n✅ Browser closed")
    except:
        pass
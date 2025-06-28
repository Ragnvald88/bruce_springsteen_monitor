#!/usr/bin/env python3
"""Diagnose why the bot isn't reserving tickets"""

import os
import time
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()

# Set URL if not set
if not os.getenv('FANSALE_TARGET_URL'):
    os.environ['FANSALE_TARGET_URL'] = 'https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388'

print("🔍 FanSale Bot Diagnostic")
print("="*60)

from fansale_check import FanSaleBotV7, BotConfig

# Create bot
config = BotConfig(browsers_count=1)
bot = FanSaleBotV7(config)

# Create single browser
print("\n1️⃣ Creating browser...")
driver = bot.create_browser(1)

try:
    print("2️⃣ Navigating to FanSale...")
    driver.get(bot.target_url)
    time.sleep(3)
    
    print("3️⃣ Dismissing popups...")
    popups = bot.dismiss_popups(driver, 1)
    print(f"   Dismissed {popups} popups")
    
    if popups > 0:
        print("   Waiting for page reload after popup...")
        time.sleep(3)
    
    print("\n4️⃣ Checking for tickets...")
    tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
    print(f"   Found {len(tickets)} ticket cards")
    
    if tickets:
        print("\n✅ TICKETS ARE AVAILABLE!")
        print("   Bot should be working. Let's test the purchase flow...")
        
        # Test clicking first ticket
        ticket = tickets[0]
        ticket_text = ticket.text[:100]
        print(f"\n5️⃣ Testing ticket click on: {ticket_text}...")
        
        # Click ticket
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", ticket)
        print("   ✅ Clicked ticket card")
        
        # Wait for navigation
        time.sleep(2)
        
        # Check for buy button
        print("\n6️⃣ Looking for buy button...")
        buy_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-qa='buyNowButton']")
        
        if buy_buttons:
            print(f"   ✅ Found {len(buy_buttons)} buy buttons!")
            print("   🎯 BOT SHOULD BE ABLE TO PURCHASE!")
            
            # Check button details
            btn = buy_buttons[0]
            print(f"\n   Buy button details:")
            print(f"   - Text: '{btn.text}'")
            print(f"   - Visible: {btn.is_displayed()}")
            print(f"   - Enabled: {btn.is_enabled()}")
            
        else:
            print("   ❌ No buy button found after clicking ticket")
            print("   Checking page URL...")
            print(f"   Current URL: {driver.current_url}")
            
            # Check for alternative selectors
            alt_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Acquista')]")
            if alt_buttons:
                print(f"   Found {len(alt_buttons)} buttons with 'Acquista' text")
    
    else:
        print("\n❌ NO TICKETS AVAILABLE")
        print("   This is why the bot isn't purchasing - no tickets to buy!")
        
        # Check for alternative messages
        no_tickets_msgs = driver.find_elements(By.XPATH, "//*[contains(text(), 'non disponibili') or contains(text(), 'sold out')]")
        if no_tickets_msgs:
            print(f"   Found 'no tickets' message: {no_tickets_msgs[0].text[:100]}")
    
    print("\n7️⃣ Checking page structure...")
    print(f"   Page title: {driver.title}")
    print(f"   Page URL: {driver.current_url}")
    
    # Keep browser open
    print("\n⏸️  Browser will stay open for 30 seconds...")
    print("   Inspect the page to verify!")
    time.sleep(30)
    
except Exception as e:
    print(f"\n❌ Error during diagnostic: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("\n✅ Diagnostic complete!")
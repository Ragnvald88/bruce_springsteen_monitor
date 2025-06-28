#!/usr/bin/env python3
"""Super simple test - are we on the right page?"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

print("🔍 Simple FanSale Test")
print("="*40)

driver = uc.Chrome(version_main=137)

try:
    # Go to the URL
    url = "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388"
    driver.get(url)
    print(f"✅ Loaded: {url}")
    
    time.sleep(5)
    
    # Check what's on the page
    print("\n📄 Page Analysis:")
    
    # 1. Are we on the right page?
    if "bruce" in driver.page_source.lower():
        print("✅ Bruce Springsteen page confirmed")
    else:
        print("❌ Wrong page!")
    
    # 2. Is there a popup blocking us?
    popups = driver.find_elements(By.CSS_SELECTOR, "button.js-BotProtectionModalButton1")
    if popups:
        print(f"⚠️  Found {len(popups)} 'Carica Offerte' buttons - NEED TO CLICK!")
        driver.execute_script("arguments[0].click();", popups[0])
        print("✅ Clicked popup")
        time.sleep(3)
    
    # 3. NOW check for tickets
    tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
    print(f"\n🎫 Tickets found: {len(tickets)}")
    
    if tickets:
        # 4. Can we see the buy button WITHOUT clicking the ticket?
        buy_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-qa='buyNowButton']")
        print(f"💰 Buy buttons visible: {len(buy_buttons)}")
        
        if buy_buttons:
            print("\n✨ INSIGHT: Buy buttons are ALREADY visible!")
            print("   Maybe we don't need to click tickets first?")
            
            # Test clicking buy directly
            btn = buy_buttons[0]
            print(f"\n🎯 Buy button text: '{btn.text}'")
            print(f"   Location: {btn.location}")
            print(f"   Displayed: {btn.is_displayed()}")
    
    print("\n" + "="*40)
    print("💡 Key Finding: Check if buy buttons are directly clickable!")
    
    time.sleep(10)
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    driver.quit()
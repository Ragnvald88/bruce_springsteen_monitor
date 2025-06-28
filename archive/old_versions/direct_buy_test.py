#!/usr/bin/env python3
"""Direct approach - just find and click buy buttons!"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

print("🎯 DIRECT BUY TEST - Keep it simple!")
print("="*50)

driver = uc.Chrome(version_main=137)

try:
    # Navigate
    driver.get("https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388")
    time.sleep(3)
    
    # Click popup to load offers
    try:
        popup = driver.find_element(By.CSS_SELECTOR, "button.js-BotProtectionModalButton1")
        driver.execute_script("arguments[0].click();", popup)
        print("✅ Clicked 'Carica Offerte'")
        time.sleep(3)
    except:
        print("No popup")
    
    # DIRECT APPROACH - Just look for buy buttons!
    print("\n🔍 Looking for ANY 'Acquista' buttons on page...")
    
    # Method 1: By data-qa
    buy_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-qa='buyNowButton']")
    print(f"Found by data-qa: {len(buy_buttons)}")
    
    # Method 2: By text
    all_buttons = driver.find_elements(By.TAG_NAME, "button")
    acquista_buttons = [b for b in all_buttons if "acquista" in b.text.lower()]
    print(f"Found by text 'Acquista': {len(acquista_buttons)}")
    
    # Method 3: Check if tickets and buy buttons are in same container
    offers = driver.find_elements(By.CSS_SELECTOR, "div[class*='OfferEntry']")
    print(f"Found offer containers: {len(offers)}")
    
    if buy_buttons:
        print("\n💡 BREAKTHROUGH: Buy buttons are directly accessible!")
        print("We might not need to click tickets first!")
        
        # Analyze first buy button
        btn = buy_buttons[0]
        print(f"\nFirst buy button:")
        print(f"  Text: {btn.text}")
        print(f"  Visible: {btn.is_displayed()}")
        
        # Find parent to understand context
        parent = btn.find_element(By.XPATH, "..")
        print(f"  Parent class: {parent.get_attribute('class')}")
        
        # Is there ticket info nearby?
        container = btn.find_element(By.XPATH, "./ancestor::div[contains(@class,'Offer') or contains(@class,'ticket')]")
        print(f"  Container text preview: {container.text[:100]}...")
        
    print("\n" + "="*50)
    print("🤔 THEORY: Maybe FanSale shows tickets WITH buy buttons")
    print("   No need to click ticket first - just click 'Acquista'!")
    
    # Keep browser open
    time.sleep(20)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
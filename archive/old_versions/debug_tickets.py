#!/usr/bin/env python3
"""Debug ticket detection on FanSale"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import os

# Set up environment
os.environ['FANSALE_TARGET_URL'] = 'https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388'

print("🔍 Debugging FanSale Ticket Detection")
print("="*60)

# Create browser
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

print("Creating browser...")
driver = uc.Chrome(options=options, version_main=137)

try:
    # Navigate to page
    url = os.environ['FANSALE_TARGET_URL']
    print(f"\nNavigating to: {url}")
    driver.get(url)
    
    print("\nWaiting for page to load...")
    time.sleep(5)
    
    # Check for popups
    print("\nChecking for popups...")
    popup_selectors = [
        "button.js-BotProtectionModalButton1",
        "button[class*='BotProtection']",
        "div.BotProtectionModal button"
    ]
    
    for selector in popup_selectors:
        try:
            popup = driver.find_element(By.CSS_SELECTOR, selector)
            if popup.is_displayed():
                print(f"✅ Found popup: {selector}")
                driver.execute_script("arguments[0].click();", popup)
                print("   Clicked!")
                time.sleep(2)
        except:
            pass
    
    # Try all ticket selectors
    print("\n🎫 Searching for tickets...")
    
    ticket_selectors = [
        ("div[data-qa='ticketToBuy']", "FanSale primary selector"),
        ("div[class*='ticket'][class*='available']", "Available ticket class"),
        ("div[class*='biglietto'][class*='disponibile']", "Italian ticket class"),
        ("article[class*='ticket']", "Article ticket"),
        ("div[data-testid*='ticket']", "Test ID ticket"),
        ("div.sc-gvZAcH", "Specific class from FanSale"),
        ("div[class*='OfferEntry']", "Offer entry"),
        ("a[id*='detailBShowOfferButton']", "Show offer button"),
        ("div.ticketContainer", "Ticket container"),
        ("div[class*='ticket-item']", "Ticket item class")
    ]
    
    tickets_found = False
    for selector, description in ticket_selectors:
        try:
            tickets = driver.find_elements(By.CSS_SELECTOR, selector)
            if tickets:
                print(f"\n✅ FOUND {len(tickets)} tickets with: {selector}")
                print(f"   Description: {description}")
                
                # Show first ticket's text
                if tickets[0].text:
                    print(f"   First ticket text: {tickets[0].text[:100]}...")
                
                tickets_found = True
        except Exception as e:
            print(f"❌ Error with {selector}: {e}")
    
    if not tickets_found:
        print("\n❌ NO TICKETS FOUND with any selector!")
        
        # Check page source
        print("\n📄 Checking page source for ticket-related content...")
        page_source = driver.page_source.lower()
        
        keywords = ['ticket', 'biglietto', 'offer', 'offerta', 'disponibile', 'available']
        for keyword in keywords:
            if keyword in page_source:
                print(f"   ✅ Found '{keyword}' in page source")
        
        # Save screenshot
        print("\n📸 Saving screenshot...")
        driver.save_screenshot("debug_no_tickets.png")
        print("   Saved as: debug_no_tickets.png")
    
    # Keep browser open for manual inspection
    print("\n⏸️  Browser will stay open for 30 seconds for inspection...")
    print("   Check if tickets are visible on the page")
    time.sleep(30)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("\n✅ Debug complete")
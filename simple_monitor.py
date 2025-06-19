#!/usr/bin/env python3
"""
Dead Simple Fansale Monitor - No bullshit, just works
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# Fix for Python 3.12+
import sys
if sys.version_info >= (3, 12):
    import types
    sys.modules['distutils'] = types.ModuleType('distutils')
    sys.modules['distutils.version'] = types.ModuleType('distutils.version')
    sys.modules['distutils.version'].LooseVersion = str


def create_driver():
    """Create undetected Chrome driver - simple as possible"""
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    return uc.Chrome(options=options)


def check_fansale(driver, url):
    """Check for tickets on Fansale"""
    driver.get(url)
    time.sleep(random.uniform(3, 5))
    
    # Handle cookie popup if exists
    try:
        cookie_btn = driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
        cookie_btn.click()
        time.sleep(1)
        print("✓ Cookies accepted")
    except:
        pass
    
    # Check if blocked
    if "access denied" in driver.page_source.lower():
        print("❌ BLOCKED! Waiting 60s...")
        time.sleep(60)
        return False
    
    # Look for tickets
    tickets = driver.find_elements(By.CSS_SELECTOR, ".offer-item")
    if tickets:
        print(f"🎫 FOUND {len(tickets)} TICKETS!")
        return True
    else:
        print("No tickets yet...")
        return False


def main():
    url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
    driver = create_driver()
    
    try:
        while True:
            try:
                found = check_fansale(driver, url)
                
                # Wait before next check
                if found:
                    time.sleep(10)  # Quick recheck if tickets found
                else:
                    time.sleep(30)  # Normal interval
                    
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(10)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

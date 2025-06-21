#!/usr/bin/env python3
"""Simple test to see what's on Fansale pages"""

import sys
import os
from pathlib import Path

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

def test_fansale():
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(options=options)
    
    try:
        # 1. Go directly to ticket page
        print("\n1. Going to ticket page...")
        driver.get("https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
        time.sleep(5)
        
        # 2. Check if we need to login
        page_text = driver.page_source
        if "Accedi" in page_text and "Il mio account" not in page_text:
            print("   Need to login - finding login button...")
            
            # Find and click Accedi
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                if "Accedi" in link.text:
                    print(f"   Found login link: {link.text}")
                    link.click()
                    time.sleep(5)
                    break
            
            # Now on TicketOne - login
            current_url = driver.current_url
            print(f"   Current URL: {current_url}")
            
            if "ticketone.it" in current_url:
                print("   On TicketOne login page")
                
                # Fill credentials
                username = driver.find_element(By.ID, "username")
                username.send_keys(os.getenv('FANSALE_EMAIL'))
                
                password = driver.find_element(By.ID, "password")
                password.send_keys(os.getenv('FANSALE_PASSWORD'))
                
                # Click login
                login_btn = driver.find_element(By.ID, "loginCustomerButton")
                login_btn.click()
                
                print("   Logging in...")
                time.sleep(10)
                
                # Should be back on Fansale
                print(f"   After login URL: {driver.current_url}")
        
        # 3. Now check what's on the page
        print("\n3. Analyzing page structure...")
        
        # Look for ANY elements that might be tickets
        selectors_to_try = [
            "article",
            "div[class*='offer']",
            "div[class*='ticket']",
            "div[class*='listing']",
            "div[class*='event']",
            "tr",  # Tables?
            "li[class*='offer']",
            "li[class*='ticket']",
            "[data-testid]",
            ".card",
            ".item"
        ]
        
        for selector in selectors_to_try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"\n   Found {len(elements)} elements with selector: {selector}")
                # Check first element
                if len(elements) > 0:
                    elem = elements[0]
                    text = elem.text[:100] if elem.text else "No text"
                    classes = elem.get_attribute("class") or "No classes"
                    print(f"   First element: class='{classes}'")
                    print(f"   Text: {text}...")
                    
                    # Look for price in element
                    if "€" in elem.text:
                        print("   ✓ Contains price!")
        
        # 4. Look for buttons/links that might reserve tickets
        print("\n4. Looking for action buttons...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Found {len(buttons)} buttons")
        for i, btn in enumerate(buttons[:5]):
            if btn.text:
                print(f"   Button {i}: '{btn.text}'")
        
        # Also check for links that might be "buy" actions
        buy_links = driver.find_elements(By.XPATH, "//a[contains(@class, 'btn') or contains(@class, 'button')]")
        print(f"\n   Found {len(buy_links)} button-like links")
        for i, link in enumerate(buy_links[:5]):
            if link.text:
                print(f"   Link {i}: '{link.text}'")
        
        # 5. Save page source for analysis
        with open("fansale_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\n5. Saved page source to fansale_page_source.html")
        
        input("\nPress Enter to close browser...")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    test_fansale()
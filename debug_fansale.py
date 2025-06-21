#!/usr/bin/env python3
"""Debug Fansale to understand the actual page structure"""

import sys
from pathlib import Path

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import time
import os
from dotenv import load_dotenv
from urllib.parse import quote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

load_dotenv()

def debug_fansale():
    # Setup proxy from .env
    proxy_url = None
    if os.getenv('IPROYAL_USERNAME'):
        proxy_user = os.getenv('IPROYAL_USERNAME')
        proxy_pass = os.getenv('IPROYAL_PASSWORD')
        proxy_host = os.getenv('IPROYAL_HOSTNAME')
        proxy_port = os.getenv('IPROYAL_PORT')
        if all([proxy_user, proxy_pass, proxy_host, proxy_port]):
            encoded_pass = quote(proxy_pass, safe='')
            proxy_url = f"http://{proxy_user}:{encoded_pass}@{proxy_host}:{proxy_port}"
    
    # Create driver
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    if proxy_url:
        options.add_argument(f'--proxy-server={proxy_url}')
        print(f"Using proxy: {proxy_url[:30]}...")
    
    driver = uc.Chrome(options=options)
    
    try:
        # Go directly to the ticket URL
        url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        print(f"\n1. Going directly to ticket URL: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Save screenshot
        driver.save_screenshot("debug_1_ticket_page.png")
        print("   Screenshot saved: debug_1_ticket_page.png")
        
        # Check page content
        page_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"\n2. Page contains 'Accedi'? {'Accedi' in page_text}")
        print(f"   Page contains 'Login'? {'Login' in page_text or 'login' in page_text}")
        print(f"   Page contains 'ticket'? {'ticket' in page_text.lower()}")
        print(f"   Page contains '€'? {'€' in page_text}")
        
        # Look for login-related elements
        print("\n3. Looking for login elements:")
        login_selectors = [
            "a:contains('Accedi')",
            "[class*='login']",
            "[class*='Login']",
            "button",
            "a[href*='login']",
            ".Header-Button"
        ]
        
        # Try finding any buttons or links
        all_links = driver.find_elements(By.TAG_NAME, "a")
        print(f"\n4. Found {len(all_links)} links on page")
        for i, link in enumerate(all_links[:10]):
            text = link.text.strip()
            href = link.get_attribute("href")
            if text:
                print(f"   Link {i}: '{text}' -> {href}")
        
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\n5. Found {len(all_buttons)} buttons on page")
        for i, button in enumerate(all_buttons[:5]):
            text = button.text.strip()
            if text:
                print(f"   Button {i}: '{text}'")
        
        # Check for tickets
        print("\n6. Looking for ticket elements:")
        potential_tickets = driver.find_elements(By.XPATH, "//*[contains(@class, 'offer') or contains(@class, 'ticket') or contains(@class, 'listing')]")
        print(f"   Found {len(potential_tickets)} potential ticket elements")
        
        # Check if we need to accept cookies
        cookie_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Accetta') or contains(@class, 'cookie')]")
        if cookie_buttons:
            print("\n7. Found cookie banner, accepting...")
            cookie_buttons[0].click()
            time.sleep(2)
        
        # Try to navigate to login from homepage
        print("\n8. Going to Fansale homepage...")
        driver.get("https://www.fansale.it")
        time.sleep(3)
        driver.save_screenshot("debug_2_homepage.png")
        print("   Screenshot saved: debug_2_homepage.png")
        
        # Look for login button on homepage
        homepage_links = driver.find_elements(By.TAG_NAME, "a")
        for link in homepage_links:
            if "Accedi" in link.text or "Login" in link.text:
                print(f"\n9. Found login link: '{link.text}'")
                print(f"   Clicking it...")
                link.click()
                time.sleep(5)
                driver.save_screenshot("debug_3_after_login_click.png")
                print("   Screenshot saved: debug_3_after_login_click.png")
                print(f"   Current URL: {driver.current_url}")
                break
        
        # Check what's on the login page
        input_fields = driver.find_elements(By.TAG_NAME, "input")
        print(f"\n10. Found {len(input_fields)} input fields")
        for field in input_fields:
            field_id = field.get_attribute("id")
            field_name = field.get_attribute("name")
            field_type = field.get_attribute("type")
            if field_id or field_name:
                print(f"    Input: id='{field_id}', name='{field_name}', type='{field_type}'")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nDebug session complete. Check the screenshots.")
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    debug_fansale()
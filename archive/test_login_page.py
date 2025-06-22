#!/usr/bin/env python3
"""
Quick test to check FanSale login page structure
"""

import time
import os
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

def test_login_page():
    """Test FanSale login page to find correct selectors"""
    
    print("🔍 Testing FanSale login page structure...")
    
    # Setup driver (minimal options for testing)
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(options=options)
    
    try:
        # Go to login page
        print("\n📄 Loading login page...")
        driver.get("https://www.fansale.it/fansale/login.htm")
        time.sleep(3)
        
        # Handle cookie popup if present
        try:
            cookie_btn = driver.find_element(By.XPATH, "//button[contains(., 'ACCETTA')]")
            cookie_btn.click()
            print("✅ Cookie banner accepted")
        except:
            print("ℹ️  No cookie banner found")
        
        print("\n🔍 Looking for login form elements...")
        
        # Test different possible selectors
        selectors_to_test = {
            "Email inputs": [
                'input[name="login_email"]',
                'input[name="email"]',
                'input[type="email"]',
                '#login_email',
                '#email',
                'input[name="login[email]"]',
                'input[name="username"]'
            ],
            "Password inputs": [
                'input[name="login_password"]',
                'input[name="password"]',
                'input[type="password"]',
                '#login_password',
                '#password',
                'input[name="login[password]"]'
            ],
            "Login buttons": [
                '#loginCustomerButton',
                'button[type="submit"]',
                'input[type="submit"]',
                '.login-button',
                'button[class*="login"]',
                'button[class*="submit"]'
            ]
        }
        
        found_elements = {}
        
        for category, selectors in selectors_to_test.items():
            print(f"\n📋 Testing {category}:")
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"  ✅ Found: {selector}")
                    print(f"     Tag: {element.tag_name}")
                    print(f"     ID: {element.get_attribute('id') or 'none'}")
                    print(f"     Name: {element.get_attribute('name') or 'none'}")
                    print(f"     Class: {element.get_attribute('class') or 'none'}")
                    
                    if category not in found_elements:
                        found_elements[category] = element
                        
                except:
                    pass
        
        # Print page source snippet for manual inspection
        print("\n📜 Login form HTML snippet:")
        try:
            form = driver.find_element(By.TAG_NAME, "form")
            print(form.get_attribute('outerHTML')[:500] + "...")
        except:
            print("Could not find form element")
        
        input("\n⏸️  Press Enter to close browser and continue...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_login_page()

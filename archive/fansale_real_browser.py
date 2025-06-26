#!/usr/bin/env python3
"""
FanSale Bot - Real Browser Profile Method
Uses your actual Chrome profile to avoid detection
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def use_real_browser_profile():
    """
    Use your real Chrome profile to avoid detection
    """
    print("""
    🌐 REAL BROWSER PROFILE METHOD
    ==============================
    
    This method uses your actual Chrome profile with all your
    cookies, extensions, and history - making it indistinguishable
    from your normal browsing.
    
    IMPORTANT: Close all Chrome windows before running!
    
    """)
    
    input("Press Enter when ready...")
    
    # Find Chrome profile path
    profile_paths = {
        'darwin': os.path.expanduser('~/Library/Application Support/Google/Chrome/'),
        'win32': os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\'),
        'linux': os.path.expanduser('~/.config/google-chrome/')
    }
    
    import sys
    chrome_profile_path = profile_paths.get(sys.platform, '')
    
    if not os.path.exists(chrome_profile_path):
        logger.error(f"Chrome profile not found at: {chrome_profile_path}")
        return None
    
    logger.info(f"Using Chrome profile from: {chrome_profile_path}")
    
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument(f'--user-data-dir={chrome_profile_path}')
    options.add_argument('--profile-directory=Default')  # or 'Profile 1', etc.
    
    # Disable automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Create driver
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("✅ Browser opened with your real profile!")
        return driver
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        logger.info("\nMake sure:")
        logger.info("1. All Chrome windows are closed")
        logger.info("2. ChromeDriver version matches your Chrome")
        logger.info("3. Try running: python3 fix_chromedriver.py")
        return None

def simple_ticket_hunter(driver, target_url, ticket_types):
    """
    Simple ticket hunter that works with real browser
    """
    logger.info("Starting simple ticket hunt...")
    
    # Navigate
    driver.get(target_url)
    time.sleep(3)
    
    tickets_secured = 0
    check_count = 0
    
    while True:
        try:
            check_count += 1
            
            # Look for tickets
            tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
            
            if tickets:
                logger.info(f"Found {len(tickets)} tickets!")
                
                for ticket in tickets:
                    ticket_text = ticket.text.lower()
                    
                    # Check if target type
                    for ticket_type in ticket_types:
                        if ticket_type in ticket_text:
                            logger.info(f"🎯 Found {ticket_type} ticket!")
                            
                            try:
                                # Click ticket
                                ticket.click()
                                time.sleep(1)
                                
                                # Look for purchase button
                                purchase_btn = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                                        "[data-qa='purchaseButton'], button[class*='purchase']"))
                                )
                                
                                purchase_btn.click()
                                logger.info("✅ PURCHASE CLICKED!")
                                
                                tickets_secured += 1
                                
                            except Exception as e:
                                logger.error(f"Purchase failed: {e}")
            
            # Status
            if check_count % 10 == 0:
                logger.info(f"Checks: {check_count} | Secured: {tickets_secured}")
            
            # Human-like wait
            time.sleep(random.uniform(2, 4))
            
        except KeyboardInterrupt:
            logger.info("Stopped by user")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(2)
    
    return tickets_secured

def main():
    """
    Main function
    """
    print("""
    🎫 FANSALE BOT - REAL BROWSER METHOD
    ====================================
    
    This uses your actual Chrome profile to avoid ALL detection.
    It's the most reliable method but requires closing Chrome first.
    
    Options:
    1. Use my real Chrome profile (most reliable)
    2. Use the ultimate stealth bot
    3. Exit
    """)
    
    choice = input("Select (1-3): ").strip()
    
    if choice == '1':
        driver = use_real_browser_profile()
        
        if driver:
            target_url = 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388'
            ticket_types = ['prato a', 'prato b']
            
            try:
                tickets = simple_ticket_hunter(driver, target_url, ticket_types)
                logger.info(f"\n✅ Session complete! Tickets secured: {tickets}")
            finally:
                driver.quit()
                
    elif choice == '2':
        os.system("python3 fansale_ultimate_stealth.py")
    else:
        print("Goodbye!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SIMPLIFIED FANSALE BOT - Direct Buy Approach
Just find 'Acquista' buttons and click them!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import os
from datetime import datetime

print("🎯 SIMPLIFIED FANSALE BOT")
print("="*50)
print("Strategy: Find 'Acquista' buttons and click them directly!")
print("="*50)

# Configuration
TARGET_URL = os.getenv('FANSALE_TARGET_URL', 
                       "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388")
CHECK_INTERVAL = 2  # seconds between checks
PURCHASES_MADE = 0
MAX_PURCHASES = 2

# Create browser
print("\n🌐 Starting browser...")
options = uc.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
driver = uc.Chrome(options=options, version_main=137)

def log(message, emoji=""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{timestamp} {emoji} {message}")

try:
    # Navigate
    log(f"Navigating to: {TARGET_URL}", "📍")
    driver.get(TARGET_URL)
    time.sleep(3)
    
    # Dismiss initial popup
    try:
        popup = driver.find_element(By.CSS_SELECTOR, "button.js-BotProtectionModalButton1")
        driver.execute_script("arguments[0].click();", popup)
        log("Clicked 'Carica Offerte' popup", "✅")
        time.sleep(3)
    except:
        log("No initial popup found", "ℹ️")
    
    log("Starting hunt for 'Acquista' buttons!", "🏃")
    checks = 0
    
    # Main loop - KEEP IT SIMPLE!
    while PURCHASES_MADE < MAX_PURCHASES:
        checks += 1
        
        # Look for buy buttons DIRECTLY
        buy_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-qa='buyNowButton']")
        
        if buy_buttons:
            log(f"FOUND {len(buy_buttons)} BUY BUTTONS!", "🎫")
            
            for i, button in enumerate(buy_buttons):
                if PURCHASES_MADE >= MAX_PURCHASES:
                    break
                    
                try:
                    # Check if button is clickable
                    if button.is_displayed() and button.is_enabled():
                        # Get ticket info from parent container
                        container = button.find_element(By.XPATH, 
                            "./ancestor::div[contains(@class,'OfferEntry') or contains(@class,'ticket')]")
                        ticket_info = container.text.replace('\n', ' ')[:100]
                        
                        log(f"Attempting to buy: {ticket_info}...", "💰")
                        
                        # CLICK THE BUY BUTTON!
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", button)
                        
                        log("CLICKED BUY BUTTON!", "✅")
                        PURCHASES_MADE += 1
                        
                        # Wait to see what happens
                        time.sleep(3)
                        
                        # Check for CAPTCHA
                        captchas = driver.find_elements(By.CSS_SELECTOR, "div.g-recaptcha, iframe[src*='recaptcha']")
                        if captchas:
                            log("CAPTCHA detected! Need manual solve or 2captcha", "🤖")
                            # In real bot, handle with 2captcha
                            time.sleep(30)  # Wait for manual solve
                        
                        # Take screenshot
                        driver.save_screenshot(f"purchase_{PURCHASES_MADE}_{int(time.time())}.png")
                        log(f"Screenshot saved", "📸")
                        
                except Exception as e:
                    log(f"Error clicking button {i}: {e}", "❌")
                    continue
        
        else:
            # No buy buttons found
            if checks % 30 == 0:  # Log every 30 checks
                log(f"No tickets available (checked {checks} times)", "🔍")
        
        # Check for popups periodically
        if checks % 10 == 0:
            try:
                popup = driver.find_element(By.CSS_SELECTOR, "button[class*='BotProtection']")
                if popup.is_displayed():
                    driver.execute_script("arguments[0].click();", popup)
                    log("Dismissed popup", "📢")
            except:
                pass
        
        # Refresh page periodically
        if checks % 100 == 0:  # Every ~3 minutes
            log("Refreshing page...", "🔄")
            driver.refresh()
            time.sleep(3)
            # Re-dismiss popup after refresh
            try:
                popup = driver.find_element(By.CSS_SELECTOR, "button.js-BotProtectionModalButton1")
                driver.execute_script("arguments[0].click();", popup)
                time.sleep(2)
            except:
                pass
        
        time.sleep(CHECK_INTERVAL)
    
    log(f"MAX PURCHASES REACHED ({MAX_PURCHASES})!", "🎉")
    
except KeyboardInterrupt:
    log("Stopped by user", "👋")
except Exception as e:
    log(f"Error: {e}", "❌")
    import traceback
    traceback.print_exc()
finally:
    log(f"Total checks: {checks}", "📊")
    log(f"Purchases made: {PURCHASES_MADE}", "💰")
    driver.quit()
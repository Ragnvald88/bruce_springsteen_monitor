"""
Session management and automatic login utilities
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)


class SessionManager:
    """Handle automatic login and session management"""
    
    @staticmethod
    def auto_login(driver, email: str, password: str, max_attempts: int = 3) -> bool:
        """Automatically login to FanSale with anti-detection measures"""
        for attempt in range(max_attempts):
            try:
                logger.info(f"Auto-login attempt {attempt + 1}/{max_attempts}")
                
                # Navigate to login page
                driver.get("https://www.fansale.it/fansale/login.htm")
                time.sleep(2)
                
                # Wait for login form
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-qa='loginEmail'], input[type='email'], input[name='email']"))
                )
                
                password_field = driver.find_element(By.CSS_SELECTOR, "[data-qa='loginPassword'], input[type='password'], input[name='password']")
                
                # Human-like typing with delays
                email_field.click()
                time.sleep(0.5)
                
                # Clear and type email character by character
                email_field.clear()
                for char in email:
                    email_field.send_keys(char)
                    time.sleep(0.05 + (0.1 if char == '@' else 0))  # Pause more on special chars
                
                time.sleep(0.5)
                
                # Move to password field
                password_field.click()
                time.sleep(0.3)
                
                # Type password
                for char in password:
                    password_field.send_keys(char)
                    time.sleep(0.04)
                
                time.sleep(0.5)
                
                # Find and click login button
                login_button = driver.find_element(By.CSS_SELECTOR, "[data-qa='loginSubmit'], button[type='submit'], input[type='submit']")
                
                # Move mouse to button area first (anti-bot)
                driver.execute_script("""
                    const button = arguments[0];
                    const rect = button.getBoundingClientRect();
                    const event = new MouseEvent('mousemove', {
                        clientX: rect.left + rect.width / 2,
                        clientY: rect.top + rect.height / 2,
                        bubbles: true
                    });
                    document.dispatchEvent(event);
                """, login_button)
                
                time.sleep(0.3)
                login_button.click()
                
                # Wait for login to complete
                time.sleep(3)
                
                # Check if login successful
                if "login" not in driver.current_url.lower():
                    logger.info("✅ Auto-login successful!")
                    return True
                else:
                    logger.warning(f"Login attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
                    
            except TimeoutException:
                logger.error("Login form not found")
            except Exception as e:
                logger.error(f"Auto-login error: {e}")
                time.sleep(2)
        
        logger.error("Auto-login failed after all attempts")
        return False
    
    @staticmethod
    def handle_cookies(driver) -> bool:
        """Handle cookie consent banners"""
        try:
            # Common cookie accept selectors
            cookie_selectors = [
                "//button[contains(text(), 'ACCETTA')]",
                "//button[contains(text(), 'Accetta')]",
                "//button[contains(@class, 'accept')]",
                "//a[contains(text(), 'Accetto')]",
                "button#accept-cookies"
            ]
            
            for selector in cookie_selectors:
                try:
                    if selector.startswith('//'):
                        cookie_btn = driver.find_element(By.XPATH, selector)
                    else:
                        cookie_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if cookie_btn.is_displayed():
                        cookie_btn.click()
                        logger.info("✅ Accepted cookies")
                        time.sleep(1)
                        return True
                except:
                    continue
                    
        except:
            pass
        
        return False

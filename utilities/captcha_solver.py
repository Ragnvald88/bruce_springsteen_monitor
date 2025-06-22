"""
CAPTCHA solving integration for StealthMaster
Supports 2Captcha service for solving various CAPTCHA types
"""

import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By

logger = logging.getLogger('StealthMaster.CaptchaSolver')


class CaptchaSolver:
    """CAPTCHA solving service integration"""
    
    def __init__(self):
        """Initialize the CAPTCHA solver with 2Captcha API"""
        self.api_key = os.getenv('TWOCAPTCHA_API_KEY')
        self.base_url = "http://2captcha.com"
        self.timeout = 180  # 3 minutes timeout
        self.polling_interval = 5  # Check every 5 seconds
        
        if not self.api_key:
            logger.warning("2Captcha API key not configured")
    
    def is_configured(self) -> bool:
        """Check if CAPTCHA solver is properly configured"""
        return bool(self.api_key)
    
    def solve_recaptcha(self, driver: webdriver.Chrome, site_key: Optional[str] = None) -> Optional[str]:
        """
        Solve reCAPTCHA v2
        
        Args:
            driver: Selenium WebDriver instance
            site_key: reCAPTCHA site key (will auto-detect if not provided)
            
        Returns:
            CAPTCHA solution token or None if failed
        """
        if not self.is_configured():
            logger.error("2Captcha not configured")
            return None
        
        try:
            # Get current page URL
            page_url = driver.current_url
            logger.info(f"Solving reCAPTCHA for: {page_url}")
            
            # Auto-detect site key if not provided
            if not site_key:
                site_key = self._find_recaptcha_site_key(driver)
                if not site_key:
                    logger.error("Could not find reCAPTCHA site key")
                    return None
            
            logger.debug(f"Site key: {site_key}")
            
            # Submit CAPTCHA for solving
            captcha_id = self._submit_recaptcha(site_key, page_url)
            if not captcha_id:
                return None
            
            # Poll for solution
            solution = self._poll_for_solution(captcha_id)
            if solution:
                logger.info("✅ CAPTCHA solved successfully")
                # Inject the solution into the page
                self._inject_recaptcha_solution(driver, solution)
            
            return solution
            
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {e}")
            return None
    
    def solve_image_captcha(self, image_path: str) -> Optional[str]:
        """
        Solve image-based CAPTCHA
        
        Args:
            image_path: Path to the CAPTCHA image
            
        Returns:
            CAPTCHA solution text or None if failed
        """
        if not self.is_configured():
            logger.error("2Captcha not configured")
            return None
        
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Submit to 2Captcha
            response = requests.post(
                f"{self.base_url}/in.php",
                data={
                    'key': self.api_key,
                    'method': 'base64',
                    'json': 1
                },
                files={'file': ('captcha.png', image_data)},
                timeout=30
            )
            
            result = response.json()
            if result.get('status') != 1:
                logger.error(f"Failed to submit image CAPTCHA: {result.get('error_text')}")
                return None
            
            captcha_id = result.get('request')
            
            # Poll for solution
            solution = self._poll_for_solution(captcha_id)
            if solution:
                logger.info(f"✅ Image CAPTCHA solved: {solution}")
            
            return solution
            
        except Exception as e:
            logger.error(f"Error solving image CAPTCHA: {e}")
            return None
    
    def _find_recaptcha_site_key(self, driver: webdriver.Chrome) -> Optional[str]:
        """Auto-detect reCAPTCHA site key from the page"""
        try:
            # Method 1: Check for data-sitekey attribute
            elements = driver.find_elements(By.CSS_SELECTOR, "[data-sitekey]")
            if elements:
                site_key = elements[0].get_attribute("data-sitekey")
                if site_key:
                    return site_key
            
            # Method 2: Check iframe src
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            for iframe in iframes:
                src = iframe.get_attribute("src")
                if "k=" in src:
                    # Extract site key from URL
                    import re
                    match = re.search(r'k=([^&]+)', src)
                    if match:
                        return match.group(1)
            
            # Method 3: Check in JavaScript
            site_key = driver.execute_script("""
                // Check for grecaptcha object
                if (typeof grecaptcha !== 'undefined') {
                    const widgets = grecaptcha.enterprise ? 
                        grecaptcha.enterprise.getResponse() : 
                        grecaptcha.getResponse();
                    if (widgets) return widgets;
                }
                
                // Check page source for site key patterns
                const pageSource = document.documentElement.innerHTML;
                const match = pageSource.match(/data-sitekey=["']([^"']+)["']/);
                if (match) return match[1];
                
                return null;
            """)
            
            if site_key:
                return site_key
            
            logger.warning("Could not auto-detect reCAPTCHA site key")
            return None
            
        except Exception as e:
            logger.error(f"Error finding site key: {e}")
            return None
    
    def _submit_recaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Submit reCAPTCHA to 2Captcha service"""
        try:
            response = requests.post(
                f"{self.base_url}/in.php",
                data={
                    'key': self.api_key,
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': page_url,
                    'json': 1
                },
                timeout=30
            )
            
            result = response.json()
            if result.get('status') == 1:
                captcha_id = result.get('request')
                logger.info(f"CAPTCHA submitted, ID: {captcha_id}")
                return captcha_id
            else:
                logger.error(f"Failed to submit CAPTCHA: {result.get('error_text')}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting CAPTCHA: {e}")
            return None
    
    def _poll_for_solution(self, captcha_id: str) -> Optional[str]:
        """Poll 2Captcha for the solution"""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                # Wait before checking
                time.sleep(self.polling_interval)
                
                # Check result
                response = requests.get(
                    f"{self.base_url}/res.php",
                    params={
                        'key': self.api_key,
                        'action': 'get',
                        'id': captcha_id,
                        'json': 1
                    },
                    timeout=30
                )
                
                result = response.json()
                
                if result.get('status') == 1:
                    # Solution ready
                    return result.get('request')
                elif result.get('request') == 'CAPCHA_NOT_READY':
                    # Still processing
                    logger.debug(f"CAPTCHA still processing... ({int(time.time() - start_time)}s)")
                    continue
                else:
                    # Error occurred
                    logger.error(f"CAPTCHA solving error: {result.get('error_text')}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error polling for solution: {e}")
                continue
        
        logger.error("CAPTCHA solving timeout")
        return None
    
    def _inject_recaptcha_solution(self, driver: webdriver.Chrome, solution: str):
        """Inject the reCAPTCHA solution into the page"""
        try:
            # Find the response textarea
            script = f"""
            // Method 1: Direct textarea injection
            const textarea = document.getElementById('g-recaptcha-response');
            if (textarea) {{
                textarea.style.display = 'block';
                textarea.value = '{solution}';
                textarea.style.display = 'none';
            }}
            
            // Method 2: Using grecaptcha callback
            if (typeof grecaptcha !== 'undefined') {{
                // Find all reCAPTCHA widgets
                const clients = grecaptcha.enterprise ? 
                    grecaptcha.enterprise.getAllClients() : 
                    [0];  // Default to first widget
                
                clients.forEach(clientId => {{
                    try {{
                        // Find callback function
                        const callback = window.___grecaptcha_cfg.clients[clientId].callback;
                        if (callback) {{
                            window[callback]('{solution}');
                        }}
                    }} catch (e) {{
                        console.log('Could not execute callback:', e);
                    }}
                }});
            }}
            
            // Method 3: Submit form if exists
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {{
                if (form.querySelector('#g-recaptcha-response')) {{
                    // Check if there's a submit button
                    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                    if (submitBtn) {{
                        submitBtn.click();
                    }} else {{
                        form.submit();
                    }}
                }}
            }});
            """
            
            driver.execute_script(script)
            logger.debug("reCAPTCHA solution injected")
            
        except Exception as e:
            logger.error(f"Error injecting solution: {e}")
    
    def report_incorrect(self, captcha_id: str):
        """Report incorrect CAPTCHA solution for refund"""
        if not self.is_configured():
            return
        
        try:
            response = requests.post(
                f"{self.base_url}/res.php",
                data={
                    'key': self.api_key,
                    'action': 'reportbad',
                    'id': captcha_id
                },
                timeout=30
            )
            
            if response.text == 'OK':
                logger.info("Incorrect CAPTCHA reported successfully")
            else:
                logger.warning(f"Failed to report incorrect CAPTCHA: {response.text}")
                
        except Exception as e:
            logger.error(f"Error reporting incorrect CAPTCHA: {e}")
    
    def get_balance(self) -> Optional[float]:
        """Get 2Captcha account balance"""
        if not self.is_configured():
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/res.php",
                params={
                    'key': self.api_key,
                    'action': 'getbalance',
                    'json': 1
                },
                timeout=30
            )
            
            result = response.json()
            if result.get('status') == 1:
                balance = float(result.get('request', 0))
                logger.info(f"2Captcha balance: ${balance:.2f}")
                return balance
            else:
                logger.error(f"Failed to get balance: {result.get('error_text')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Test the CAPTCHA solver
    logging.basicConfig(level=logging.DEBUG)
    
    solver = CaptchaSolver()
    
    if solver.is_configured():
        # Check balance
        balance = solver.get_balance()
        if balance:
            print(f"✅ 2Captcha configured, balance: ${balance:.2f}")
    else:
        print("❌ 2Captcha not configured")
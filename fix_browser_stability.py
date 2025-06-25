#!/usr/bin/env python3
"""
Fix 2: Browser Stability - Prevent session closing errors
"""

from pathlib import Path

def fix_browser_stability():
    """Fix browser creation and stability issues"""
    
    print("🔧 Fixing browser stability...")
    
    file_path = Path("fansale_no_login.py")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Update create_browser to be more robust
    # Find and replace the driver creation section
    old_creation = """                    # Create driver
                    driver = uc.Chrome(options=options, version_main=version_main, driver_executable_path=None)
                    
                    # Give browser time to stabilize
                    time.sleep(2)
                    
                    # Set timeouts
                    driver.set_page_load_timeout(30)
                    driver.implicitly_wait(10)
                    
                    # Test if driver works by navigating to a simple page first
                    try:
                        driver.get("data:text/html,<h1>Test</h1>")
                        time.sleep(1)
                        driver.execute_script("return navigator.userAgent")
                    except Exception as e:
                        logger.warning(f"Browser test failed: {e}")
                        raise"""
    
    new_creation = """                    # Create driver with enhanced stability
                    driver = uc.Chrome(
                        options=options, 
                        version_main=version_main,
                        driver_executable_path=None,
                        use_subprocess=False,  # More stable
                        headless=False
                    )
                    
                    # Essential: Wait for browser to fully initialize
                    time.sleep(3)
                    
                    # Set reasonable timeouts
                    driver.set_page_load_timeout(30)
                    driver.implicitly_wait(5)
                    
                    # Health check with retry
                    for attempt in range(3):
                        try:
                            # Test basic functionality
                            driver.get("data:text/html,<h1>Browser Test</h1>")
                            time.sleep(1)
                            
                            # Verify JavaScript execution
                            result = driver.execute_script("return window.navigator.userAgent")
                            if result:
                                logger.debug(f"Browser {browser_id} health check passed")
                                break
                        except Exception as e:
                            if attempt == 2:
                                logger.warning(f"Browser health check failed: {e}")
                                raise
                            time.sleep(2)"""
    
    content = content.replace(old_creation, new_creation)
    
    # Fix 2: Add browser keep-alive mechanism
    keep_alive_method = '''
    def _keep_browser_alive(self, driver: uc.Chrome, browser_id: int):
        """Keep browser session alive with periodic checks"""
        try:
            # Execute a simple JavaScript to keep session active
            driver.execute_script("return document.readyState")
            return True
        except Exception as e:
            logger.warning(f"Browser {browser_id} session check failed: {e}")
            return False
'''
    
    # Insert after _load_saved_config method
    insert_marker = "logger.info(f\"✅ Loaded saved configuration\")"
    insert_pos = content.find(insert_marker)
    if insert_pos > 0:
        # Find the end of the method
        method_end = content.find('\n\n', insert_pos)
        if method_end > 0:
            content = content[:method_end] + keep_alive_method + content[method_end:]
    
    # Fix 3: Update hunt_tickets to handle session errors better
    old_navigation = """        # Navigate to event page with error handling
        logger.info(f"📍 Navigating to: {self.target_url}")
        try:
            driver.get(self.target_url)
            time.sleep(random.uniform(3.5, 5.0))  # Give more time for initial load
            
            # Verify we're on the right page
            if "fansale" not in driver.current_url.lower():
                logger.warning(f"Unexpected URL: {driver.current_url}")
                time.sleep(2)
                driver.get(self.target_url)
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            # Try one more time
            time.sleep(2)
            driver.get(self.target_url)"""
    
    new_navigation = """        # Navigate to event page with enhanced error handling
        logger.info(f"📍 Navigating to: {self.target_url}")
        
        # Retry navigation up to 3 times
        for nav_attempt in range(3):
            try:
                # Check if browser is still alive
                if not self._keep_browser_alive(driver, browser_id):
                    logger.error(f"Browser {browser_id} session dead")
                    return
                
                driver.get(self.target_url)
                time.sleep(random.uniform(4.0, 5.0))  # Adequate time for load
                
                # Verify successful navigation
                if "fansale" in driver.current_url.lower():
                    logger.info(f"✅ Browser {browser_id} successfully navigated")
                    break
                else:
                    logger.warning(f"Unexpected URL: {driver.current_url}")
                    if nav_attempt < 2:
                        time.sleep(3)
                        continue
            except Exception as e:
                logger.error(f"Navigation attempt {nav_attempt + 1} failed: {e}")
                if nav_attempt == 2:
                    logger.error(f"Browser {browser_id} failed to navigate after 3 attempts")
                    return
                time.sleep(3)"""
    
    content = content.replace(old_navigation, new_navigation)
    
    # Fix 4: Add session validation in the main hunting loop
    old_loop_check = """                # Check for 404 blocks
                if self.is_blocked(driver):"""
    
    new_loop_check = """                # Validate session is still alive
                if check_count % 10 == 0:  # Check every 10 iterations
                    if not self._keep_browser_alive(driver, browser_id):
                        logger.error(f"Browser {browser_id} session lost, exiting hunter")
                        break
                
                # Check for 404 blocks
                if self.is_blocked(driver):"""
    
    content = content.replace(old_loop_check, new_loop_check)
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Browser stability fixed!")
    print("\nChanges made:")
    print("1. ✅ Added 3-second initialization delay")
    print("2. ✅ Implemented health checks with retry")
    print("3. ✅ Added keep-alive mechanism")
    print("4. ✅ Enhanced navigation error handling")
    print("5. ✅ Added periodic session validation")

if __name__ == "__main__":
    fix_browser_stability()

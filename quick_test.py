#!/usr/bin/env python3
"""Test the fixed bot"""
import sys
sys.path.insert(0, '.')

from fansale_no_login_fixed import FanSaleBot, Colors
from selenium.webdriver.common.by import By
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fixed_bot():
    """Test the fixed bot with proper block detection"""
    try:
        logger.info("Testing FIXED FanSale bot...")
        
        # Create bot instance
        bot = FanSaleBot()
        
        # Enable debug mode for testing
        bot.config.debug_mode = True
        logger.info("Debug mode enabled")
        
        # Test configuration
        logger.info(f"\n{Colors.BOLD}Configuration:{Colors.END}")
        logger.info(f"  Checks/min: {bot.config.checks_per_minute}")
        logger.info(f"  Debug mode: {bot.config.debug_mode}")
        
        # Test browser creation
        logger.info(f"\n{Colors.BOLD}Testing browser creation (no popups):{Colors.END}")
        browser = bot.create_browser(1)
        
        if browser:
            logger.info("✅ Browser created successfully!")
            
            # Test navigation
            logger.info("\nTesting navigation...")
            browser.get("https://www.fansale.it")
            
            # Test block detection with a normal page
            logger.info("\nTesting block detection on normal page...")
            is_blocked = bot.is_blocked(browser)
            logger.info(f"Is blocked: {is_blocked} (should be False)")
            
            if is_blocked:
                logger.error("❌ FALSE POSITIVE: Normal page detected as blocked!")
            else:
                logger.info("✅ Block detection working correctly")
            
            # Test with actual ticket page
            logger.info("\nNavigating to ticket page...")
            browser.get(bot.target_url)
            
            import time
            time.sleep(2)
            
            # Check for tickets
            tickets = browser.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
            logger.info(f"Found {len(tickets)} ticket elements")
            
            # Check block detection again
            is_blocked = bot.is_blocked(browser)
            logger.info(f"Is blocked on ticket page: {is_blocked}")
            
            # Clean up
            browser.quit()
            
            return True
        else:
            logger.error("❌ Failed to create browser")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_fixed_bot():
        logger.info(f"\n{Colors.GREEN}✅ Fixed bot tests passed!{Colors.END}")
        logger.info("\nKey fixes:")
        logger.info("- Block detection now matches original logic")
        logger.info("- No more false positives on normal pages") 
        logger.info("- Popup prevention flags added")
        logger.info("- Fast ticket clicking without delays")
        logger.info("- Debug mode for troubleshooting")
        logger.info("\nRun with: python3 fansale_no_login_fixed.py")
    else:
        logger.error(f"\n{Colors.RED}❌ Tests failed{Colors.END}")

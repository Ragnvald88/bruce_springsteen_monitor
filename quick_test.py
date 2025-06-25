#!/usr/bin/env python3
"""Test the improved bot"""
import sys
sys.path.insert(0, '.')

from fansale_no_login_improved import FanSaleBot, Colors
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def test_improved_bot():
    """Test the improved bot configuration and features"""
    try:
        logger.info("Testing improved FanSale bot...")
        
        # Create bot instance
        bot = FanSaleBot()
        
        # Test configuration
        logger.info(f"\n{Colors.BOLD}Configuration Test:{Colors.END}")
        logger.info(f"  Checks/min: {bot.config.checks_per_minute}")
        logger.info(f"  Min wait: {bot.config.min_wait}s")
        logger.info(f"  Max wait: {bot.config.max_wait}s")
        logger.info(f"  Status interval: {bot.config.status_update_interval}")
        
        # Test wait time calculation
        wait_time = bot.config.calculate_wait_time()
        logger.info(f"  Calculated wait: {wait_time:.2f}s")
        
        # Test browser creation
        logger.info(f"\n{Colors.BOLD}Browser Creation Test:{Colors.END}")
        browser = bot.create_browser(1)
        
        if browser:
            logger.info("✅ Browser created successfully!")
            
            # Test navigation
            browser.get("https://www.fansale.it")
            logger.info("✅ Navigation successful!")
            
            # Clean up
            browser.quit()
            
            # Show statistics
            logger.info(f"\n{Colors.BOLD}Statistics Test:{Colors.END}")
            bot.show_statistics_dashboard()
            
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
    if test_improved_bot():
        logger.info(f"\n{Colors.GREEN}✅ All tests passed!{Colors.END}")
        logger.info("The improved bot is ready to use!")
        logger.info("\nKey improvements:")
        logger.info("- Configurable check frequency (60-600 checks/min)")
        logger.info("- Better logging with adjustable verbosity")
        logger.info("- Enhanced menu system with more options")
        logger.info("- Performance presets for different risk levels")
        logger.info("- Health monitoring and error tracking")
    else:
        logger.error(f"\n{Colors.RED}❌ Tests failed{Colors.END}")

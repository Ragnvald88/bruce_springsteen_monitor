"""
Selective Resource Blocking for Data Optimization
Only blocks truly unnecessary resources to avoid detection
"""

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from ..utils.logging import get_logger

logger = get_logger(__name__)


def apply_selective_blocking(driver):
    """Apply selective resource blocking to Chrome driver"""
    try:
        # Only block images and obvious tracking/ads
        driver.execute_cdp_cmd('Network.setBlockedURLs', {
            'urls': [
                '*://*.doubleclick.net/*',
                '*://googleads.g.doubleclick.net/*',
                '*://*.googlesyndication.com/*',
                '*://*.google-analytics.com/*',
                '*://*.googletagmanager.com/*',
                '*://*.facebook.com/tr/*',
                '*://*.amazon-adsystem.com/*',
                '*://*.adsrvr.org/*',
                '*.jpg',
                '*.jpeg',
                '*.png',
                '*.gif',
                '*.webp',
                '*.ico',
                '*.woff',
                '*.woff2',
                '*.ttf'
            ]
        })
        
        # Enable network domain
        driver.execute_cdp_cmd('Network.enable', {})
        
        # Set cache behavior to use cache when possible
        driver.execute_cdp_cmd('Network.setCacheDisabled', {'cacheDisabled': False})
        
        logger.info("Applied selective resource blocking (images + ads only)")
        
    except Exception as e:
        logger.warning(f"Could not apply resource blocking: {e}")
        # Non-critical, continue anyway

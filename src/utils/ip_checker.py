"""IP Address checker utility for verifying proxy usage"""

import asyncio
from typing import Dict, Any, Optional
from ..utils.logging import get_logger

logger = get_logger(__name__)


async def check_ip_address(page: Any) -> Dict[str, Any]:
    """
    Check the current IP address using the page
    
    Args:
        page: Browser page (Playwright or Selenium)
        
    Returns:
        Dict with IP info
    """
    try:
        # Navigate to IP check service
        if hasattr(page, "goto"):
            # Playwright
            await page.goto("https://httpbin.org/ip", wait_until="domcontentloaded", timeout=10000)
            content = await page.evaluate("() => document.body.textContent")
        else:
            # Selenium
            page.get("https://httpbin.org/ip")
            await asyncio.sleep(1)
            content = page.execute_script("return document.body.textContent")
        
        # Parse IP info
        import json
        ip_data = json.loads(content)
        
        logger.info(f"🌍 Current IP: {ip_data.get('origin', 'Unknown')}")
        
        return {
            "success": True,
            "ip": ip_data.get("origin", "Unknown"),
            "raw": ip_data
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to check IP: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def verify_proxy_working(page: Any, expected_proxy: Optional[str] = None) -> bool:
    """
    Verify that proxy is working by checking IP
    
    Args:
        page: Browser page
        expected_proxy: Expected proxy host (optional)
        
    Returns:
        True if proxy appears to be working
    """
    result = await check_ip_address(page)
    
    if not result["success"]:
        return False
    
    current_ip = result.get("ip", "")
    
    # Log the IP
    logger.info(f"🔍 Verifying proxy - Current IP: {current_ip}")
    
    # If we have expected proxy, we could do more validation
    # For now, just check that we got an IP
    return bool(current_ip)
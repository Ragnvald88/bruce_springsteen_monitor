#!/usr/bin/env python3
"""Test proxy connectivity and functionality"""

import os
import sys
import asyncio
import httpx
import yaml
from pathlib import Path
from typing import Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.proxy_manager import StealthProxyManager
from src.utils.enhanced_logger import EnhancedLogger

logger = EnhancedLogger.get_logger(__name__)


async def test_proxy_connectivity():
    """Test proxy connectivity and basic functionality"""
    
    # Load config
    config_path = Path(__file__).parent / "config" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    logger.info("🔍 Testing Proxy Configuration")
    logger.info("=" * 60)
    
    # Check if proxy is enabled
    if not config.get("proxy_settings", {}).get("enabled", False):
        logger.error("❌ Proxy is disabled in config!")
        return False
    
    # Initialize proxy manager
    proxy_manager = StealthProxyManager(config)
    
    # Test 1: Basic connectivity
    logger.info("\n📡 Test 1: Basic Proxy Connectivity")
    proxy = proxy_manager.get_proxy()
    
    if not proxy:
        logger.error("❌ No proxy available!")
        return False
    
    logger.info(f"Using proxy: {proxy['host']}:{proxy['port']}")
    
    try:
        # Test proxy connection
        proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        
        async with httpx.AsyncClient(proxies=proxy_url, timeout=30.0) as client:
            # Check IP
            response = await client.get("https://httpbin.org/ip")
            data = response.json()
            logger.info(f"✅ Proxy IP: {data['origin']}")
            
            # Check headers
            response = await client.get("https://httpbin.org/headers")
            headers = response.json()["headers"]
            logger.info(f"✅ User-Agent: {headers.get('User-Agent', 'Not set')}")
            
    except Exception as e:
        logger.error(f"❌ Proxy connection failed: {e}")
        return False
    
    # Test 2: Platform accessibility
    logger.info("\n🌐 Test 2: Platform Accessibility via Proxy")
    
    platforms = {
        "Fansale": "https://www.fansale.it",
        "Ticketmaster IT": "https://www.ticketmaster.it",
        "Vivaticket": "https://www.vivaticket.com"
    }
    
    for platform, url in platforms.items():
        try:
            async with httpx.AsyncClient(proxies=proxy_url, timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    logger.info(f"✅ {platform}: Accessible (Status: {response.status_code})")
                else:
                    logger.warning(f"⚠️  {platform}: Status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ {platform}: Failed - {str(e)[:100]}")
    
    # Test 3: Proxy rotation
    logger.info("\n🔄 Test 3: Proxy Rotation")
    
    # Get platform-specific proxy
    fansale_proxy = proxy_manager.get_proxy_for_platform("fansale")
    if fansale_proxy:
        logger.info(f"✅ Fansale proxy: {fansale_proxy['host']} (Country: {fansale_proxy.get('country', 'Unknown')})")
    
    # Test rotation
    proxy_manager.mark_proxy_failed(proxy["host"], proxy["port"])
    new_proxy = proxy_manager.get_proxy()
    
    if new_proxy and (new_proxy["host"] != proxy["host"] or new_proxy["port"] != proxy["port"]):
        logger.info("✅ Proxy rotation working")
    else:
        logger.warning("⚠️  Proxy rotation may not be working properly")
    
    # Test 4: Proxy performance
    logger.info("\n⚡ Test 4: Proxy Performance")
    
    start = asyncio.get_event_loop().time()
    try:
        async with httpx.AsyncClient(proxies=proxy_url, timeout=30.0) as client:
            await client.get("https://www.google.com")
        latency = (asyncio.get_event_loop().time() - start) * 1000
        logger.info(f"✅ Proxy latency: {latency:.0f}ms")
        
        if latency < 500:
            logger.info("✅ Excellent proxy performance!")
        elif latency < 1000:
            logger.info("✅ Good proxy performance")
        else:
            logger.warning("⚠️  Proxy is slow, consider alternatives")
            
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Proxy testing completed successfully!")
    return True


async def main():
    """Main test runner"""
    try:
        success = await test_proxy_connectivity()
        if not success:
            logger.error("\n❌ Proxy tests failed! Check your configuration.")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n👋 Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
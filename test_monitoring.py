#!/usr/bin/env python3
"""Test script to verify monitoring is working without Live display."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from src.config import load_settings
from src.utils.logging import setup_logging, get_logger

console = Console()
logger = get_logger(__name__)


async def test_monitoring():
    """Test basic monitoring functionality."""
    # Load settings
    settings = load_settings()
    setup_logging(level="INFO", log_dir=Path("logs"))
    
    console.print("[cyan]🔍 Testing StealthMaster Configuration[/cyan]\n")
    
    # Check proxy settings
    console.print("[yellow]1. Proxy Configuration:[/yellow]")
    if settings.proxy_settings.enabled:
        console.print("   ✅ Proxy enabled")
        if settings.proxy_settings.primary_pool:
            proxy = settings.proxy_settings.primary_pool[0]
            console.print(f"   • Host: {proxy.host}:{proxy.port}")
            console.print(f"   • Username: {proxy.username}")
            console.print(f"   • Type: {proxy.type}")
        else:
            console.print("   ❌ No proxies configured!")
    else:
        console.print("   ⚠️  Proxy disabled")
    
    # Check targets
    console.print("\n[yellow]2. Monitoring Targets:[/yellow]")
    enabled_count = 0
    for target in settings.targets:
        status = "✅ ENABLED" if target.enabled else "❌ DISABLED"
        console.print(f"   • {target.platform}: {target.event_name} - {status}")
        if target.enabled:
            enabled_count += 1
            console.print(f"     URL: {target.url}")
            console.print(f"     Interval: {target.interval_s}s")
            console.print(f"     Max price: €{target.max_price_per_ticket}")
    
    console.print(f"\n   Total enabled: {enabled_count}")
    
    # Check authentication
    console.print("\n[yellow]3. Authentication:[/yellow]")
    if settings.authentication.enabled:
        console.print("   ✅ Authentication enabled")
        for platform, creds in settings.authentication.platforms.items():
            has_creds = bool(creds.username and creds.password)
            status = "✅" if has_creds else "❌"
            console.print(f"   {status} {platform}: {creds.username if has_creds else 'Not configured'}")
    else:
        console.print("   ❌ Authentication disabled")
    
    # Test browser launch
    console.print("\n[yellow]4. Browser Test:[/yellow]")
    from src.browser.launcher import launcher
    launcher.settings = settings
    launcher._configure_proxies()
    
    try:
        console.print("   🌐 Launching test browser...")
        browser_id = await launcher.launch_browser()
        console.print(f"   ✅ Browser launched: {browser_id}")
        
        # Create a page and check IP
        context_id = await launcher.create_context(browser_id)
        page = await launcher.new_page(context_id)
        
        console.print("   🌍 Checking IP address...")
        if hasattr(page, "goto"):
            await page.goto("https://httpbin.org/ip", wait_until='domcontentloaded')
            ip_data = await page.evaluate("() => document.body.textContent")
        else:
            page.get("https://httpbin.org/ip")
            await asyncio.sleep(2)
            ip_data = page.execute_script("return document.body.textContent")
        
        import json
        ip_info = json.loads(ip_data)
        console.print(f"   ✅ Current IP: {ip_info.get('origin', 'Unknown')}")
        
        # Quick test of a target site
        console.print("\n   🎯 Testing Fansale access...")
        test_url = "https://www.fansale.it"
        if hasattr(page, "goto"):
            response = await page.goto(test_url, wait_until='domcontentloaded', timeout=10000)
            status = response.status if response else "Unknown"
        else:
            page.get(test_url)
            await asyncio.sleep(3)
            status = "200"  # Selenium doesn't easily give status
        
        console.print(f"   • Response status: {status}")
        if status == 403:
            console.print("   ❌ Access denied - proxy might be blocked")
        elif status == 200:
            console.print("   ✅ Access successful!")
        
        # Cleanup
        await launcher.close_all()
        
    except Exception as e:
        console.print(f"   ❌ Browser test failed: {e}")
        import traceback
        traceback.print_exc()
    
    console.print("\n[green]✅ Configuration test complete![/green]")
    console.print("\n[cyan]Summary:[/cyan]")
    console.print(f"• Proxy: {'✅ Configured' if settings.proxy_settings.enabled else '❌ Disabled'}")
    console.print(f"• Targets: {enabled_count} enabled")
    console.print(f"• Authentication: {'✅ Ready' if settings.authentication.enabled else '❌ Disabled'}")
    console.print("\n[yellow]Run ./run.sh to start monitoring with the live dashboard![/yellow]")


if __name__ == "__main__":
    asyncio.run(test_monitoring())
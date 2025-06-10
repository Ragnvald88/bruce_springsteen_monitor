#!/usr/bin/env python3
"""Run StealthMaster with visible browser windows for testing."""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import load_settings
from browser.pool import EnhancedBrowserPool
from profiles.manager import ProfileManager
from utils.logging import setup_logging

console = Console()


async def run_browser_test():
    """Run StealthMaster with browser windows visible."""
    
    console.print("[bold cyan]🚀 Starting StealthMaster with Browser GUI[/bold cyan]\n")
    
    # Load settings
    settings = load_settings(Path("config.yaml"))
    
    # Force non-headless mode
    settings.browser_options.headless = False
    
    # Setup logging
    setup_logging(
        level="INFO",
        log_dir=settings.logs_dir,
        settings=settings.logging
    )
    
    # Initialize components
    console.print("[yellow]Initializing components...[/yellow]")
    
    profile_manager = ProfileManager(settings)
    await profile_manager.load_all_profiles()
    console.print("[green]✓ Profiles loaded[/green]")
    
    # Initialize browser pool
    # Get settings from current mode config
    mode = settings.app_settings.mode
    mode_config = settings.app_settings.mode_configs.get(mode)
    
    browser_pool = EnhancedBrowserPool(
        max_browsers=mode_config.max_concurrent_monitors if mode_config else 2,
        max_contexts_per_browser=2,  # Default value
        headless=False,  # Force visible browsers
        data_limit_mb=settings.data_limits.global_limit_mb
    )
    
    console.print("[yellow]Starting browser pool...[/yellow]")
    await browser_pool.initialize()
    console.print("[green]✓ Browser pool ready[/green]")
    
    # Show what we're monitoring
    console.print("\n[bold]Active Targets:[/bold]")
    for target in settings.targets:
        if target.enabled:
            console.print(f"• {target.platform.value}: {target.event_name}")
    
    console.print("\n[bold cyan]Opening browser windows...[/bold cyan]")
    
    # Open browser for each target
    contexts = []
    for i, target in enumerate(settings.targets):
        if target.enabled:
            try:
                console.print(f"\n[yellow]Opening browser for {target.platform.value}...[/yellow]")
                
                # Acquire context
                context, page = await browser_pool.acquire_context(
                    platform=target.platform.value,
                    prefer_fresh=True
                )
                contexts.append((context, page, target))
                
                # Navigate to platform
                platform_urls = {
                    "ticketmaster": "https://www.ticketmaster.com",
                    "fansale": "https://www.fansale.de",
                    "vivaticket": "https://www.vivaticket.com"
                }
                
                url = platform_urls.get(target.platform.value, "https://google.com")
                console.print(f"[green]✓ Browser window {i+1} opened[/green]")
                console.print(f"  Navigating to: {url}")
                
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # Log some info about the page
                console.print(f"  Page title: {await page.title()}")
                
                # Check for detection
                page_content = await page.content()
                if any(word in page_content.lower() for word in ['captcha', 'robot', 'bot', 'automated']):
                    console.print(f"  [yellow]⚠️  Possible detection keywords found[/yellow]")
                else:
                    console.print(f"  [green]✓ No obvious detection[/green]")
                
            except Exception as e:
                console.print(f"[red]❌ Error opening browser: {e}[/red]")
    
    if contexts:
        console.print(f"\n[bold green]✅ Successfully opened {len(contexts)} browser window(s)![/bold green]")
        console.print("\n[bold]Browser windows are now open. You can:[/bold]")
        console.print("• Check if pages load normally")
        console.print("• Look for any captchas or bot detection")
        console.print("• Try navigating around the sites")
        console.print("• Monitor the console for any errors")
        
        console.print("\n[yellow]Press Ctrl+C to close all browsers and exit...[/yellow]")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
                # Could add monitoring logic here
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
    else:
        console.print("[red]❌ No browsers were opened. Check your configuration.[/red]")
    
    # Cleanup
    await browser_pool.shutdown()
    console.print("[green]✅ All browsers closed. Goodbye![/green]")


if __name__ == "__main__":
    try:
        asyncio.run(run_browser_test())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()
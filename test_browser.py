#!/usr/bin/env python3
"""Simple browser test to verify StealthMaster is working."""

import asyncio
from playwright.async_api import async_playwright
from rich.console import Console
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import load_settings, BrowserOptions
from browser.launcher import BrowserLauncher
from stealth.core import StealthCore
from utils.logging import setup_logging

console = Console()


async def test_browser():
    """Test browser with anti-detection."""
    
    console.print("[bold cyan]🚀 StealthMaster Browser Test[/bold cyan]\n")
    
    # Load settings
    settings = load_settings(Path("config.yaml"))
    
    # Setup logging
    setup_logging(level="INFO", log_dir=settings.logs_dir, settings=settings.logging)
    
    # Force non-headless
    browser_options = BrowserOptions(
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
        channel="chrome"
    )
    
    console.print("[yellow]Starting browser with stealth measures...[/yellow]")
    
    async with async_playwright() as playwright:
        # Initialize components
        launcher = BrowserLauncher(browser_options)
        stealth_core = StealthCore()
        
        # Launch browser
        browser = await launcher.launch(
            playwright=playwright,
            proxy=None,
            headless=False
        )
        
        console.print("[green]✓ Browser launched[/green]")
        
        # Create stealth context
        context = await stealth_core.create_stealth_context(
            browser=browser
        )
        
        console.print("[green]✓ Stealth measures applied[/green]")
        
        # Create page
        page = await context.new_page()
        
        # Test sites
        test_sites = [
            ("Bot Detection Test", "https://bot.sannysoft.com/"),
            ("Ticketmaster", "https://www.ticketmaster.com"),
            ("Google", "https://www.google.com")
        ]
        
        for name, url in test_sites:
            console.print(f"\n[yellow]Testing: {name}[/yellow]")
            console.print(f"URL: {url}")
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                console.print(f"[green]✓ Page loaded[/green]")
                
                # Check for common detection indicators
                content = await page.content()
                detection_keywords = ['captcha', 'robot', 'automated', 'denied', 'blocked']
                found_keywords = [kw for kw in detection_keywords if kw in content.lower()]
                
                if found_keywords:
                    console.print(f"[yellow]⚠️  Possible detection keywords found: {found_keywords}[/yellow]")
                else:
                    console.print(f"[green]✓ No obvious detection[/green]")
                
                # Give time to review
                console.print("Check the browser window...")
                await asyncio.sleep(5)
                
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
        
        console.print("\n[bold]Browser is open. Press Ctrl+C to close and exit.[/bold]")
        
        try:
            # Keep browser open
            await asyncio.sleep(300)
        except KeyboardInterrupt:
            pass
        
        await browser.close()
        console.print("\n[green]✅ Test completed![/green]")


if __name__ == "__main__":
    try:
        asyncio.run(test_browser())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
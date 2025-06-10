#!/usr/bin/env python3
"""Test script to verify anti-detection measures are working."""

import asyncio
import sys
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table

from browser.launcher import BrowserLauncher
from stealth.core import StealthCore
from config import BrowserOptions

console = Console()


async def test_detection_sites():
    """Test browser against common detection sites."""
    
    detection_sites = [
        {
            "name": "Bot Detection Test",
            "url": "https://bot.sannysoft.com/",
            "description": "Comprehensive bot detection test"
        },
        {
            "name": "Browser Leaks",
            "url": "https://browserleaks.com/javascript",
            "description": "JavaScript environment detection"
        },
        {
            "name": "Pixelscan",
            "url": "https://pixelscan.net/",
            "description": "Advanced fingerprinting detection"
        },
        {
            "name": "CreepJS",
            "url": "https://abrahamjuliot.github.io/creepjs/",
            "description": "Deep fingerprinting analysis"
        },
        {
            "name": "FingerprintJS Demo",
            "url": "https://fingerprintjs.github.io/fingerprintjs/",
            "description": "Browser fingerprinting demo"
        }
    ]
    
    console.print("[bold cyan]🔍 StealthMaster Detection Test Suite[/bold cyan]\n")
    console.print("This will test your browser against common bot detection sites.")
    console.print("Each site will open in a new browser window.\n")
    
    # Browser options
    options = BrowserOptions(
        headless=False,  # Always show GUI for testing
        viewport_width=1920,
        viewport_height=1080,
        user_agent=None  # Will be generated
    )
    
    # Initialize components
    launcher = BrowserLauncher()
    stealth_core = StealthCore()
    
    async with async_playwright() as playwright:
        # Launch browser with stealth
        browser = await launcher.launch(
            playwright=playwright,
            browser_type="chromium",
            options=options,
            proxy_config=None
        )
        
        results = []
        
        for site in detection_sites:
            console.print(f"\n[yellow]Testing: {site['name']}[/yellow]")
            console.print(f"URL: {site['url']}")
            console.print(f"Description: {site['description']}")
            
            try:
                # Create stealth context
                context = await stealth_core.create_stealth_context(
                    browser=browser,
                    options=options
                )
                
                page = await context.new_page()
                
                console.print("[green]✓ Stealth measures applied[/green]")
                console.print("Opening site... Check the browser window for results.")
                
                # Navigate to detection site
                await page.goto(site['url'], wait_until='domcontentloaded', timeout=30000)
                
                # Give user time to review
                console.print("\n[bold]Press Enter to continue to next test...[/bold]")
                input()
                
                results.append({
                    "site": site['name'],
                    "status": "✅ Tested",
                    "notes": "Review in browser"
                })
                
                await page.close()
                await context.close()
                
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
                results.append({
                    "site": site['name'],
                    "status": "❌ Failed",
                    "notes": str(e)
                })
        
        await browser.close()
        
        # Show results summary
        console.print("\n[bold cyan]📊 Test Results Summary[/bold cyan]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Site", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Notes", style="yellow")
        
        for result in results:
            table.add_row(result["site"], result["status"], result["notes"])
        
        console.print(table)
        
        console.print("\n[bold]💡 What to look for:[/bold]")
        console.print("• [green]✅ PASSED[/green] - No bot detection warnings")
        console.print("• [yellow]⚠️  WARNING[/yellow] - Some suspicious characteristics detected")
        console.print("• [red]❌ FAILED[/red] - Detected as automated/bot")
        console.print("\nCheck each site's results in the browser window for detailed analysis.")


async def test_specific_platform(platform: str = "ticketmaster"):
    """Test against a specific ticketing platform."""
    
    platforms = {
        "ticketmaster": "https://www.ticketmaster.com",
        "fansale": "https://www.fansale.de",
        "vivaticket": "https://www.vivaticket.com"
    }
    
    if platform not in platforms:
        console.print(f"[red]Unknown platform: {platform}[/red]")
        return
    
    url = platforms[platform]
    console.print(f"\n[bold cyan]🎫 Testing {platform.title()} Anti-Detection[/bold cyan]")
    console.print(f"URL: {url}\n")
    
    options = BrowserOptions(
        headless=False,
        viewport_width=1920,
        viewport_height=1080
    )
    
    launcher = BrowserLauncher()
    stealth_core = StealthCore()
    
    async with async_playwright() as playwright:
        browser = await launcher.launch(
            playwright=playwright,
            browser_type="chromium",
            options=options,
            proxy_config=None
        )
        
        context = await stealth_core.create_stealth_context(
            browser=browser,
            options=options
        )
        
        page = await context.new_page()
        
        console.print("[yellow]⏳ Loading platform...[/yellow]")
        await page.goto(url, wait_until='networkidle', timeout=60000)
        
        console.print("[green]✅ Page loaded successfully![/green]")
        console.print("\n[bold]Check the browser window and try:[/bold]")
        console.print("• Search for an event")
        console.print("• Navigate through pages")
        console.print("• Check if you encounter any captchas or blocks")
        console.print("\nPress Ctrl+C when done testing...")
        
        try:
            await asyncio.sleep(300)  # Keep browser open for 5 minutes
        except KeyboardInterrupt:
            pass
        
        await browser.close()
        console.print("\n[green]✅ Test completed![/green]")


if __name__ == "__main__":
    console.print("[bold]StealthMaster Detection Test Tool[/bold]\n")
    console.print("1. Test against bot detection sites")
    console.print("2. Test specific ticketing platform")
    console.print("3. Exit\n")
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_detection_sites())
    elif choice == "2":
        platform = input("Enter platform (ticketmaster/fansale/vivaticket): ").strip().lower()
        asyncio.run(test_specific_platform(platform))
    else:
        sys.exit(0)
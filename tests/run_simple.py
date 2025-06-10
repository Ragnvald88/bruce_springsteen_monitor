#!/usr/bin/env python3
"""Simple runner to show browser GUI working."""

import asyncio
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()


async def run_simple():
    """Run StealthMaster with browser windows visible - no proxy."""
    
    console.print("[bold cyan]🚀 StealthMaster Simple Browser Demo[/bold cyan]\n")
    
    async with async_playwright() as p:
        # Launch browser WITHOUT proxy for demo
        browser = await p.chromium.launch(
            headless=False,  # This makes browser visible
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )
        
        console.print("[green]✅ Browser window opened![/green]")
        
        # Create multiple tabs for different sites
        sites = [
            ("Ticketmaster", "https://www.ticketmaster.com"),
            ("Fansale", "https://www.fansale.de"),
            ("Example", "https://example.com")
        ]
        
        pages = []
        for name, url in sites:
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()
            pages.append((name, page))
            
            console.print(f"\n[yellow]Opening {name}...[/yellow]")
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                console.print(f"[green]✅ {name} loaded successfully![/green]")
                
                # Check page title
                title = await page.title()
                console.print(f"   Page title: {title}")
                
            except Exception as e:
                console.print(f"[red]❌ Error loading {name}: {e}[/red]")
        
        console.print("\n[bold cyan]Browser windows are now open![/bold cyan]")
        console.print("You should see 3 browser tabs/windows:")
        console.print("• Ticketmaster")
        console.print("• Fansale") 
        console.print("• Example")
        
        console.print("\n[yellow]Keeping browsers open for 60 seconds...[/yellow]")
        console.print("Press Ctrl+C to close earlier.")
        
        try:
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            pass
        
        await browser.close()
        console.print("\n[green]✅ Browsers closed![/green]")


if __name__ == "__main__":
    asyncio.run(run_simple())
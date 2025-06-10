#!/usr/bin/env python3
"""Quick browser test to show GUI is working."""

import asyncio
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()


async def quick_test():
    """Quick test to show browser GUI."""
    
    console.print("[bold cyan]🌐 StealthMaster Browser GUI Test[/bold cyan]\n")
    
    async with async_playwright() as p:
        # Launch browser with GUI
        browser = await p.chromium.launch(
            headless=False,  # This makes the browser visible
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )
        
        console.print("[green]✅ Browser window should be visible now![/green]")
        
        # Create a new page
        page = await browser.new_page()
        
        # Go to example site
        console.print("\n[yellow]Loading test page...[/yellow]")
        await page.goto("https://example.com")
        
        console.print("[green]✅ Page loaded![/green]")
        console.print("\n[bold]You should see:[/bold]")
        console.print("• A browser window with Example Domain page")
        console.print("• The browser is NOT in headless mode")
        console.print("• You can interact with it manually")
        
        console.print("\n[yellow]The browser will stay open for 30 seconds...[/yellow]")
        console.print("Press Ctrl+C to close earlier.")
        
        # Keep browser open
        try:
            await asyncio.sleep(30)
        except KeyboardInterrupt:
            pass
        
        await browser.close()
        console.print("\n[green]✅ Browser closed![/green]")


if __name__ == "__main__":
    asyncio.run(quick_test())
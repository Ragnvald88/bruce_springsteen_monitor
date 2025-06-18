#!/usr/bin/env python3
"""
StealthMaster Fixed - Minimal working version
No complexity, just functionality
"""

import time
import asyncio
from datetime import datetime
from pathlib import Path
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align

console = Console()


class WorkingStealthMaster:
    """A version that actually works"""
    
    def __init__(self):
        self.running = False
        self.start_time = datetime.now()
        self.drivers = {}
        self.status = {}
        self.stats = {
            'checks': 0,
            'tickets_found': 0,
            'blocks': 0,
            'errors': 0
        }
        
    def create_stealth_driver(self, proxy_config=None):
        """Create a Chrome driver with stealth settings"""
        options = Options()
        
        # Basic stealth
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Block images to save data
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Window size
        options.add_argument('--window-size=1920,1080')
        
        # User agent
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        
        # Proxy if provided
        if proxy_config:
            # For now, skip proxy to test basic functionality
            # proxy_string = f"{proxy_config['host']}:{proxy_config['port']}"
            # options.add_argument(f'--proxy-server={proxy_string}')
            pass
            
        try:
            # Auto-download correct chromedriver version
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Stealth JavaScript
            stealth_js = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: (params) => (
                        params.name === 'notifications' ?
                            Promise.resolve({ state: 'prompt' }) :
                            undefined
                    )
                })
            });
            """
            driver.execute_script(stealth_js)
            
            return driver
        except Exception as e:
            console.print(f"[red]Failed to create driver: {e}[/red]")
            return None
    
    def dismiss_cookies(self, driver):
        """Try to dismiss cookie banners"""
        cookie_selectors = [
            '#onetrust-accept-btn-handler',
            'button[id*="accept"]',
            'button[class*="accept"]',
            '.cookie-consent-accept',
            '[data-testid="cookie-accept"]',
            'button:contains("Accetta")',
            'button:contains("Accept")'
        ]
        
        for selector in cookie_selectors:
            try:
                # Try CSS selector
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        console.print(f"[green]✓ Clicked cookie button: {selector}[/green]")
                        time.sleep(1)
                        return True
            except:
                pass
        
        # Try XPath for text-based search
        try:
            accept_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]"
            )
            for button in accept_buttons:
                if button.is_displayed() and button.is_enabled():
                    driver.execute_script("arguments[0].click();", button)
                    console.print("[green]✓ Clicked cookie accept button (XPath)[/green]")
                    time.sleep(1)
                    return True
        except:
            pass
            
        return False
    
    def check_page(self, driver, url, name):
        """Check a page for tickets and blocks"""
        try:
            # Navigate
            driver.get(url)
            time.sleep(3)  # Let page load
            
            # Dismiss cookies on first load
            if f"{name}_cookies_dismissed" not in self.status:
                if self.dismiss_cookies(driver):
                    self.status[f"{name}_cookies_dismissed"] = True
                    time.sleep(2)  # Wait after dismissing
            
            # Get page content
            page_text = driver.page_source.lower()
            current_url = driver.current_url.lower()
            
            # Check if blocked
            block_indicators = [
                'access denied',
                'blocked',
                'forbidden', 
                'not authorized',
                'security check',
                'verificando il browser'  # Italian
            ]
            
            if any(indicator in page_text for indicator in block_indicators):
                self.stats['blocks'] += 1
                return {'status': 'blocked', 'has_tickets': False}
            
            # Check for login page redirect
            if 'login' in current_url or 'signin' in current_url:
                return {'status': 'need_login', 'has_tickets': False}
            
            # Look for ticket indicators
            ticket_indicators = [
                'biglietto disponibile',
                'ticket available',
                'acquista ora',
                'buy now',
                'aggiungi al carrello',
                'add to cart',
                'prezzo',
                'price'
            ]
            
            has_tickets = any(indicator in page_text for indicator in ticket_indicators)
            
            # Also check for "sold out" indicators
            sold_out_indicators = [
                'sold out',
                'esaurito',
                'non disponibile',
                'not available'
            ]
            
            is_sold_out = any(indicator in page_text for indicator in sold_out_indicators)
            
            if has_tickets and not is_sold_out:
                self.stats['tickets_found'] += 1
                return {'status': 'tickets_available', 'has_tickets': True}
            
            return {'status': 'no_tickets', 'has_tickets': False}
            
        except Exception as e:
            self.stats['errors'] += 1
            return {'status': 'error', 'has_tickets': False, 'error': str(e)}
    
    async def monitor_target(self, target):
        """Monitor a single target"""
        name = target['name']
        url = target['url']
        platform = target['platform']
        interval = target.get('interval', 30)
        
        # Create driver for this target
        console.print(f"[cyan]Creating driver for {name}...[/cyan]")
        driver = self.create_stealth_driver()
        
        if not driver:
            self.status[name] = "❌ Driver failed"
            return
            
        self.drivers[name] = driver
        console.print(f"[green]✓ Driver created for {name}[/green]")
        
        while self.running:
            try:
                self.status[name] = "🔄 Checking..."
                
                # Check the page
                result = self.check_page(driver, url, name)
                self.stats['checks'] += 1
                
                # Update status based on result
                if result['status'] == 'blocked':
                    self.status[name] = "🚫 BLOCKED"
                    console.print(f"[red]🚫 Blocked on {name}[/red]")
                    await asyncio.sleep(60)  # Wait longer if blocked
                    
                elif result['status'] == 'need_login':
                    self.status[name] = "🔐 Need login"
                    console.print(f"[yellow]🔐 Login required for {name}[/yellow]")
                    await asyncio.sleep(interval)
                    
                elif result['status'] == 'tickets_available':
                    self.status[name] = "🎫 TICKETS FOUND!"
                    console.print(f"[green bold]🎫 TICKETS AVAILABLE on {name}![/green bold]")
                    console.bell()  # System beep
                    await asyncio.sleep(5)  # Check more frequently when tickets found
                    
                elif result['status'] == 'error':
                    self.status[name] = f"⚠️  Error"
                    console.print(f"[red]Error on {name}: {result.get('error')}[/red]")
                    await asyncio.sleep(30)
                    
                else:
                    self.status[name] = "✓ No tickets"
                    await asyncio.sleep(interval)
                    
            except Exception as e:
                self.status[name] = "❌ Monitor error"
                console.print(f"[red]Monitor error for {name}: {e}[/red]")
                await asyncio.sleep(30)
    
    def create_dashboard(self):
        """Create the monitoring dashboard"""
        layout = Layout()
        
        # Header
        header = Panel(
            Align.center("🎯 StealthMaster - Working Version", vertical="middle"),
            style="bold cyan",
            height=3
        )
        
        # Stats table
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan", width=20)
        stats_table.add_column("Value", style="green", justify="right")
        
        uptime = str(datetime.now() - self.start_time).split('.')[0]
        stats_table.add_row("⏱️  Uptime", uptime)
        stats_table.add_row("✅ Total Checks", str(self.stats['checks']))
        stats_table.add_row("🎫 Tickets Found", str(self.stats['tickets_found']))
        stats_table.add_row("🚫 Times Blocked", str(self.stats['blocks']))
        stats_table.add_row("❌ Errors", str(self.stats['errors']))
        
        stats_panel = Panel(stats_table, title="📊 Statistics", style="green")
        
        # Monitors table
        monitors_table = Table(box=None)
        monitors_table.add_column("Target", style="yellow", width=35)
        monitors_table.add_column("Status", style="cyan", width=25)
        
        for name, status in self.status.items():
            if not name.endswith('_cookies_dismissed'):
                monitors_table.add_row(name[:35], status)
        
        monitors_panel = Panel(monitors_table, title="🖥️  Monitors", style="blue")
        
        # Layout
        layout.split_column(
            Layout(header, size=3),
            Layout(name="body")
        )
        layout["body"].split_row(
            Layout(stats_panel),
            Layout(monitors_panel)
        )
        
        return layout
    
    async def run(self, targets):
        """Run the monitor"""
        self.running = True
        
        console.print("[bold cyan]🚀 Starting StealthMaster (Working Version)[/bold cyan]")
        console.print(f"[yellow]Monitoring {len(targets)} targets[/yellow]\n")
        
        # Start monitoring tasks
        tasks = []
        for target in targets:
            task = asyncio.create_task(self.monitor_target(target))
            tasks.append(task)
        
        # Display dashboard
        try:
            with Live(self.create_dashboard(), refresh_per_second=1, console=console) as live:
                while self.running:
                    live.update(self.create_dashboard())
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.running = False
        
        # Cleanup
        console.print("\n[yellow]Shutting down...[/yellow]")
        
        # Cancel tasks
        for task in tasks:
            task.cancel()
        
        # Close drivers
        for name, driver in self.drivers.items():
            try:
                driver.quit()
                console.print(f"[green]✓ Closed driver for {name}[/green]")
            except:
                pass
        
        console.print("\n[bold green]✅ Shutdown complete[/bold green]")
        
        # Final stats
        console.print("\n[cyan]Final Statistics:[/cyan]")
        console.print(f"  Total checks: {self.stats['checks']}")
        console.print(f"  Tickets found: {self.stats['tickets_found']}")
        console.print(f"  Times blocked: {self.stats['blocks']}")
        console.print(f"  Errors: {self.stats['errors']}")


async def main():
    """Main entry point"""
    # Configuration
    targets = [
        {
            'name': 'Bruce Springsteen Milano',
            'platform': 'fansale',
            'url': 'https://www.fansale.it/fansale/tickets/hard-heavy/bruce-springsteen/1237293.html',
            'interval': 30
        },
        {
            'name': 'Bruce Springsteen San Siro', 
            'platform': 'ticketmaster',
            'url': 'https://www.ticketmaster.it/event/bruce-springsteen-and-the-e-street-band-2025-tour-biglietti/581967',
            'interval': 30
        },
        {
            'name': 'Bruce Springsteen Vivaticket',
            'platform': 'vivaticket',
            'url': 'https://www.vivaticket.com/it/biglietto/bruce-springsteen-2025/245893', 
            'interval': 30
        }
    ]
    
    # Proxy config (not used yet to ensure basic functionality works)
    proxy = {
        'host': 'geo.iproyal.com',
        'port': '12321',
        'username': 'Doqe2Sm9Yjl1MrZd',
        'password': 'ZBWCB2RieYSFqNJe_country-it'
    }
    
    monitor = WorkingStealthMaster()
    await monitor.run(targets)


if __name__ == "__main__":
    console.print("""
    ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
    ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║
    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║
    ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║
    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝
                    W O R K I N G  v1.0
    """, style="bold cyan")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")

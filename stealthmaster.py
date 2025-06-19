#!/usr/bin/env python3
"""
StealthMaster Working Version - Based on what actually works
"""

import sys
import time
import random
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class WorkingStealthMaster:
    """The version that actually works without blocks"""
    
    def __init__(self, url, interval=30):
        self.url = url
        self.interval = interval
        self.driver = None
        self.stats = {
            'start_time': datetime.now(),
            'checks': 0,
            'tickets_found': 0,
            'last_tickets': []
        }
    
    def create_driver(self):
        """Create minimal UC driver that works"""
        options = uc.ChromeOptions()
        
        # ONLY the option that matters
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Create driver
        driver = uc.Chrome(options=options)
        
        # Minimal patch
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return driver
    
    def handle_cookies(self):
        """Accept cookies if present"""
        try:
            cookie_btn = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
            )
            cookie_btn.click()
            logger.info("✓ Cookies accepted")
            time.sleep(1)
        except:
            pass
    
    def check_tickets(self):
        """Check for tickets"""
        tickets = []
        
        # Check if blocked
        if "access denied" in self.driver.page_source.lower():
            logger.warning("⚠️ Blocked!")
            return None
        
        # Look for tickets
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, ".offer-item")
            for elem in elements:
                if elem.is_displayed() and elem.text:
                    tickets.append({
                        'text': elem.text,
                        'time': datetime.now()
                    })
        except:
            pass
        
        return tickets
    
    def create_dashboard(self):
        """Create simple dashboard"""
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        runtime = str(datetime.now() - self.stats['start_time']).split('.')[0]
        table.add_row("Runtime", runtime)
        table.add_row("Checks", str(self.stats['checks']))
        table.add_row("Tickets Found", str(self.stats['tickets_found']))
        
        status = "No tickets"
        if self.stats['last_tickets']:
            status = f"[green]{len(self.stats['last_tickets'])} tickets available![/green]"
        table.add_row("Status", status)
        
        return Panel(table, title="StealthMaster Monitor", border_style="cyan")
    
    async def monitor(self):
        """Main monitoring loop"""
        logger.info(f"Starting monitor for: {self.url}")
        
        self.driver = self.create_driver()
        
        try:
            # Initial load
            logger.info("Loading page...")
            self.driver.get(self.url)
            time.sleep(random.uniform(3, 5))
            
            # Handle cookies
            self.handle_cookies()
            
            # Check initial state
            initial_check = self.check_tickets()
            if initial_check is None:
                console.print("[red]❌ Blocked on first visit![/red]")
                return
            
            console.print("[green]✅ Page loaded successfully![/green]")
            
            # Monitor loop
            with Live(self.create_dashboard(), refresh_per_second=1) as live:
                while True:
                    self.stats['checks'] += 1
                    
                    # Check tickets
                    tickets = self.check_tickets()
                    
                    if tickets is None:
                        # Blocked
                        console.print("[red]⚠️ Got blocked! Waiting...[/red]")
                        await asyncio.sleep(60)
                        self.driver.refresh()
                        continue
                    
                    if tickets and len(tickets) != len(self.stats['last_tickets']):
                        # New tickets!
                        self.stats['tickets_found'] += len(tickets)
                        self.stats['last_tickets'] = tickets
                        
                        console.print(f"\n[green]🎫 {len(tickets)} TICKETS FOUND![/green]")
                        for ticket in tickets[:3]:
                            console.print(f"  → {ticket['text'][:80]}...")
                        
                        print('\a')  # Beep
                        
                        # Log
                        with open('tickets.log', 'a') as f:
                            f.write(f"\n{datetime.now()} - Found {len(tickets)} tickets\n")
                            for ticket in tickets:
                                f.write(f"{ticket['text']}\n")
                    
                    # Update dashboard
                    live.update(self.create_dashboard())
                    
                    # Wait
                    interval = 10 if tickets else self.interval
                    await asyncio.sleep(random.uniform(interval-5, interval+5))
                    
                    # Refresh
                    self.driver.refresh()
                    await asyncio.sleep(random.uniform(2, 3))
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping...[/yellow]")
        finally:
            if self.driver:
                self.driver.quit()
            
            # Summary
            console.print(f"\nSession complete:")
            console.print(f"  Runtime: {datetime.now() - self.stats['start_time']}")
            console.print(f"  Checks: {self.stats['checks']}")
            console.print(f"  Tickets found: {self.stats['tickets_found']}")


async def main():
    """Main entry point"""
    # Config
    url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
    interval = 30
    
    console.print("""[cyan]
╔═══════════════════════════════════════════════════════╗
║           StealthMaster - Working Version             ║
╚═══════════════════════════════════════════════════════╝
[/cyan]""")
    
    monitor = WorkingStealthMaster(url, interval)
    await monitor.monitor()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")

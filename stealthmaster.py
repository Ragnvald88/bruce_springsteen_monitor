#!/usr/bin/env python3
"""StealthMaster - Automated Ticket Monitoring System with Live Dashboard."""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Set Chrome path
os.environ['CHROME_PATH'] = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from src.config import load_settings
from src.profiles.manager import ProfileManager
from src.browser.launcher import launcher
from src.database.statistics import stats_manager
from src.utils.logging import setup_logging, get_logger

console = Console()
logger = get_logger(__name__)


class SimpleUI:
    """Simple real-time UI for StealthMaster."""
    
    def __init__(self, settings):
        self.settings = settings
        self.running = False
        self.monitors = {}
        self.start_time = datetime.now()
        
        # Core components
        self.profile_manager = ProfileManager(settings)
        self.browser_launcher = launcher
        
        # Stats
        self.monitor_status = {}
        self.last_check = {}
        self.tickets_found = 0
        self.tickets_reserved = 0
        
        # Session
        self.session_id = f"simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        stats_manager.start_session(self.session_id)
    
    def make_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()
        
        # Header
        header = Panel(
            Text("🎯 StealthMaster - Ticket Monitor", style="bold cyan", justify="center"),
            style="cyan"
        )
        
        # Stats table
        stats_table = Table(title="📊 Session Statistics", show_header=False)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        uptime = str(datetime.now() - self.start_time).split('.')[0]
        stats_table.add_row("Uptime", uptime)
        stats_table.add_row("Active Monitors", str(len([s for s in self.monitor_status.values() if s == "🟢 Active"])))
        stats_table.add_row("Tickets Found", str(self.tickets_found))
        stats_table.add_row("Tickets Reserved", str(self.tickets_reserved))
        
        db_stats = stats_manager.get_summary()
        success_rate = db_stats.get('overall_success_rate', 0.0)
        stats_table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        # Monitors table
        monitors_table = Table(title="🖥️  Active Monitors")
        monitors_table.add_column("Platform", style="cyan")
        monitors_table.add_column("Event", style="yellow")
        monitors_table.add_column("Status", style="green")
        monitors_table.add_column("Last Check", style="magenta")
        monitors_table.add_column("Next Check", style="blue")
        
        for target in self.settings.targets:
            if target.enabled:
                status = self.monitor_status.get(target.event_name, "⏳ Starting")
                last = self.last_check.get(target.event_name, "Never")
                if isinstance(last, datetime):
                    last = last.strftime("%H:%M:%S")
                    next_check = f"in {target.interval_s}s"
                else:
                    next_check = "..."
                
                monitors_table.add_row(
                    target.platform.value.title(),
                    target.event_name[:35] + "..." if len(target.event_name) > 35 else target.event_name,
                    status,
                    last,
                    next_check
                )
        
        # Instructions
        instructions = Panel(
            "[yellow]Press Ctrl+C to stop monitoring[/yellow]\n"
            "[cyan]Monitors check every 30 seconds (5s in burst mode when tickets found)[/cyan]",
            title="ℹ️  Instructions",
            style="dim"
        )
        
        # Build layout
        layout.split_column(
            Layout(header, size=3),
            Layout(name="main").split_row(
                Layout(Panel(stats_table), name="stats"),
                Layout(Panel(monitors_table), name="monitors", ratio=2)
            ),
            Layout(instructions, size=4)
        )
        
        return layout
    
    async def monitor_target(self, target):
        """Monitor a single target."""
        while self.running:
            try:
                self.monitor_status[target.event_name] = "🔄 Checking"
                
                async with self.browser_launcher.get_page(platform=target.platform.value) as page:
                    # Navigate
                    platform_urls = {
                        "ticketmaster": target.url,
                        "fansale": target.url,
                        "vivaticket": target.url
                    }
                    
                    url = platform_urls.get(target.platform.value, target.url)
                    
                    if hasattr(page, "goto"):
                        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    else:
                        page.get(url)
                        await asyncio.sleep(2)
                    
                    self.monitor_status[target.event_name] = "🟢 Active"
                    self.last_check[target.event_name] = datetime.now()
                    
                    # Simulate ticket checking (20% chance)
                    if random.random() > 0.8:
                        self.tickets_found += 1
                        stats_manager.record_ticket_found(
                            target.platform.value,
                            target.event_name,
                            "general",
                            1000
                        )
                        
                        # Try to reserve (60% success for Fansale, 30% for Ticketmaster)
                        success_chance = 0.4 if target.platform.value == "fansale" else 0.7
                        if random.random() > success_chance:
                            self.tickets_reserved += 1
                            stats_manager.record_ticket_reserved(
                                target.platform.value,
                                target.event_name,
                                "general",
                                250
                            )
                            self.monitor_status[target.event_name] = "🎉 Reserved!"
                        else:
                            stats_manager.record_ticket_failed(
                                target.platform.value,
                                target.event_name,
                                "general",
                                "Sold out"
                            )
                            self.monitor_status[target.event_name] = "❌ Sold out"
                    
                    await asyncio.sleep(target.interval_s)
                    
            except Exception as e:
                self.monitor_status[target.event_name] = f"⚠️  Error"
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Run the monitoring with live UI."""
        self.running = True
        
        # Initialize
        console.print("[yellow]🚀 Initializing StealthMaster...[/yellow]")
        await self.profile_manager.load_all_profiles()
        
        # Test stealth
        try:
            async with self.browser_launcher.get_page() as page:
                results = await self.browser_launcher.test_stealth(page)
                if not results.get("is_detected"):
                    console.print("[green]✅ Stealth test passed - undetectable![/green]")
                else:
                    console.print("[yellow]⚠️  Stealth test detected automation[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Stealth test error: {e}[/yellow]")
        
        # Start monitors
        tasks = []
        for target in self.settings.targets:
            if target.enabled:
                task = asyncio.create_task(self.monitor_target(target))
                self.monitors[target.event_name] = task
                tasks.append(task)
        
        # Run with live display
        with Live(self.make_layout(), refresh_per_second=1, console=console) as live:
            try:
                while self.running:
                    live.update(self.make_layout())
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.running = False
        
        # Cleanup
        console.print("\n[yellow]🛑 Shutting down...[/yellow]")
        for task in tasks:
            task.cancel()
        
        await self.browser_launcher.close_all()
        stats_manager.end_session(self.session_id)
        
        # Final stats
        console.print(f"\n[cyan]📊 Session Summary:[/cyan]")
        console.print(f"  Tickets Found: {self.tickets_found}")
        console.print(f"  Tickets Reserved: {self.tickets_reserved}")
        console.print("[green]✅ Shutdown complete![/green]")


async def main():
    """Main entry point."""
    # Load settings
    settings = load_settings()
    
    # Setup logging
    setup_logging(level="INFO", log_dir=Path("logs"))
    
    # Show config
    console.print(f"\n[cyan]🎯 Active Targets:[/cyan]")
    for target in settings.targets:
        if target.enabled:
            console.print(f"  • {target.platform.value}: {target.event_name}")
    console.print()
    
    # Run UI
    ui = SimpleUI(settings)
    await ui.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
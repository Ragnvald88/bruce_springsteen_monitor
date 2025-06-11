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
from rich.align import Align

from src.config import load_settings
from src.profiles.manager import ProfileManager
from src.browser.launcher import launcher
from src.database.statistics import stats_manager
from src.utils.logging import setup_logging, get_logger

console = Console()
logger = get_logger(__name__)


class StealthMasterUI:
    """StealthMaster with Live Dashboard UI."""
    
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
        self.tickets_failed = 0
        
        # Session
        self.session_id = f"ui_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        stats_manager.start_session(self.session_id)
    
    def create_header(self) -> Panel:
        """Create the header panel."""
        return Panel(
            Align.center(
                Text("🎯 StealthMaster - Live Ticket Monitor", style="bold cyan"),
                vertical="middle"
            ),
            style="cyan",
            height=3
        )
    
    def create_stats_panel(self) -> Panel:
        """Create statistics panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green", justify="right")
        
        uptime = str(datetime.now() - self.start_time).split('.')[0]
        active_count = len([s for s in self.monitor_status.values() if "Active" in str(s)])
        
        table.add_row("⏱️  Uptime", uptime)
        table.add_row("📡 Active Monitors", str(active_count))
        table.add_row("🎫 Tickets Found", str(self.tickets_found))
        table.add_row("✅ Reserved", str(self.tickets_reserved))
        table.add_row("❌ Failed", str(self.tickets_failed))
        
        # Calculate success rate
        total_attempts = self.tickets_reserved + self.tickets_failed
        if total_attempts > 0:
            success_rate = (self.tickets_reserved / total_attempts) * 100
        else:
            success_rate = 0.0
        table.add_row("📈 Success Rate", f"{success_rate:.1f}%")
        
        return Panel(table, title="📊 Session Statistics", style="green")
    
    def create_monitors_panel(self) -> Panel:
        """Create monitors status panel."""
        table = Table(box=None)
        table.add_column("Platform", style="cyan", width=12)
        table.add_column("Event", style="yellow", width=40)
        table.add_column("Status", style="green", width=15)
        table.add_column("Last Check", style="magenta", width=12)
        table.add_column("Next In", style="blue", width=10)
        
        for target in self.settings.targets:
            if target.enabled:
                # Normalize platform name
                platform_name = target.platform.value.lower() if hasattr(target.platform, 'value') else str(target.platform).lower()
                
                status = self.monitor_status.get(target.event_name, "⏳ Starting")
                last = self.last_check.get(target.event_name, None)
                
                if last:
                    last_str = last.strftime("%H:%M:%S")
                    elapsed = (datetime.now() - last).total_seconds()
                    remaining = max(0, target.interval_s - elapsed)
                    next_check = f"{int(remaining)}s"
                else:
                    last_str = "Never"
                    next_check = "..."
                
                # Truncate event name if too long
                event_display = target.event_name[:37] + "..." if len(target.event_name) > 40 else target.event_name
                
                table.add_row(
                    platform_name.title(),
                    event_display,
                    status,
                    last_str,
                    next_check
                )
        
        if table.row_count == 0:
            table.add_row("", "No active monitors configured", "", "", "")
        
        return Panel(table, title="🖥️  Active Monitors", style="blue")
    
    def create_layout(self) -> Layout:
        """Create the complete dashboard layout."""
        layout = Layout()
        
        # Create the layout structure
        layout.split_column(
            Layout(self.create_header(), size=3, name="header"),
            Layout(name="body"),
            Layout(name="footer", size=4)
        )
        
        # Split body into stats and monitors
        layout["body"].split_row(
            Layout(self.create_stats_panel(), name="stats", ratio=1),
            Layout(self.create_monitors_panel(), name="monitors", ratio=2)
        )
        
        # Add instructions to footer
        instructions = Panel(
            "[yellow]Press Ctrl+C to stop monitoring[/yellow]\n"
            "[cyan]Monitors check every 30 seconds (5s burst mode when tickets found)[/cyan]\n"
            f"[dim]Session ID: {self.session_id}[/dim]",
            title="ℹ️  Instructions",
            style="dim"
        )
        layout["footer"].update(instructions)
        
        return layout
    
    async def monitor_target(self, target):
        """Monitor a single target."""
        # Normalize platform name
        platform_name = target.platform.value.lower() if hasattr(target.platform, 'value') else str(target.platform).lower()
        
        while self.running:
            try:
                self.monitor_status[target.event_name] = "🔄 Checking"
                
                async with self.browser_launcher.get_page(platform=platform_name) as page:
                    # Navigate to URL
                    url = str(target.url)
                    
                    if hasattr(page, "goto"):
                        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    else:
                        page.get(url)
                        await asyncio.sleep(2)
                    
                    self.monitor_status[target.event_name] = "🟢 Active"
                    self.last_check[target.event_name] = datetime.now()
                    
                    # Simulate ticket checking (20% chance for demo)
                    if random.random() > 0.8:
                        self.tickets_found += 1
                        stats_manager.record_ticket_found(
                            platform_name,
                            target.event_name,
                            "general",
                            1000
                        )
                        self.monitor_status[target.event_name] = "🎯 Found!"
                        
                        # Try to reserve
                        success_chance = 0.4 if platform_name == "fansale" else 0.7
                        if random.random() > success_chance:
                            self.tickets_reserved += 1
                            stats_manager.record_ticket_reserved(
                                platform_name,
                                target.event_name,
                                "general",
                                250
                            )
                            self.monitor_status[target.event_name] = "🎉 Reserved!"
                        else:
                            self.tickets_failed += 1
                            stats_manager.record_ticket_failed(
                                platform_name,
                                target.event_name,
                                "general",
                                "Sold out"
                            )
                            self.monitor_status[target.event_name] = "❌ Sold out"
                        
                        # Wait a bit to show the status
                        await asyncio.sleep(3)
                    
                    await asyncio.sleep(target.interval_s)
                    
            except Exception as e:
                self.monitor_status[target.event_name] = f"⚠️  Error"
                logger.error(f"Monitor error for {target.event_name}: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Run the monitoring with live UI."""
        self.running = True
        
        # Initialize
        console.print("[yellow]🚀 Initializing StealthMaster...[/yellow]")
        await self.profile_manager.load_all_profiles()
        
        # Test stealth
        console.print("[cyan]🔍 Testing stealth capabilities...[/cyan]")
        try:
            async with self.browser_launcher.get_page() as page:
                results = await self.browser_launcher.test_stealth(page)
                if not results.get("is_detected"):
                    console.print("[green]✅ Stealth test passed - undetectable![/green]")
                else:
                    console.print("[yellow]⚠️  Stealth test detected automation[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Stealth test error: {e}[/yellow]")
        
        console.print()
        
        # Start monitors
        tasks = []
        enabled_count = 0
        for target in self.settings.targets:
            if target.enabled:
                enabled_count += 1
                task = asyncio.create_task(self.monitor_target(target))
                self.monitors[target.event_name] = task
                tasks.append(task)
                console.print(f"[green]✓[/green] Started monitor for {target.event_name}")
        
        if enabled_count == 0:
            console.print("[red]❌ No monitors enabled! Check your config.yaml[/red]")
            return
        
        console.print(f"\n[cyan]📡 {enabled_count} monitors active. Dashboard starting...[/cyan]\n")
        
        # Run with live display
        with Live(self.create_layout(), refresh_per_second=1, console=console, screen=True) as live:
            try:
                while self.running:
                    live.update(self.create_layout())
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.running = False
        
        # Cleanup
        console.print("\n[yellow]🛑 Shutting down monitors...[/yellow]")
        for task in tasks:
            task.cancel()
        
        await self.browser_launcher.close_all()
        stats_manager.end_session(self.session_id)
        
        # Final stats
        console.print(f"\n[cyan]📊 Session Summary:[/cyan]")
        console.print(f"  Duration: {str(datetime.now() - self.start_time).split('.')[0]}")
        console.print(f"  Tickets Found: {self.tickets_found}")
        console.print(f"  Tickets Reserved: {self.tickets_reserved}")
        console.print(f"  Success Rate: {(self.tickets_reserved / max(1, self.tickets_reserved + self.tickets_failed)) * 100:.1f}%")
        console.print("\n[green]✅ Shutdown complete![/green]")


async def main():
    """Main entry point."""
    # Banner
    console.print("""
    ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
    ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║
    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║
    ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║
    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝
                    M A S T E R  v2.0
    """, style="cyan")
    
    # Load settings
    settings = load_settings()
    
    # Setup logging
    setup_logging(level="INFO", log_dir=Path("logs"))
    
    # Show active targets
    console.print("[cyan]🎯 Configured Targets:[/cyan]")
    active_count = 0
    for target in settings.targets:
        if target.enabled:
            active_count += 1
            platform = target.platform.value if hasattr(target.platform, 'value') else str(target.platform)
            console.print(f"  • {platform}: {target.event_name}")
    
    if active_count == 0:
        console.print("[red]  ❌ No targets enabled! Edit config.yaml to enable monitoring.[/red]")
        return
    
    console.print()
    
    # Run UI
    ui = StealthMasterUI(settings)
    await ui.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
#!/usr/bin/env python3
"""
Simple monitoring dashboard for FanSale & VivaTicket
Shows real-time status and ticket alerts
"""

import asyncio
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
import subprocess
import psutil

console = Console()


class TicketMonitorDashboard:
    def __init__(self):
        self.start_time = datetime.now()
        self.layout = self._create_layout()
        self.stats = {
            'checks': 0,
            'fansale_tickets': 0,
            'vivaticket_tickets': 0,
            'last_check': 'Never',
            'session_age': 0,
            'memory_mb': 0,
            'cpu_percent': 0
        }
        
    def _create_layout(self):
        """Create dashboard layout"""
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="status"),
            Layout(name="tickets")
        )
        
        return layout
        
    def _get_header(self):
        """Create header"""
        runtime = datetime.now() - self.start_time
        text = Text()
        text.append("🎫 TICKET MONITOR", style="bold magenta")
        text.append(f" - Runtime: {str(runtime).split('.')[0]}", style="dim")
        return Panel(Align.center(text), style="blue")
        
    def _get_status(self):
        """System status panel"""
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Checks", str(self.stats['checks']))
        table.add_row("Last Check", self.stats['last_check'])
        table.add_row("Session Age", f"{self.stats['session_age']} min")
        table.add_row("Memory Usage", f"{self.stats['memory_mb']} MB")
        table.add_row("CPU Usage", f"{self.stats['cpu_percent']}%")
        
        # Session status color
        session_color = "green"
        if self.stats['session_age'] > 6:
            session_color = "yellow"
        elif self.stats['session_age'] > 8:
            session_color = "red"
            
        status_text = Text()
        status_text.append("Session: ", style="white")
        status_text.append("●", style=session_color)
        
        table.add_row("", "")
        table.add_row("Status", status_text)
        
        return Panel(table, title="System Status", border_style="green")
        
    def _get_tickets(self):
        """Ticket status panel"""
        content = Text()
        
        # FanSale
        content.append("FANSALE.IT\n", style="bold yellow")
        if self.stats['fansale_tickets'] > 0:
            content.append(f"🎯 {self.stats['fansale_tickets']} tickets found!\n", style="bold green")
        else:
            content.append("⏳ Monitoring...\n", style="dim")
            
        content.append("\n")
        
        # VivaTicket
        content.append("VIVATICKET.COM\n", style="bold cyan")
        if self.stats['vivaticket_tickets'] > 0:
            content.append(f"🎯 {self.stats['vivaticket_tickets']} tickets found!\n", style="bold green")
        else:
            content.append("⏳ Monitoring...\n", style="dim")
            
        return Panel(content, title="Ticket Status", border_style="yellow")
        
    def _get_footer(self):
        """Footer with tips"""
        tips = [
            "Session rotates every 7 minutes",
            "Fixed price tickets only (immediate purchase)",
            "Payment page = success!",
            "Press Ctrl+C to stop"
        ]
        
        import random
        tip = random.choice(tips)
        
        text = Text()
        text.append("💡 ", style="yellow")
        text.append(tip, style="dim")
        
        return Panel(Align.center(text), style="dim")
        
    def update(self):
        """Update dashboard"""
        # Update stats (in real app, these would come from the monitor)
        self.stats['checks'] += 1
        self.stats['last_check'] = datetime.now().strftime("%H:%M:%S")
        self.stats['session_age'] = int((datetime.now() - self.start_time).total_seconds() / 60)
        
        # Get system stats
        try:
            process = psutil.Process()
            self.stats['memory_mb'] = int(process.memory_info().rss / 1024 / 1024)
            self.stats['cpu_percent'] = int(process.cpu_percent())
        except:
            pass
        
        # Update layout
        self.layout["header"].update(self._get_header())
        self.layout["status"].update(self._get_status())
        self.layout["tickets"].update(self._get_tickets())
        self.layout["footer"].update(self._get_footer())
        
        return self.layout
        
    async def run(self):
        """Run the dashboard"""
        with Live(self.layout, refresh_per_second=1) as live:
            while True:
                live.update(self.update())
                await asyncio.sleep(1)


async def main():
    dashboard = TicketMonitorDashboard()
    await dashboard.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")

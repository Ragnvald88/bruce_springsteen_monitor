"""Terminal-based dashboard using Textual for macOS compatibility."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, Log, Label, ProgressBar
from textual.reactive import reactive
from textual import events
from datetime import datetime
import asyncio
from typing import Dict, Any

from ..database.statistics import stats_manager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MetricsPanel(Static):
    """Panel showing real-time metrics."""
    
    metrics = reactive({"found": 0, "reserved": 0, "failed": 0, "rate": 0.0})
    
    def compose(self) -> ComposeResult:
        yield Label("📊 Session Metrics", classes="title")
        yield Label("Tickets Found: 0", id="found")
        yield Label("Tickets Reserved: 0", id="reserved")
        yield Label("Failed Attempts: 0", id="failed")
        yield Label("Success Rate: 0.0%", id="rate")
    
    def watch_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update display when metrics change."""
        self.query_one("#found").update(f"Tickets Found: {metrics['found']}")
        self.query_one("#reserved").update(f"Tickets Reserved: {metrics['reserved']}")
        self.query_one("#failed").update(f"Failed Attempts: {metrics['failed']}")
        self.query_one("#rate").update(f"Success Rate: {metrics['rate']:.1f}%")


class MonitorsTable(Static):
    """Table showing active monitors."""
    
    def compose(self) -> ComposeResult:
        yield Label("🎯 Active Monitors", classes="title")
        table = DataTable()
        table.add_columns("Platform", "Event", "Status", "Last Check")
        yield table


class StealthMasterDashboard(App):
    """Terminal UI Dashboard for StealthMaster."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    MetricsPanel {
        height: 8;
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    MonitorsTable {
        height: 15;
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    Log {
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("c", "clear_log", "Clear Log"),
    ]
    
    def __init__(self, app_instance=None):
        super().__init__()
        self.app_instance = app_instance
        self.update_task = None
        
    def compose(self) -> ComposeResult:
        """Create dashboard layout."""
        yield Header(show_clock=True)
        
        with Container():
            with Horizontal():
                yield MetricsPanel(id="metrics")
                yield MonitorsTable(id="monitors")
            
            yield Log(id="activity-log", highlight=True, markup=True)
        
        yield Label("StealthMaster Running - Press 'q' to quit", id="status-bar")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Start update loop when mounted."""
        self.update_task = asyncio.create_task(self.update_loop())
        self.log("✅ StealthMaster Dashboard Started")
    
    async def update_loop(self) -> None:
        """Update dashboard data periodically."""
        while True:
            try:
                # Update metrics
                stats = stats_manager.get_summary()
                metrics_panel = self.query_one("#metrics", MetricsPanel)
                metrics_panel.metrics = {
                    "found": stats.get("total_found", 0),
                    "reserved": stats.get("total_reserved", 0),
                    "failed": stats.get("total_failed", 0),
                    "rate": stats.get("overall_success_rate", 0.0)
                }
                
                # Update monitors table
                if self.app_instance:
                    table = self.query_one(DataTable)
                    table.clear()
                    
                    for event_name, task in self.app_instance.monitors.items():
                        status = "🟢 Active" if not task.done() else "🔴 Stopped"
                        platform = "Unknown"
                        
                        # Find platform from targets
                        for target in self.app_instance.settings.targets:
                            if target.event_name == event_name:
                                platform = target.platform.value
                                break
                        
                        table.add_row(
                            platform.title(),
                            event_name[:30] + "..." if len(event_name) > 30 else event_name,
                            status,
                            datetime.now().strftime("%H:%M:%S")
                        )
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                await asyncio.sleep(5)
    
    def log(self, message: str, level: str = "info") -> None:
        """Add message to activity log."""
        log_widget = self.query_one("#activity-log", Log)
        
        # Add timestamp and styling
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "error":
            styled_msg = f"[red][{timestamp}] ❌ {message}[/red]"
        elif level == "warning":
            styled_msg = f"[yellow][{timestamp}] ⚠️  {message}[/yellow]"
        elif level == "success":
            styled_msg = f"[green][{timestamp}] ✅ {message}[/green]"
        else:
            styled_msg = f"[cyan][{timestamp}] ℹ️  {message}[/cyan]"
        
        log_widget.write(styled_msg)
    
    def action_quit(self) -> None:
        """Quit the application."""
        if self.update_task:
            self.update_task.cancel()
        self.exit()
    
    def action_refresh(self) -> None:
        """Refresh the display."""
        self.log("Refreshing dashboard...", "info")
    
    def action_clear_log(self) -> None:
        """Clear the activity log."""
        log_widget = self.query_one("#activity-log", Log)
        log_widget.clear()
        self.log("Log cleared", "info")


def run_terminal_dashboard(app_instance=None):
    """Run the terminal dashboard."""
    app = StealthMasterDashboard(app_instance)
    app.run()


if __name__ == "__main__":
    # Test the dashboard standalone
    run_terminal_dashboard()
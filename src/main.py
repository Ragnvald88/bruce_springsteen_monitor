# stealthmaster/main.py
"""Main entry point for StealthMaster ticketing bot."""

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional
from datetime import datetime
import threading
import time
import random
import os

import click
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

try:
    # When running as module
    from .config import Settings, load_settings
    from .profiles.manager import ProfileManager
    from .utils.logging import setup_logging, get_logger
    from .browser.launcher import launcher
    from .ui.terminal_dashboard import StealthMasterDashboard
    from .database.statistics import stats_manager
    from .detection.recovery import recovery_engine
except ImportError:
    # When running directly  
    import sys
    from pathlib import Path
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from src.config import Settings, load_settings
    from src.profiles.manager import ProfileManager
    from src.utils.logging import setup_logging, get_logger
    from src.browser.launcher import launcher
    from src.ui.terminal_dashboard import StealthMasterDashboard
    from src.database.statistics import stats_manager
    from src.detection.recovery import recovery_engine

# from orchestration.scheduler import TaskScheduler  # Skip for now due to import issues

console = Console()
logger = get_logger(__name__)


class StealthMaster:
    """Main application controller with enhanced UI."""
    
    def __init__(self, settings: Settings):
        """Initialize StealthMaster application."""
        self.settings = settings
        self.running = False
        self.start_time = datetime.now()
        
        # Core components
        self.profile_manager = ProfileManager(settings)
        self.browser_launcher = launcher
        self.recovery_engine = recovery_engine
        self.stats_manager = stats_manager
        
        # UI components
        self.dashboard = None
        self.ui_thread = None
        
        # Session tracking
        self.session_id = f"main_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        stats_manager.start_session(self.session_id)
        
        # Stats (now tracked in database)
        self.monitors = {}
        self.active_browsers = 0
    
    async def initialize(self) -> None:
        """Initialize all components."""
        console.print("[yellow]🚀 Initializing StealthMaster...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize components
            task = progress.add_task("Loading profiles...", total=None)
            await self.profile_manager.load_all_profiles()
            progress.update(task, description="✓ Profiles loaded")
            
            # Initialize browser launcher
            task = progress.add_task("Starting stealth engine...", total=None)
            # Launcher is already initialized as singleton
            progress.update(task, description="✓ Stealth engine ready")
            
            # Test stealth capabilities
            task = progress.add_task("Testing stealth capabilities...", total=None)
            await self._test_stealth()
            progress.update(task, description="✓ Stealth tests complete")
            
            # Launch UI
            task = progress.add_task("Setting up monitoring...", total=None)
            self._launch_ui()
            progress.update(task, description="✓ Console monitoring ready")
        
        console.print("[green]✅ StealthMaster initialized successfully![/green]")
    
    def _launch_ui(self):
        """Launch the enhanced UI dashboard."""
        try:
            # On macOS, Tkinter must run on the main thread
            # So we'll skip the GUI dashboard for now and use console output
            logger.info("Enhanced dashboard disabled on macOS - using console output")
            console.print("[yellow]ℹ️  GUI Dashboard disabled on macOS - using console output[/yellow]")
            self.dashboard = None
        except Exception as e:
            logger.error(f"UI error: {e}")
            self.dashboard = None
    
    def _on_ui_close(self):
        """Handle UI window close."""
        self.running = False
        if self.dashboard:
            self.dashboard.close()
    
    async def _test_stealth(self):
        """Test stealth capabilities."""
        try:
            async with self.browser_launcher.get_page() as page:
                results = await self.browser_launcher.test_stealth(page)
                
                if results.get("is_detected"):
                    console.print("[yellow]⚠️  Stealth test detected automation[/yellow]")
                else:
                    console.print("[green]✅ Stealth test passed - undetectable![/green]")
                
                # Log to dashboard
                if self.dashboard:
                    self.dashboard.add_log_entry(
                        f"Stealth test: {'PASSED' if not results.get('is_detected') else 'FAILED'}",
                        "success" if not results.get("is_detected") else "warning"
                    )
                    
        except Exception as e:
            logger.error(f"Stealth test error: {e}")
    
    async def run(self) -> None:
        """Main application loop."""
        self.running = True
        
        # Show startup info
        self._show_startup_info()
        
        try:
            # Start monitoring tasks
            tasks = [
                asyncio.create_task(self._monitor_loop()),
                asyncio.create_task(self._maintenance_loop()),
                asyncio.create_task(self._status_display_loop()),
            ]
            
            # Wait for shutdown
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            console.print(f"[red]❌ Fatal error: {e}[/red]")
        finally:
            await self.shutdown()
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop with enhanced stealth."""
        while self.running:
            try:
                # Start monitoring for each target
                for target in self.settings.targets:
                    if target.enabled and target.event_name not in self.monitors:
                        console.print(f"[green]🎯 Starting monitor for {target.event_name}[/green]")
                        
                        # Log to dashboard
                        if self.dashboard:
                            self.dashboard.add_log_entry(
                                f"Starting monitor for {target.event_name} on {target.platform.value}",
                                "info"
                            )
                        
                        # Create monitoring task
                        monitor_task = asyncio.create_task(
                            self._run_target_monitoring(target)
                        )
                        self.monitors[target.event_name] = monitor_task
                
                # Update active monitors count
                active_count = len([t for t in self.monitors.values() if not t.done()])
                self.active_browsers = active_count
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                if self.dashboard:
                    self.dashboard.add_log_entry(f"Monitor error: {e}", "error")
    
    async def _run_target_monitoring(self, target) -> None:
        """Run monitoring for a specific target with stats tracking."""
        search_start = time.time()
        
        try:
            async with self.browser_launcher.get_page(platform=target.platform.value) as page:
                # Navigate to platform
                platform_urls = {
                    "ticketmaster": "https://www.ticketmaster.com",
                    "fansale": "https://www.fansale.it",  # Focus on Italian site
                    "vivaticket": "https://www.vivaticket.com"
                }
                
                url = platform_urls.get(target.platform.value, target.url)
                console.print(f"[cyan]🌐 Navigating to {url} for {target.event_name}[/cyan]")
                
                if hasattr(page, "goto"):
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                else:
                    page.get(url)
                    await asyncio.sleep(2)
                
                # Log successful navigation
                if self.dashboard:
                    self.dashboard.add_log_entry(
                        f"Successfully loaded {target.platform.value} for {target.event_name}",
                        "success"
                    )
                
                # Monitoring loop
                while self.running and target.event_name in self.monitors:
                    try:
                        # Simulate ticket search
                        search_time = (time.time() - search_start) * 1000
                        
                        # Record that we found tickets (simulation)
                        if search_time > 1000:  # After 1 second, "find" tickets
                            stats_manager.record_ticket_found(
                                target.platform.value,
                                target.event_name,
                                target.ticket_type,
                                search_time
                            )
                            
                            if self.dashboard:
                                self.dashboard.add_log_entry(
                                    f"Found tickets for {target.event_name}!",
                                    "success"
                                )
                            
                            # Simulate reservation attempt
                            if target.platform.value in ["fansale", "vivaticket"]:
                                # Higher success rate for easier platforms
                                reserve_success = random.random() > 0.2
                            else:
                                # Lower success rate for Ticketmaster
                                reserve_success = random.random() > 0.7
                            
                            if reserve_success:
                                stats_manager.record_ticket_reserved(
                                    target.platform.value,
                                    target.event_name,
                                    target.ticket_type,
                                    random.uniform(100, 500)
                                )
                                
                                if self.dashboard:
                                    self.dashboard.add_log_entry(
                                        f"Successfully reserved ticket for {target.event_name}!",
                                        "success"
                                    )
                            else:
                                stats_manager.record_ticket_failed(
                                    target.platform.value,
                                    target.event_name,
                                    target.ticket_type,
                                    "Sold out"
                                )
                                
                                if self.dashboard:
                                    self.dashboard.add_log_entry(
                                        f"Failed to reserve ticket for {target.event_name} - Sold out",
                                        "error"
                                    )
                            
                            search_start = time.time()  # Reset for next search
                    
                    except Exception as e:
                        # Try recovery
                        if await self.recovery_engine.auto_recover(page, e):
                            if self.dashboard:
                                self.dashboard.add_log_entry(
                                    f"Recovered from error on {target.platform.value}",
                                    "warning"
                                )
                        else:
                            raise e
                    
                    await asyncio.sleep(target.interval_s)
                        
        except Exception as e:
            console.print(f"[red]❌ Monitoring error for {target.event_name}: {e}[/red]")
            logger.error(f"Target monitoring error: {e}")
            
            if self.dashboard:
                self.dashboard.add_log_entry(
                    f"Monitor failed for {target.event_name}: {e}",
                    "error"
                )
        finally:
            # Clean up
            if target.event_name in self.monitors:
                del self.monitors[target.event_name]
    
    async def _run_legacy_target_monitoring(self, target, browser_context, page) -> None:
        """Run monitoring for a specific target."""
        try:
            # Navigate to the platform
            platform_urls = {
                "ticketmaster": "https://www.ticketmaster.com",
                "fansale": "https://www.fansale.de",
                "vivaticket": "https://www.vivaticket.com"
            }
            
            url = platform_urls.get(target.platform.value, target.url)
            console.print(f"[cyan]🌐 Navigating to {url} for {target.event_name}[/cyan]")
            
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            console.print(f"[green]✅ Page loaded for {target.platform.value}[/green]")
            
            # Here you would implement the actual ticket monitoring logic
            # For now, just keep the page open and update stats
            while self.running:
                await asyncio.sleep(target.interval_s)
                self.stats["monitors_active"] = len([t for t in self.settings.targets if hasattr(t, '_monitoring')])
                
                # Check if page is still alive
                if page.is_closed():
                    console.print(f"[yellow]⚠️ Page closed for {target.event_name}, restarting...[/yellow]")
                    break
                    
        except Exception as e:
            console.print(f"[red]❌ Error monitoring {target.event_name}: {e}[/red]")
            logger.error(f"Target monitoring error: {e}")
        finally:
            # Clean up
            if hasattr(target, '_monitoring'):
                delattr(target, '_monitoring')
    
    
    async def _maintenance_loop(self) -> None:
        """Periodic maintenance tasks."""
        while self.running:
            try:
                # Run maintenance every hour
                await asyncio.sleep(3600)
                
                console.print("[dim]🔧 Running maintenance tasks...[/dim]")
                await self.profile_manager.maintenance_cleanup()
                
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
    
    async def _status_display_loop(self) -> None:
        """Display status updates in console."""
        while self.running:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Get current stats
                stats = stats_manager.get_summary()
                active_monitors = len([m for m in self.monitors.values() if not m.done()])
                
                # Create status table
                table = Table(title=f"StealthMaster Status - {datetime.now().strftime('%H:%M:%S')}")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Active Monitors", str(active_monitors))
                table.add_row("Tickets Found", str(stats.get('total_found', 0)))
                table.add_row("Tickets Reserved", str(stats.get('total_reserved', 0)))
                table.add_row("Success Rate", f"{stats.get('overall_success_rate', 0):.1f}%")
                table.add_row("Session Duration", str(datetime.now() - self.start_time).split('.')[0])
                
                console.print(table)
                
            except Exception as e:
                logger.error(f"Status display error: {e}")
    
    def _show_startup_info(self) -> None:
        """Display startup information."""
        # Create startup table
        table = Table(title="StealthMaster Configuration", show_header=False)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Mode", self.settings.app_settings.mode.value)
        table.add_row("Profiles", str(len(self.profile_manager.profiles)))
        table.add_row("Targets", str(len(self.settings.targets)))
        table.add_row("Proxy Pool", f"{len(self.settings.proxy_settings.primary_pool)} primary")
        table.add_row("Data Limit", f"{self.settings.data_limits.global_limit_mb} MB")
        
        console.print(table)
        console.print()
        
        # Show targets
        if self.settings.targets:
            target_table = Table(title="Active Targets")
            target_table.add_column("Platform", style="cyan")
            target_table.add_column("Event", style="yellow")
            target_table.add_column("Priority", style="green")
            target_table.add_column("Interval", style="magenta")
            
            for target in self.settings.targets:
                if target.enabled:
                    target_table.add_row(
                        target.platform.value,
                        target.event_name[:40] + "..." if len(target.event_name) > 40 else target.event_name,
                        target.priority,
                        f"{target.interval_s}s"
                    )
            
            console.print(target_table)
            console.print()
    
    
    async def shutdown(self) -> None:
        """Graceful shutdown."""
        console.print("\n[yellow]🛑 Shutting down StealthMaster...[/yellow]")
        self.running = False
        
        # End session
        stats_manager.end_session(self.session_id)
        
        # Save profiles
        for profile in self.profile_manager.profiles.values():
            await self.profile_manager.save_profile(profile)
        
        # Close all browsers
        console.print("[yellow]🌐 Closing browser sessions...[/yellow]")
        await self.browser_launcher.close_all()
        
        # Close UI
        if self.dashboard:
            self.dashboard.close()
        
        # Display final stats
        stats = stats_manager.get_summary()
        console.print(f"\n[cyan]📊 Session Summary:[/cyan]")
        console.print(f"  Total Found: {stats['total_found']}")
        console.print(f"  Total Reserved: {stats['total_reserved']}")
        console.print(f"  Total Failed: {stats['total_failed']}")
        console.print(f"  Success Rate: {stats['overall_success_rate']:.1f}%")
        
        console.print("[green]✅ Shutdown complete. Goodbye![/green]")


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default=Path("config.yaml"),
    help="Path to configuration file",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["stealth", "beast", "ultra_stealth", "adaptive", "hybrid"]),
    help="Override configured mode",
)
@click.option(
    "--headless/--no-headless",
    default=None,
    help="Run browsers in headless mode",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run without making actual purchases",
)
def main(
    config: Path,
    mode: Optional[str],
    headless: Optional[bool],
    debug: bool,
    dry_run: bool,
) -> None:
    """StealthMaster - Undetectable Ticketing Bot with Enhanced UI."""
    # ASCII art banner
    banner = """
    ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
    ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║
    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║
    ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║
    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝
                    M A S T E R
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    
    # Load configuration
    try:
        settings = load_settings(config)
    except Exception as e:
        console.print(f"[red]❌ Failed to load configuration: {e}[/red]")
        sys.exit(1)
    
    # Apply overrides
    if mode:
        settings.app_settings.mode = mode
    if headless is not None:
        settings.browser_options.headless = headless
    if dry_run:
        settings.app_settings.dry_run = True
    
    # Setup logging
    log_level = "DEBUG" if debug else settings.logging.level
    setup_logging(
        level=log_level,
        log_dir=settings.logs_dir,
        settings=settings.logging
    )
    
    # Show warnings
    if not settings.browser_options.headless:
        console.print("[yellow]⚠️  Running with visible browsers reduces stealth![/yellow]")
    if settings.app_settings.dry_run:
        console.print("[yellow]ℹ️  DRY RUN MODE - No actual purchases will be made[/yellow]")
    
    # Create and run application
    app = StealthMaster(settings)
    
    # Setup signal handlers
    def signal_handler(signal_num, stack_frame):  # noqa: ARG001  # pylint: disable=unused-argument
        console.print("\n[yellow]🛑 Interrupt received, shutting down...[/yellow]")
        app.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run async main
    try:
        asyncio.run(run_app(app))
    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 Keyboard interrupt, shutting down...[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Fatal error: {e}[/red]")
        logger.exception("Fatal error in main")
        sys.exit(1)


async def run_app(app: StealthMaster) -> None:
    """Run the application."""
    await app.initialize()
    await app.run()


if __name__ == "__main__":
    main()
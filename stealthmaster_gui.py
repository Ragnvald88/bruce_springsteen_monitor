#!/usr/bin/env python3
"""
StealthMaster GUI - Main entry point with UI on main thread for macOS compatibility
"""

import sys
import asyncio
import threading
import platform
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import StealthMaster, load_settings, setup_logging, console
from src.ui.enhanced_dashboard import EnhancedDashboard
import click


class StealthMasterGUI:
    """Wrapper to run UI on main thread and async operations in background"""
    
    def __init__(self, settings):
        self.settings = settings
        self.app = None
        self.dashboard = None
        self.async_thread = None
        self.loop = None
        
    def run(self):
        """Run the application with UI on main thread"""
        # Start async operations in background thread
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._run_async, daemon=True)
        self.async_thread.start()
        
        # Give async thread time to initialize
        import time
        time.sleep(2)
        
        # Run UI on main thread (required for macOS)
        try:
            self.dashboard = EnhancedDashboard()
            self.dashboard.parent.protocol("WM_DELETE_WINDOW", self._on_close)
            console.print("[cyan]📊 Dashboard opened in main window[/cyan]")
            self.dashboard.run()
        except Exception as e:
            console.print(f"[red]❌ UI Error: {e}[/red]")
            
    def _run_async(self):
        """Run async operations in background thread"""
        asyncio.set_event_loop(self.loop)
        
        # Create app without UI (we handle UI separately)
        self.app = StealthMaster(self.settings)
        self.app.dashboard = self.dashboard  # Connect to our dashboard
        
        # Run async initialization and main loop
        self.loop.run_until_complete(self._async_main())
        
    async def _async_main(self):
        """Async main operations"""
        await self.app.initialize()
        # Don't launch UI again - we already did it on main thread
        self.app._launch_ui = lambda: None  # Disable the UI launch in initialize
        
        await self.app.run()
        
    def _on_close(self):
        """Handle window close"""
        if self.app:
            self.app.running = False
        if self.dashboard:
            self.dashboard.parent.quit()
        

@click.command()
@click.option(
    "-c",
    "--config",
    type=Path,
    default=Path("config.yaml"),
    help="Path to configuration file",
)
@click.option(
    "-m",
    "--mode",
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
    mode: str,
    headless: bool,
    debug: bool,
    dry_run: bool,
) -> None:
    """StealthMaster GUI - Ticketing Bot with Enhanced Dashboard"""
    
    # ASCII art banner
    banner = """
    ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
    ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║
    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║
    ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║
    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝
                    M A S T E R   G U I
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
    
    # Check platform
    if platform.system() == "Darwin":
        console.print("[cyan]ℹ️  macOS detected - Running UI on main thread[/cyan]")
    
    # Create and run application with GUI
    gui_app = StealthMasterGUI(settings)
    gui_app.run()


if __name__ == "__main__":
    main()
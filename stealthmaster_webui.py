#!/usr/bin/env python3
"""
StealthMaster Web UI - Browser-based dashboard that works on all platforms
"""

import sys
import asyncio
import threading
import webbrowser
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import StealthMaster, load_settings, setup_logging, console
from src.ui.mobile_interface import create_web_app
from flask_socketio import SocketIO
import click


class StealthMasterWebUI:
    """Web-based UI that works on all platforms"""
    
    def __init__(self, settings):
        self.settings = settings
        self.app = None
        self.web_app = None
        self.socketio = None
        self.async_thread = None
        self.loop = None
        
    def run(self):
        """Run the application with web UI"""
        # Start async operations in background thread
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._run_async, daemon=True)
        self.async_thread.start()
        
        # Give async thread time to initialize
        import time
        time.sleep(2)
        
        # Create and run web UI
        self._run_web_ui()
        
    def _run_async(self):
        """Run async operations in background thread"""
        asyncio.set_event_loop(self.loop)
        
        # Create app
        self.app = StealthMaster(self.settings)
        
        # Run async initialization and main loop
        self.loop.run_until_complete(self._async_main())
        
    async def _async_main(self):
        """Async main operations"""
        # Initialize without launching tkinter UI
        await self.app.initialize()
        self.app._launch_ui = lambda: None  # Disable tkinter UI
        
        # Connect web UI events
        self._setup_web_events()
        
        await self.app.run()
        
    def _run_web_ui(self):
        """Run Flask web UI"""
        from flask import Flask, render_template_string, jsonify
        
        self.web_app = Flask(__name__)
        self.socketio = SocketIO(self.web_app, cors_allowed_origins="*")
        
        # Simple dashboard template
        dashboard_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>StealthMaster Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #0a0a0a;
                    color: #fff;
                    margin: 0;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                }
                .logo {
                    font-size: 48px;
                    font-weight: bold;
                    background: linear-gradient(45deg, #00ff88, #00aaff);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                .status {
                    padding: 20px;
                    background: #1a1a1a;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                .stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .stat-card {
                    background: #1a1a1a;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }
                .stat-value {
                    font-size: 36px;
                    font-weight: bold;
                    color: #00ff88;
                }
                .stat-label {
                    color: #888;
                    margin-top: 5px;
                }
                .logs {
                    background: #1a1a1a;
                    padding: 20px;
                    border-radius: 10px;
                    max-height: 400px;
                    overflow-y: auto;
                }
                .log-entry {
                    padding: 10px;
                    border-bottom: 1px solid #333;
                    font-family: monospace;
                    font-size: 14px;
                }
                .log-entry.success { color: #00ff88; }
                .log-entry.error { color: #ff4444; }
                .log-entry.warning { color: #ffaa00; }
                .log-entry.info { color: #00aaff; }
            </style>
            <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">STEALTHMASTER</div>
                    <div>Web Dashboard</div>
                </div>
                
                <div class="status">
                    <h2>System Status</h2>
                    <div id="status-text">Initializing...</div>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value" id="active-monitors">0</div>
                        <div class="stat-label">Active Monitors</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="tickets-found">0</div>
                        <div class="stat-label">Tickets Found</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="success-rate">0%</div>
                        <div class="stat-label">Success Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="uptime">0m</div>
                        <div class="stat-label">Uptime</div>
                    </div>
                </div>
                
                <div class="logs">
                    <h2>Activity Log</h2>
                    <div id="log-container"></div>
                </div>
            </div>
            
            <script>
                const socket = io();
                let startTime = Date.now();
                
                socket.on('connect', function() {
                    document.getElementById('status-text').textContent = 'Connected to StealthMaster';
                    addLog('Connected to dashboard', 'success');
                });
                
                socket.on('stats_update', function(data) {
                    document.getElementById('active-monitors').textContent = data.active_monitors || 0;
                    document.getElementById('tickets-found').textContent = data.tickets_found || 0;
                    document.getElementById('success-rate').textContent = (data.success_rate || 0) + '%';
                });
                
                socket.on('log_message', function(data) {
                    addLog(data.message, data.level);
                });
                
                function addLog(message, level = 'info') {
                    const container = document.getElementById('log-container');
                    const entry = document.createElement('div');
                    entry.className = 'log-entry ' + level;
                    const time = new Date().toLocaleTimeString();
                    entry.textContent = `[${time}] ${message}`;
                    container.insertBefore(entry, container.firstChild);
                    
                    // Keep only last 100 entries
                    while (container.children.length > 100) {
                        container.removeChild(container.lastChild);
                    }
                }
                
                // Update uptime
                setInterval(function() {
                    const uptime = Math.floor((Date.now() - startTime) / 60000);
                    document.getElementById('uptime').textContent = uptime + 'm';
                }, 1000);
                
                // Request initial stats
                socket.emit('get_stats');
            </script>
        </body>
        </html>
        '''
        
        @self.web_app.route('/')
        def index():
            return render_template_string(dashboard_html)
            
        @self.web_app.route('/api/stats')
        def get_stats():
            stats = {
                'active_monitors': len(self.app.monitors) if self.app else 0,
                'tickets_found': 0,  # Would come from stats_manager
                'success_rate': 0,
                'uptime': 0
            }
            return jsonify(stats)
            
        @self.socketio.on('connect')
        def handle_connect():
            console.print("[green]✅ Web dashboard connected[/green]")
            
        @self.socketio.on('get_stats')
        def handle_get_stats():
            if self.app:
                stats = {
                    'active_monitors': len(self.app.monitors),
                    'tickets_found': 0,
                    'success_rate': 0
                }
                self.socketio.emit('stats_update', stats)
        
        # Open browser
        port = 5000
        console.print(f"[cyan]🌐 Starting web dashboard on http://localhost:{port}[/cyan]")
        webbrowser.open(f'http://localhost:{port}')
        
        # Run Flask app
        self.socketio.run(self.web_app, host='0.0.0.0', port=port, debug=False)
        
    def _setup_web_events(self):
        """Connect app events to web UI"""
        # This would connect the app's events to emit socket.io messages
        pass


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
    """StealthMaster Web UI - Browser-based Dashboard"""
    
    # ASCII art banner
    banner = """
    ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
    ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║
    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║
    ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║
    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝
                    W E B   U I
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
    
    # Create and run application with web UI
    web_app = StealthMasterWebUI(settings)
    web_app.run()


if __name__ == "__main__":
    main()
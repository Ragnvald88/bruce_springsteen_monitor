#!/usr/bin/env python3
"""StealthMaster - Automated Ticket Monitoring System with Browser Reuse."""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import random
import logging
import json
import time
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Auto-detect Chrome path
def get_chrome_path():
    """Auto-detect Chrome/Chromium path across different OS."""
    paths = [
        # macOS
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        # Linux
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        # Windows
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    # Check if chrome is in PATH
    import shutil
    chrome_in_path = shutil.which('google-chrome') or shutil.which('chromium')
    if chrome_in_path:
        return chrome_in_path
    
    return None

# Set Chrome path if found
chrome_path = get_chrome_path()
if chrome_path:
    os.environ['CHROME_PATH'] = chrome_path
else:
    print("[yellow]⚠️  Chrome/Chromium not found. Please install Chrome or set CHROME_PATH environment variable.[/yellow]")

from rich.console import Console
from rich.table import Table, box
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
from src.utils.notifications import notification_manager
from src.utils.config_validator import ConfigValidator
from src.utils.retry_manager import retry_manager, with_retry
from src.stealth.akamai_bypass import AkamaiBypass
from src.stealth.ultimate_bypass import UltimateAkamaiBypass, StealthMasterBot
from src.telemetry.data_tracker import DataUsageTracker
from src.detection.ticket_detector import TicketDetector
# ADDED: New imports for enhancements
from src.utils.session_manager import session_manager
from src.orchestration.purchase import purchase_engine
from src.telemetry.history_tracker import history_tracker
# ADDED: Request scheduler for rate limit management
from src.network.request_scheduler import request_scheduler

console = Console()
logger = get_logger(__name__)


class StealthMasterUI:
    """StealthMaster with Browser Reuse and Session Management."""
    
    def __init__(self, settings):
        self.settings = settings
        self.running = False
        self.monitors = {}
        self.browsers = {}  # Store browser instances for reuse
        self.start_time = datetime.now()
        
        # Check for ultimate mode
        self.ultimate_mode = getattr(settings.app_settings, 'ultimate_mode', False)
        self.ultimate_bot = None
        
        # Core components
        self.profile_manager = ProfileManager(settings)
        # Update launcher with settings
        launcher.settings = settings
        launcher._configure_proxies()
        self.browser_launcher = launcher
        
        # Initialize data tracker
        self.data_tracker = DataUsageTracker()
        
        # Initialize ticket detector
        self.ticket_detector = TicketDetector()
        
        # Stats
        self.monitor_status = {}
        self.last_check = {}
        self.tickets_found = 0
        self.tickets_reserved = 0
        self.tickets_failed = 0
        self.access_denied_count = 0
        
        # Session
        self.session_id = f"ui_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        stats_manager.start_session(self.session_id)
        
        # ADDED: Initialize history tracker with session
        history_tracker.set_session_id(self.session_id)
    
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
        active_count = len([s for s in self.monitor_status.values() if "Active" in str(s) or "Checking" in str(s)])
        
        table.add_row("⏱️  Uptime", uptime)
        table.add_row("📡 Active Monitors", str(active_count))
        table.add_row("🎫 Tickets Found", str(self.tickets_found))
        table.add_row("✅ Reserved", str(self.tickets_reserved))
        table.add_row("❌ Failed", str(self.tickets_failed))
        
        if self.access_denied_count > 0:
            table.add_row("🚫 Access Denied", str(self.access_denied_count), style="red")
        
        # Calculate success rate
        total_attempts = self.tickets_reserved + self.tickets_failed
        if total_attempts > 0:
            success_rate = (self.tickets_reserved / total_attempts) * 100
        else:
            success_rate = 0.0
        table.add_row("📈 Success Rate", f"{success_rate:.1f}%")
        
        # Browser count
        table.add_row("🌐 Browsers Open", str(len(self.browsers)))
        
        # Show mode
        mode_text = "🔥 Ultimate" if self.ultimate_mode else "🛡️ Standard"
        table.add_row("⚡ Mode", mode_text)
        
        # Data usage stats
        data_summary = self.data_tracker.get_summary()
        table.add_row("📊 Data Used", f"{data_summary['total_data_mb']:.1f} MB")
        
        # Efficiency score (average across platforms)
        efficiency_scores = [p['efficiency_score'] for p in data_summary['platforms'].values()]
        avg_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 100
        table.add_row("⚡ Efficiency", f"{avg_efficiency:.0f}%")
        
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
    
    # ADDED: Create history panel with ticket categorization
    def create_history_panel(self) -> Panel:
        """Create detailed history panel with ticket categories"""
        history_data = history_tracker.get_formatted_history()
        
        # Create main table
        table = Table(title="📊 Ticket Detection History", box=box.ROUNDED)
        table.add_column("Platform", style="cyan", width=12)
        table.add_column("Total", style="white", width=8)
        table.add_column("Prato A", style="green", width=10)
        table.add_column("Prato B", style="yellow", width=10)
        table.add_column("Seating", style="blue", width=10)
        table.add_column("Avg Conf", style="dim", width=8)
        
        for platform, stats in history_data.items():
            if platform == 'session_totals':
                continue
                
            table.add_row(
                platform.title(),
                str(stats['total_detections']),
                f"🎫 {stats.get('prato_a', 0)}",
                f"🎫 {stats.get('prato_b', 0)}",
                f"💺 {stats.get('seating', 0)}",
                f"{stats['avg_confidence']:.0%}"
            )
        
        # Add session summary below
        session_summary = Text()
        session_summary.append(f"\n📅 Session: {self.session_id}\n", style="dim")
        session_summary.append(f"⏱️  Duration: {str(datetime.now() - self.start_time).split('.')[0]}\n")
        
        # Add current session stats
        if 'session_totals' in history_data:
            session_summary.append("\n🔥 Current Session Detections:\n", style="bold")
            for platform, categories in history_data['session_totals'].items():
                total = sum(categories.values())
                if total > 0:
                    session_summary.append(f"  {platform}: {total} detections\n", style="cyan")
        
        layout = Layout()
        layout.split_column(
            Layout(table),
            Layout(Panel(session_summary, style="dim"), size=6)
        )
        
        return Panel(layout, title="📈 Analytics Dashboard", style="blue")
    
    def create_layout(self) -> Layout:
        """Create the complete dashboard layout."""
        layout = Layout()
        
        # Create the layout structure
        layout.split_column(
            Layout(self.create_header(), size=3, name="header"),
            Layout(name="body"),
            Layout(name="footer", size=5)
        )
        
        # MODIFIED: Split body into three sections
        layout["body"].split_column(
            Layout(name="top_row", size=10),
            Layout(name="bottom_row", size=12)
        )
        
        # Top row: stats and monitors
        layout["body"]["top_row"].split_row(
            Layout(self.create_stats_panel(), name="stats", ratio=1),
            Layout(self.create_monitors_panel(), name="monitors", ratio=2)
        )
        
        # Bottom row: history panel
        layout["body"]["bottom_row"].update(self.create_history_panel())
        
        # Add instructions to footer
        instructions = Panel(
            "[yellow]Press Ctrl+C to stop monitoring[/yellow]\n"
            "[cyan]Monitors check every 30 seconds (5s burst mode when tickets found)[/cyan]\n"
            f"[dim]Session ID: {self.session_id}[/dim]\n"
            "[red]Note: Using ONE browser per platform to avoid detection[/red]",
            title="ℹ️  Instructions",
            style="dim"
        )
        layout["footer"].update(instructions)
        
        return layout
    
    @with_retry(max_retries=3, base_delay=2.0)
    async def get_or_create_browser(self, platform_name: str):
        """Get existing browser or create new one for platform."""
        if platform_name not in self.browsers:
            console.print(f"[cyan]🌐 Creating browser for {platform_name}...[/cyan]")
            try:
                # Get proxy settings for this platform
                proxy_config = None
                if self.settings.proxy_settings.enabled:
                    proxy_config = self._get_proxy_for_platform(platform_name)
                
                browser_data = await self.browser_launcher.launch_browser(proxy=proxy_config)
                self.browsers[platform_name] = {
                    'id': browser_data,
                    'page': None,
                    'context': None,
                    'last_used': datetime.now(),
                    'request_count': 0,
                    'health_check_fails': 0
                }
                console.print(f"[green]✓ Browser created for {platform_name}[/green]")
            except Exception as e:
                console.print(f"[red]✗ Failed to create browser for {platform_name}: {e}[/red]")
                raise
        
        return self.browsers[platform_name]['id']
    
    def _get_proxy_for_platform(self, platform_name: str):
        """Get proxy configuration for a specific platform."""
        if not self.settings.proxy_settings.primary_pool:
            console.print("[yellow]⚠️ No proxy configured - using direct connection[/yellow]")
            return None
        
        # For now, use the first proxy in the pool
        # TODO: Implement proper proxy rotation
        proxy = self.settings.proxy_settings.primary_pool[0]
        
        # Convert proxy settings to browser format - DO NOT include auth in URL
        proxy_url = f"{proxy.type}://{proxy.host}:{proxy.port}"
        
        console.print(f"[cyan]🌐 Using proxy: {proxy.host}:{proxy.port} (user: {proxy.username})[/cyan]")
        
        return {
            'server': proxy_url,
            'username': proxy.username,
            'password': proxy.password
        }
    
    async def monitor_target(self, target):
        """Monitor a single target with browser reuse."""
        # Normalize platform name
        platform_name = target.platform.value.lower() if hasattr(target.platform, 'value') else str(target.platform).lower()
        
        # Get or create browser for this platform
        try:
            browser_id = await self.get_or_create_browser(platform_name)
        except Exception as e:
            self.monitor_status[target.event_name] = "❌ Browser Error"
            logger.error(f"Failed to get browser for {target.event_name}: {e}")
            return
        
        # Create persistent page/tab for this monitor
        page = None
        first_run = True
        
        while self.running:
            try:
                self.monitor_status[target.event_name] = "🔄 Checking"
                
                # ADDED: Check rate limits before making request
                wait_time = await request_scheduler.wait_if_needed(platform_name)
                if wait_time > 0:
                    self.monitor_status[target.event_name] = f"⏳ Rate limit wait ({wait_time:.0f}s)"
                
                # Create page if needed (reuse existing browser)
                if page is None:
                    try:
                        context_id = await self.browser_launcher.create_context(browser_id)
                        page = await self.browser_launcher.new_page(context_id)
                        
                        # Store page reference for cleanup
                        self.browsers[platform_name]['page'] = page
                        self.browsers[platform_name]['context_id'] = context_id
                        
                        if first_run:
                            console.print(f"[green]📄 Created dedicated tab for {target.event_name}[/green]")
                            
                            # FIXED: Load cookies BEFORE navigating to save bandwidth
                            if self.settings.authentication.enabled:
                                platform_auth = getattr(self.settings.authentication.platforms, platform_name, None)
                                if platform_auth:
                                    credentials = {
                                        'username': platform_auth.username,
                                        'password': platform_auth.password
                                    }
                                    console.print(f"[cyan]🔐 Loading saved session for {platform_name}...[/cyan]")
                                    
                                    # Try to load existing cookies first
                                    cookie_file = Path(f"data/cookies/{platform_name}_cookies.json")
                                    if cookie_file.exists():
                                        try:
                                            import json
                                            with open(cookie_file, 'r') as f:
                                                cookies = json.load(f)
                                            
                                            # For Selenium, we need to navigate to domain first
                                            base_urls = {
                                                'fansale': 'https://www.fansale.it',
                                                'ticketmaster': 'https://www.ticketmaster.it',
                                                'vivaticket': 'https://www.vivaticket.com'
                                            }
                                            
                                            if platform_name in base_urls:
                                                page.get(base_urls[platform_name])
                                                await asyncio.sleep(2)
                                                
                                                # Add cookies
                                                for cookie in cookies:
                                                    try:
                                                        # Selenium needs specific format
                                                        if 'sameSite' in cookie:
                                                            cookie['sameSite'] = 'Strict'
                                                        page.add_cookie(cookie)
                                                    except Exception as e:
                                                        logger.debug(f"Cookie error: {e}")
                                                
                                                console.print(f"[green]✓ Loaded {len(cookies)} saved cookies for {platform_name}[/green]")
                                        except Exception as e:
                                            logger.error(f"Failed to load cookies: {e}")
                            
                            # Apply selective resource blocking for Selenium
                            if hasattr(page, 'execute_cdp_cmd'):
                                from src.browser.resource_blocker import apply_selective_blocking
                                apply_selective_blocking(page)
                            
                            # Apply Akamai bypass for platforms that need it
                            if platform_name in ['ticketmaster', 'ticketone', 'fansale']:
                                console.print(f"[cyan]🛡️ Applying Akamai bypass for {platform_name}[/cyan]")
                                await AkamaiBypass.apply_bypass(page)
                            
                            # Check IP to verify proxy (optional, can be disabled for speed)
                            if self.settings.proxy_settings.enabled:
                                try:
                                    if hasattr(page, "goto"):
                                        await page.goto("https://httpbin.org/ip", wait_until='domcontentloaded', timeout=10000)
                                        ip_data = await page.evaluate("() => document.body.textContent")
                                    else:
                                        page.get("https://httpbin.org/ip")
                                        await asyncio.sleep(1)
                                        ip_data = page.execute_script("return document.body.textContent")
                                    
                                    import json
                                    ip_info = json.loads(ip_data)
                                    console.print(f"[cyan]🌍 Current IP: {ip_info.get('origin', 'Unknown')}[/cyan]")
                                except Exception as e:
                                    console.print(f"[yellow]⚠️ Could not verify IP: {e}[/yellow]")
                            
                            first_run = False
                    except Exception as e:
                        logger.error(f"Failed to create page for {target.event_name}: {e}")
                        # Mark browser as potentially broken
                        self.browsers[platform_name]['broken'] = True
                        return
                
                # Navigate to URL with retry
                url = str(target.url)
                
                try:
                    # MODIFIED: Use smart check for minimal data usage
                    if hasattr(page, "goto"):
                        # First time or cache expired - do full navigation
                        cache_key = f"{platform_name}:{url}"
                        should_full_load = cache_key not in self.data_tracker.request_cache
                        
                        if should_full_load:
                            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                            
                            # Reset health check counter on successful navigation
                            self.browsers[platform_name]['health_check_fails'] = 0
                            
                            # ADDED: Record request for rate limiting
                            request_scheduler.record_request(platform_name)
                            
                            # Check for access denied
                            if response and response.status == 403:
                                self.access_denied_count += 1
                                self.monitor_status[target.event_name] = "🚫 Access Denied"
                                console.print(f"[red]🚫 Access denied for {target.event_name}![/red]")
                                
                                # Implement exponential backoff
                                backoff_time = min(300, 60 * (2 ** min(self.browsers[platform_name].get('block_count', 0), 5)))
                                self.browsers[platform_name]['block_count'] = self.browsers[platform_name].get('block_count', 0) + 1
                                
                                console.print(f"[yellow]⏳ Backing off for {backoff_time}s...[/yellow]")
                                await asyncio.sleep(backoff_time)
                                
                                # Consider rotating proxy or browser
                                if self.browsers[platform_name].get('block_count', 0) >= 3:
                                    console.print(f"[yellow]🔄 Too many blocks, recreating browser for {platform_name}[/yellow]")
                                    await self._close_browser(platform_name)
                                    self.browsers.pop(platform_name, None)
                                
                                continue
                        else:
                            # Use smart check for subsequent checks
                            console.print(f"[dim]Using optimized check for {target.event_name}[/dim]", end="\r")
                    else:
                        page.get(url)
                        await asyncio.sleep(2)
                        self.browsers[platform_name]['health_check_fails'] = 0
                except Exception as nav_error:
                    logger.error(f"Navigation error for {target.event_name}: {nav_error}")
                    self.browsers[platform_name]['health_check_fails'] = self.browsers[platform_name].get('health_check_fails', 0) + 1
                    
                    # If too many failures, recreate browser
                    if self.browsers[platform_name]['health_check_fails'] >= 3:
                        console.print(f"[yellow]🔧 Browser health check failed, recreating for {platform_name}[/yellow]")
                        await self._close_browser(platform_name)
                        self.browsers.pop(platform_name, None)
                        page = None
                    
                    await asyncio.sleep(10)
                    continue
                
                self.monitor_status[target.event_name] = "🟢 Active"
                self.last_check[target.event_name] = datetime.now()
                
                # ADDED: Save cookies periodically for session persistence
                if hasattr(page, 'get_cookies'):
                    cookies = page.get_cookies()
                    if cookies and len(cookies) > 5:  # Only save if we have meaningful cookies
                        cookie_file = Path(f"data/cookies/{platform_name}_cookies.json")
                        cookie_file.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            with open(cookie_file, 'w') as f:
                                json.dump(cookies, f)
                            logger.debug(f"Saved {len(cookies)} cookies for {platform_name}")
                        except Exception as e:
                            logger.debug(f"Cookie save error: {e}")
                
                # Check page content for access denied
                try:
                    content = await page.content() if hasattr(page, 'content') else page.page_source
                    content_lower = content.lower()
                    
                    # Check for various blocking indicators
                    if any(indicator in content_lower for indicator in [
                        'access denied', 'blocked', 'forbidden', 
                        'edgesuite.net', 'akamai', '_abck'
                    ]):
                        self.access_denied_count += 1
                        self.monitor_status[target.event_name] = "🚫 Blocked"
                        console.print(f"[red]🚫 Blocked on {target.event_name}![/red]")
                        
                        # Try Akamai challenge handler
                        if '_abck' in content or 'akamai' in content_lower:
                            console.print(f"[yellow]🛡️ Attempting Akamai challenge bypass...[/yellow]")
                            success = await AkamaiBypass.handle_challenge(page)
                            if success:
                                console.print(f"[green]✓ Challenge bypass attempted[/green]")
                                await asyncio.sleep(5)  # Give it time to work
                                continue
                        
                        await asyncio.sleep(60)
                        continue
                except:
                    pass
                
                # MODIFIED: Use smart check for data optimization
                ticket_data = await self.data_tracker.smart_check(page, url, platform_name)
                
                # Get page content for detection (only if needed)
                if ticket_data and ticket_data.get('hasTickets'):
                    # We have tickets, get more details for detection
                    content = await page.content() if hasattr(page, 'content') else page.page_source
                else:
                    # Use minimal content from smart check
                    content = json.dumps(ticket_data)
                
                # Use enhanced ticket detector
                detection_result = await self.ticket_detector.detect_tickets(page, platform_name, content)
                
                if detection_result['tickets_found']:
                    self.tickets_found += 1
                    confidence = detection_result['confidence']
                    ticket_count = detection_result.get('ticket_count', 1)
                    
                    self.monitor_status[target.event_name] = f"🎯 Tickets found! ({confidence:.0%})"
                    console.print(f"[green]🎫 Tickets detected on {target.event_name}![/green]")
                    console.print(f"  Detection confidence: {confidence:.0%}")
                    console.print(f"  Ticket count: {ticket_count}")
                    console.print(f"  Recommendation: {detection_result['recommendation']}")
                    
                    # ADDED: Record detection in history tracker
                    await history_tracker.record_detection(
                        platform=platform_name,
                        event=target.event_name,
                        page_content=content,
                        confidence=confidence,
                        ticket_details=detection_result.get('details', {})
                    )
                    
                    # Show detection details in debug mode
                    if logger.isEnabledFor(logging.DEBUG):
                        console.print(f"  Detection details: {detection_result['details']}")
                    
                    stats_manager.record_ticket_found(
                        platform_name,
                        target.event_name,
                        "general",
                        int(confidence * 1000)
                    )
                    
                    # Send notification with confidence level
                    await notification_manager.send_ticket_alert(
                        platform=platform_name,
                        event_name=target.event_name,
                        ticket_count=ticket_count,
                        url=url,
                        confidence=confidence
                    )
                    
                    # ADDED: Attempt automatic purchase if confidence is high
                    if confidence >= 0.7 and not self.settings.app_settings.dry_run:
                        console.print(f"[yellow]🛒 Attempting automatic purchase...[/yellow]")
                        
                        purchase_result = await purchase_engine.handle_ticket_detection(
                            page=page,
                            platform=platform_name,
                            detection_result=detection_result
                        )
                        
                        if purchase_result and purchase_result.success:
                            self.tickets_reserved += purchase_result.tickets_purchased
                            console.print(f"[green]🎉 Purchase successful! Order: {purchase_result.order_id}[/green]")
                        elif purchase_result:
                            self.tickets_failed += 1
                            console.print(f"[red]❌ Purchase failed: {purchase_result.error}[/red]")
                    
                    # Switch to burst mode (5 second intervals) for high confidence
                    if confidence >= 0.8:
                        base_interval = 5
                        console.print(f"[yellow]⚡ Burst mode activated for {target.event_name}[/yellow]")
                    else:
                        base_interval = 10  # Slower for lower confidence
                    
                    # Wait a bit to show the status
                    await asyncio.sleep(3)
                else:
                    # Log that we're still searching with data usage info
                    data_summary = self.data_tracker.get_summary()
                    platform_data = data_summary['platforms'].get(platform_name, {})
                    console.print(f"[dim]Searching {target.event_name}... (Data: {platform_data.get('data_mb', 0):.1f}MB)[/dim]", end="\r")
                
                # Implement adaptive rate limiting
                self.browsers[platform_name]['request_count'] = self.browsers[platform_name].get('request_count', 0) + 1
                
                # MODIFIED: Use request scheduler for intelligent intervals
                base_interval = target.interval_s
                dynamic_interval = request_scheduler.get_optimal_interval(platform_name, base_interval)
                
                # Additional adjustments for blocks
                block_count = self.browsers[platform_name].get('block_count', 0)
                if block_count > 0:
                    dynamic_interval *= (1 + (block_count * 0.5))
                
                # Wait for next check
                await asyncio.sleep(dynamic_interval)
                
            except Exception as e:
                self.monitor_status[target.event_name] = f"⚠️  Error"
                logger.error(f"Monitor error for {target.event_name}: {e}")
                
                # Close broken page
                if page:
                    try:
                        if hasattr(page, 'close'):
                            await page.close()
                    except:
                        pass
                    page = None
                
                await asyncio.sleep(10)  # Wait before retry
        
        # Cleanup on exit
        if page:
            try:
                if hasattr(page, 'close'):
                    await page.close()
            except:
                pass
    
    async def monitor_target_ultimate(self, target):
        """Monitor a single target using ultimate bypass mode."""
        platform_name = target.platform.value.lower() if hasattr(target.platform, 'value') else str(target.platform).lower()
        
        # Initialize ultimate bot if not already done
        if not self.ultimate_bot:
            console.print("[cyan]🔥 Initializing Ultimate Bypass Mode...[/cyan]")
            self.ultimate_bot = StealthMasterBot()
        
        # Get proxy configuration
        proxy = None
        # TODO: Implement proxy support for ultimate mode
        # For now, ultimate mode runs without proxy
        if False and self.settings.proxy_settings.enabled and self.settings.proxy_settings.primary_pool:
            proxy_config = self.settings.proxy_settings.primary_pool[0]
            proxy = {
                'host': proxy_config.host,
                'port': proxy_config.port,
                'username': proxy_config.username,
                'password': proxy_config.password
            }
        
        while self.running:
            try:
                self.monitor_status[target.event_name] = "🔄 Checking"
                
                # Get page using ultimate stealth
                page = await self.ultimate_bot.get_page(
                    str(target.url),
                    profile=f"{platform_name}_{target.event_name.replace(' ', '_')}",
                    proxy=proxy
                )
                
                self.monitor_status[target.event_name] = "🟢 Active"
                self.last_check[target.event_name] = datetime.now()
                
                # Get page content
                content = await page.content()
                response_size = len(content)
                
                # Use enhanced ticket detector
                detection_result = await self.ticket_detector.detect_tickets(page, platform_name, content)
                
                # Track data usage
                await self.data_tracker.track_request(
                    platform=platform_name,
                    url=str(target.url),
                    response_size=response_size,
                    blocked_resources={'images': 0, 'scripts': 0}  # Ultimate mode doesn't block resources
                )
                
                if detection_result['tickets_found']:
                    self.tickets_found += 1
                    confidence = detection_result['confidence']
                    ticket_count = detection_result.get('ticket_count', 1)
                    
                    self.monitor_status[target.event_name] = f"🎯 Tickets found! ({confidence:.0%})"
                    console.print(f"[green]🎫 Tickets detected on {target.event_name}![/green]")
                    console.print(f"  [Ultimate Mode] Confidence: {confidence:.0%}")
                    
                    # Send notification
                    await notification_manager.send_ticket_alert(
                        platform=platform_name,
                        event_name=target.event_name,
                        ticket_count=ticket_count,
                        url=str(target.url),
                        confidence=confidence
                    )
                    
                    # Burst mode
                    await asyncio.sleep(5)
                else:
                    await asyncio.sleep(target.interval_s)
                    
            except Exception as e:
                self.monitor_status[target.event_name] = f"⚠️  Error"
                logger.error(f"Ultimate monitor error for {target.event_name}: {e}")
                await asyncio.sleep(10)
    
    async def run(self):
        """Run the monitoring with live UI."""
        self.running = True
        
        # Initialize
        console.print("[yellow]🚀 Initializing StealthMaster...[/yellow]")
        await self.profile_manager.load_all_profiles()
        
        # Start data usage monitoring
        await self.data_tracker.start_monitoring()
        console.print("[cyan]📊 Data usage monitoring enabled[/cyan]")
        
        # Important notice about proxies
        if not self.settings.proxy_settings.enabled:
            console.print("[yellow]⚠️  Proxies are DISABLED - you may get blocked![/yellow]")
            console.print("[cyan]   Enable proxies in config.yaml for better protection[/cyan]")
        
        # Skip stealth test to avoid extra browser
        console.print("[cyan]🔍 Stealth mode enabled[/cyan]")
        console.print()
        
        # Start monitors
        tasks = []
        enabled_count = 0
        for target in self.settings.targets:
            if target.enabled:
                enabled_count += 1
                task = asyncio.create_task(
                    self.monitor_target_ultimate(target) if self.ultimate_mode else self.monitor_target(target)
                )
                self.monitors[target.event_name] = task
                tasks.append(task)
                console.print(f"[green]✓[/green] Starting monitor for {target.event_name}")
        
        if enabled_count == 0:
            console.print("[red]❌ No monitors enabled! Check your config.yaml[/red]")
            return
        
        console.print(f"\n[cyan]📡 {enabled_count} monitors starting with browser reuse...[/cyan]")
        console.print(f"[yellow]🌐 Creating {len(set(t.platform.value.lower() if hasattr(t.platform, 'value') else str(t.platform).lower() for t in self.settings.targets if t.enabled))} browsers total (one per platform)[/yellow]\n")
        
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
        
        # Cancel monitor tasks
        for task in tasks:
            task.cancel()
        
        # Stop data monitoring
        await self.data_tracker.stop_monitoring()
        
        # Close all browsers
        console.print("[yellow]🌐 Closing browsers...[/yellow]")
        
        # Ultimate mode cleanup
        if self.ultimate_bot:
            console.print("[yellow]🔥 Closing ultimate mode sessions...[/yellow]")
            await self.ultimate_bot.cleanup()
        else:
            # Standard mode cleanup
            for platform_name in list(self.browsers.keys()):
                await self._close_browser(platform_name)
            await self.browser_launcher.close_all()
        
        # Generate and display data usage report
        console.print("\n[cyan]📊 Data Usage Report:[/cyan]")
        report = await self.data_tracker.generate_report()
        for line in report.split('\n'):
            console.print(f"  {line}")
        
        # ADDED: Display detection analytics
        console.print("\n[cyan]📈 Detection Analytics:[/cyan]")
        analytics = history_tracker.get_detection_analytics()
        
        if analytics.get('total_detections', 0) > 0:
            console.print(f"  Total Detections: {analytics['total_detections']}")
            console.print(f"  Platform Breakdown:")
            for platform, data in analytics['platforms'].items():
                console.print(f"    - {platform}: {data['count']} ({data['percentage']:.1f}%)")
            
            console.print(f"  Category Distribution:")
            for category, count in analytics['categories'].items():
                console.print(f"    - {category}: {count}")
            
            if analytics.get('time_analysis', {}).get('peak_hours'):
                peak_hours = ', '.join([f"{h}:00" for h in analytics['time_analysis']['peak_hours']])
                console.print(f"  Peak Detection Hours: {peak_hours}")
            
            if analytics.get('recommendations'):
                console.print(f"  Recommendations:")
                for rec in analytics['recommendations']:
                    console.print(f"    • {rec}")
        
        # End session tracking
        stats_manager.end_session(self.session_id)
    
    async def _close_browser(self, platform_name: str):
        """Safely close a browser instance."""
        try:
            browser_info = self.browsers.get(platform_name)
            if browser_info:
                # Close any open pages
                if browser_info.get('page'):
                    try:
                        if hasattr(browser_info['page'], 'close'):
                            await browser_info['page'].close()
                        else:
                            browser_info['page'].quit()
                    except Exception as e:
                        logger.debug(f"Error closing page for {platform_name}: {e}")
                
                # Close context if exists
                if browser_info.get('context_id'):
                    try:
                        await self.browser_launcher.close_context(browser_info['context_id'])
                    except Exception as e:
                        logger.debug(f"Error closing context for {platform_name}: {e}")
                
                # Close browser
                if browser_info.get('id'):
                    try:
                        await self.browser_launcher.close_browser(browser_info['id'])
                    except Exception as e:
                        logger.debug(f"Error closing browser for {platform_name}: {e}")
                        
                # Remove from tracking
                self.browsers.pop(platform_name, None)
                
        except Exception as e:
            logger.error(f"Error during browser cleanup for {platform_name}: {e}")
        
        # Final stats
        console.print(f"\n[cyan]📊 Session Summary:[/cyan]")
        console.print(f"  Duration: {str(datetime.now() - self.start_time).split('.')[0]}")
        console.print(f"  Tickets Found: {self.tickets_found}")
        console.print(f"  Tickets Reserved: {self.tickets_reserved}")
        console.print(f"  Access Denied: {self.access_denied_count}")
        console.print(f"  Success Rate: {(self.tickets_reserved / max(1, self.tickets_reserved + self.tickets_failed)) * 100:.1f}%")
        
        # ADDED: Export history if significant detections
        if self.tickets_found > 0:
            export_file = history_tracker.export_history()
            console.print(f"\n[green]📁 History exported to: {export_file}[/green]")
        
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
    
    # ADDED: Ensure data directories exist
    Path("data").mkdir(exist_ok=True)
    Path("data/cookies").mkdir(exist_ok=True)
    
    # Validate configuration
    validator = ConfigValidator(settings)
    is_valid, errors, warnings = validator.validate()
    validator.print_validation_results()
    
    if not is_valid:
        console.print("\n[red]❌ Cannot start due to configuration errors![/red]")
        console.print("[yellow]Please fix the errors in config.yaml and try again.[/yellow]")
        return
    
    # Show active targets
    console.print("[cyan]🎯 Configured Targets:[/cyan]")
    active_count = 0
    platforms = set()
    for target in settings.targets:
        if target.enabled:
            active_count += 1
            platform = target.platform.value if hasattr(target.platform, 'value') else str(target.platform)
            platforms.add(platform.lower())
            console.print(f"  • {platform}: {target.event_name}")
    
    if active_count == 0:
        console.print("[red]  ❌ No targets enabled! Edit config.yaml to enable monitoring.[/red]")
        return
    
    console.print(f"\n[green]ℹ️  Will use {len(platforms)} browser(s) total (one per platform)[/green]")
    console.print()
    
    # Run UI
    ui = StealthMasterUI(settings)
    await ui.run()


if __name__ == "__main__":
    # Check if GUI mode is requested
    if "--gui" in sys.argv or os.environ.get('STEALTHMASTER_GUI'):
        # Launch GUI
        try:
            from src.ui.advanced_gui import main as gui_main
            gui_main()
        except ImportError as e:
            console.print(f"[red]❌ GUI dependencies not installed: {e}[/red]")
            console.print("[yellow]Install GUI dependencies with: pip install PySide6[/yellow]")
            sys.exit(1)
    else:
        # Run CLI mode
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Goodbye![/yellow]")
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            import traceback
            traceback.print_exc()
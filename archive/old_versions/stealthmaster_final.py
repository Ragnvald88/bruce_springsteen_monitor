#!/usr/bin/env python3
"""
StealthMaster Final - Complete working version with proxy
"""

import time
import asyncio
import random
from datetime import datetime
from pathlib import Path
import json
import base64
import zipfile
import os

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


def create_proxy_auth_extension(proxy_host, proxy_port, proxy_user, proxy_pass):
    """Create Chrome extension for proxy authentication"""
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
              },
              bypassList: ["localhost"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (proxy_host, proxy_port, proxy_user, proxy_pass)

    pluginfile = f'/tmp/proxy_auth_plugin_{random.randint(1000, 9999)}.zip'
    
    with zipfile.ZipFile(pluginfile, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    
    return pluginfile


class StealthMasterFinal:
    """Final working version with all features"""
    
    def __init__(self, use_proxy=True):
        self.running = False
        self.start_time = datetime.now()
        self.drivers = {}
        self.status = {}
        self.stats = {
            'checks': 0,
            'tickets_found': 0,
            'blocks': 0,
            'errors': 0,
            'proxy_working': False
        }
        self.use_proxy = use_proxy
        self.proxy_config = {
            'host': 'geo.iproyal.com',
            'port': '12321',
            'username': 'Doqe2Sm9Yjl1MrZd',
            'password': 'ZBWCB2RieYSFqNJe_country-it'
        }
        
    def create_stealth_driver(self, name):
        """Create Chrome driver with maximum stealth"""
        options = Options()
        
        # Stealth arguments
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance and stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-setuid-sandbox')
        
        # Additional stealth
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-site-isolation-trials')
        
        # Window size
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Block images and other resources to save data
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream": 2,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.idle_detection": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Add proxy if enabled
        if self.use_proxy:
            proxy_extension = create_proxy_auth_extension(
                self.proxy_config['host'],
                self.proxy_config['port'],
                self.proxy_config['username'],
                self.proxy_config['password']
            )
            options.add_extension(proxy_extension)
            console.print(f"[cyan]🌐 Using proxy for {name}[/cyan]")
        
        try:
            # Create driver with auto-downloaded chromedriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Enhanced stealth JavaScript
            stealth_js = """
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Fix Chrome object
            window.chrome = {
                runtime: {
                    connect: () => {},
                    sendMessage: () => {},
                    onMessage: { addListener: () => {} }
                },
                loadTimes: () => ({
                    requestTime: Date.now() / 1000,
                    startLoadTime: Date.now() / 1000
                })
            };
            
            // Fix plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const arr = [1, 2, 3, 4, 5];
                    arr.item = (i) => arr[i];
                    arr.namedItem = () => null;
                    arr.refresh = () => {};
                    return arr;
                }
            });
            
            // Fix languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'it-IT', 'it']
            });
            
            // Fix permissions
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (params) => (
                params.name === 'notifications' ?
                    Promise.resolve({ state: 'prompt' }) :
                    originalQuery(params)
            );
            
            // Fix WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            
            // Fix screen
            Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
            Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
            
            // Canvas fingerprint protection
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] = imageData.data[i] ^ 1;
                    imageData.data[i + 1] = imageData.data[i + 1] ^ 1;
                    imageData.data[i + 2] = imageData.data[i + 2] ^ 1;
                }
                context.putImageData(imageData, 0, 0);
                return toDataURL.apply(this, arguments);
            };
            """
            
            driver.execute_script(stealth_js)
            
            # Additional CDP commands for stealth
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
            
            return driver
            
        except Exception as e:
            console.print(f"[red]Failed to create driver for {name}: {e}[/red]")
            return None
    
    def dismiss_cookies(self, driver, name):
        """Enhanced cookie dismissal"""
        cookie_selectors = [
            # OneTrust (common on many sites)
            '#onetrust-accept-btn-handler',
            '#onetrust-pc-btn-handler',
            '.onetrust-close-btn-handler',
            
            # Generic accept buttons
            'button[id*="accept"]',
            'button[class*="accept"]',
            'button[aria-label*="accept" i]',
            'button[aria-label*="accetta" i]',
            
            # Text-based buttons
            'button:contains("Accept")',
            'button:contains("Accetta")',
            'button:contains("OK")',
            
            # Other common frameworks
            '.cookie-consent-accept',
            '.cookie-accept-button',
            '.accept-cookies',
            '#cookie-accept',
            '[data-testid="cookie-accept"]',
            '.iubenda-cs-accept-btn',
            
            # Platform specific
            '.js-accept-cookies',
            '.cookie-banner__cta',
            '.gdpr-accept'
        ]
        
        dismissed = False
        
        # Try CSS selectors
        for selector in cookie_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.5)
                        element.click()
                        console.print(f"[green]✓ Dismissed cookies on {name} with {selector}[/green]")
                        dismissed = True
                        break
            except:
                pass
            
            if dismissed:
                break
        
        # Try XPath as fallback
        if not dismissed:
            try:
                xpath_queries = [
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'consenti')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
                    "//a[contains(@class, 'accept')]",
                    "//div[@role='button' and contains(., 'Accept')]"
                ]
                
                for xpath in xpath_queries:
                    buttons = driver.find_elements(By.XPATH, xpath)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            driver.execute_script("arguments[0].click();", button)
                            console.print(f"[green]✓ Dismissed cookies on {name} (XPath)[/green]")
                            dismissed = True
                            break
                    
                    if dismissed:
                        break
                        
            except Exception as e:
                console.print(f"[yellow]Cookie XPath error: {e}[/yellow]")
        
        return dismissed
    
    def check_page(self, driver, url, name):
        """Enhanced page checking with better detection"""
        try:
            # Navigate
            driver.get(url)
            
            # Random delay to appear more human
            time.sleep(random.uniform(3, 5))
            
            # Try to dismiss cookies
            if f"{name}_cookies" not in self.status:
                if self.dismiss_cookies(driver, name):
                    self.status[f"{name}_cookies"] = True
                    time.sleep(2)
            
            # Get page info
            page_text = driver.page_source.lower()
            current_url = driver.current_url.lower()
            title = driver.title.lower()
            
            # Enhanced block detection
            block_indicators = [
                'access denied',
                'blocked',
                'forbidden',
                'bot detection',
                'security check',
                'verificando il browser',
                'verifica in corso',
                'checking your browser',
                'ddos protection',
                'ray id',
                'cloudflare'
            ]
            
            if any(indicator in page_text for indicator in block_indicators):
                self.stats['blocks'] += 1
                
                # Check if we can verify proxy is working
                if self.use_proxy and not self.stats.get('proxy_verified'):
                    self.verify_proxy(driver)
                
                return {'status': 'blocked', 'has_tickets': False}
            
            # Check for login redirect
            if any(word in current_url for word in ['login', 'signin', 'accedi', 'registrati']):
                return {'status': 'need_login', 'has_tickets': False}
            
            # Enhanced ticket detection
            ticket_indicators = [
                # General
                'biglietto disponibile',
                'biglietti disponibili',
                'ticket available',
                'tickets available',
                'acquista ora',
                'buy now',
                'compra ora',
                'aggiungi al carrello',
                'add to cart',
                
                # Price indicators
                'prezzo',
                'price',
                '€',
                'eur',
                
                # Seat/section indicators
                'settore',
                'sector',
                'posto',
                'seat',
                'fila',
                'row',
                
                # Platform specific
                'offerta',
                'offer',
                'in vendita',
                'on sale'
            ]
            
            # Count matches
            matches = sum(1 for indicator in ticket_indicators if indicator in page_text)
            
            # Check for sold out
            sold_out_indicators = [
                'sold out',
                'esaurito',
                'esauriti',
                'non disponibile',
                'not available',
                'nessun biglietto',
                'no tickets',
                'terminati'
            ]
            
            is_sold_out = any(indicator in page_text for indicator in sold_out_indicators)
            
            # Strong indication of tickets
            if matches >= 3 and not is_sold_out:
                self.stats['tickets_found'] += 1
                
                # Try to find specific ticket info
                ticket_info = self.extract_ticket_info(driver)
                
                return {
                    'status': 'tickets_available',
                    'has_tickets': True,
                    'info': ticket_info
                }
            
            return {'status': 'no_tickets', 'has_tickets': False}
            
        except Exception as e:
            self.stats['errors'] += 1
            return {'status': 'error', 'has_tickets': False, 'error': str(e)}
    
    def extract_ticket_info(self, driver):
        """Try to extract ticket details"""
        info = []
        
        try:
            # Look for price elements
            price_selectors = [
                '[class*="price"]',
                '[class*="prezzo"]',
                '[class*="cost"]',
                'span:contains("€")'
            ]
            
            for selector in price_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:5]:  # Limit to first 5
                        text = element.text.strip()
                        if '€' in text or text.replace('.', '').replace(',', '').isdigit():
                            info.append(f"Price: {text}")
                except:
                    pass
            
            # Look for section/seat info
            section_selectors = [
                '[class*="section"]',
                '[class*="settore"]',
                '[class*="sector"]'
            ]
            
            for selector in section_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:3]:
                        text = element.text.strip()
                        if text and len(text) < 50:
                            info.append(f"Section: {text}")
                except:
                    pass
                    
        except:
            pass
            
        return info[:5]  # Return max 5 pieces of info
    
    def verify_proxy(self, driver):
        """Verify proxy is working"""
        try:
            # Save current URL
            current_url = driver.current_url
            
            # Check IP
            driver.get('https://httpbin.org/ip')
            time.sleep(2)
            
            ip_text = driver.find_element(By.TAG_NAME, 'body').text
            
            if 'origin' in ip_text.lower():
                self.stats['proxy_verified'] = True
                self.stats['proxy_working'] = True
                console.print(f"[green]✓ Proxy verified: {ip_text}[/green]")
            
            # Go back
            driver.get(current_url)
            
        except Exception as e:
            console.print(f"[yellow]Could not verify proxy: {e}[/yellow]")
    
    async def monitor_target(self, target):
        """Monitor a single target with all features"""
        name = target['name']
        url = target['url']
        platform = target['platform']
        interval = target.get('interval', 30)
        
        # Create driver
        console.print(f"[cyan]Creating driver for {name}...[/cyan]")
        driver = self.create_stealth_driver(name)
        
        if not driver:
            self.status[name] = "❌ Driver failed"
            return
            
        self.drivers[name] = driver
        console.print(f"[green]✓ Driver created for {name}[/green]")
        
        # Main monitoring loop
        consecutive_blocks = 0
        
        while self.running:
            try:
                self.status[name] = "🔄 Checking..."
                
                # Check the page
                result = self.check_page(driver, url, name)
                self.stats['checks'] += 1
                
                # Handle results
                if result['status'] == 'blocked':
                    consecutive_blocks += 1
                    self.status[name] = f"🚫 BLOCKED ({consecutive_blocks}x)"
                    console.print(f"[red]🚫 Blocked on {name} (attempt {consecutive_blocks})[/red]")
                    
                    # Progressive backoff
                    wait_time = min(300, 30 * (2 ** (consecutive_blocks - 1)))
                    console.print(f"[yellow]⏳ Waiting {wait_time}s before retry...[/yellow]")
                    await asyncio.sleep(wait_time)
                    
                    # Recreate driver after multiple blocks
                    if consecutive_blocks >= 3:
                        console.print(f"[yellow]🔄 Recreating driver for {name}...[/yellow]")
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = self.create_stealth_driver(name)
                        if driver:
                            self.drivers[name] = driver
                            consecutive_blocks = 0
                        else:
                            break
                    
                elif result['status'] == 'need_login':
                    self.status[name] = "🔐 Login needed"
                    console.print(f"[yellow]🔐 Login required for {name}[/yellow]")
                    consecutive_blocks = 0
                    await asyncio.sleep(interval)
                    
                elif result['status'] == 'tickets_available':
                    consecutive_blocks = 0
                    self.status[name] = "🎫 TICKETS FOUND! 🎉"
                    console.print(f"\n[bold green]🎫 TICKETS AVAILABLE on {name}! 🎉[/bold green]")
                    
                    if result.get('info'):
                        console.print("[cyan]Ticket details:[/cyan]")
                        for detail in result['info']:
                            console.print(f"  • {detail}")
                    
                    console.bell()  # System beep
                    
                    # Check more frequently when tickets found
                    await asyncio.sleep(5)
                    
                elif result['status'] == 'error':
                    self.status[name] = "⚠️  Error"
                    console.print(f"[red]Error on {name}: {result.get('error')}[/red]")
                    consecutive_blocks = 0
                    await asyncio.sleep(30)
                    
                else:
                    consecutive_blocks = 0
                    self.status[name] = "✓ No tickets"
                    
                    # Add some randomness to avoid patterns
                    wait_time = interval + random.randint(-5, 5)
                    await asyncio.sleep(max(10, wait_time))
                    
            except Exception as e:
                self.status[name] = "❌ Monitor error"
                console.print(f"[red]Monitor error for {name}: {e}[/red]")
                await asyncio.sleep(30)
    
    def create_dashboard(self):
        """Create enhanced dashboard"""
        layout = Layout()
        
        # Header
        header_text = "🎯 StealthMaster Final - Complete Edition"
        if self.use_proxy:
            header_text += " [Proxy Enabled]"
        
        header = Panel(
            Align.center(header_text, vertical="middle"),
            style="bold cyan",
            height=3
        )
        
        # Stats
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan", width=20)
        stats_table.add_column("Value", style="green", justify="right")
        
        uptime = str(datetime.now() - self.start_time).split('.')[0]
        stats_table.add_row("⏱️  Uptime", uptime)
        stats_table.add_row("✅ Total Checks", str(self.stats['checks']))
        stats_table.add_row("🎫 Tickets Found", str(self.stats['tickets_found']))
        stats_table.add_row("🚫 Times Blocked", str(self.stats['blocks']))
        stats_table.add_row("❌ Errors", str(self.stats['errors']))
        
        if self.use_proxy:
            proxy_status = "✓ Working" if self.stats.get('proxy_working') else "? Unknown"
            stats_table.add_row("🌐 Proxy Status", proxy_status)
        
        stats_panel = Panel(stats_table, title="📊 Statistics", style="green")
        
        # Monitors
        monitors_table = Table(box=None)
        monitors_table.add_column("Target", style="yellow", width=35)
        monitors_table.add_column("Status", style="cyan", width=25)
        
        for name, status in self.status.items():
            if not name.endswith('_cookies'):
                # Color code status
                if "TICKETS" in status:
                    status = f"[bold green]{status}[/bold green]"
                elif "BLOCKED" in status:
                    status = f"[red]{status}[/red]"
                elif "Login" in status:
                    status = f"[yellow]{status}[/yellow]"
                
                monitors_table.add_row(name[:35], status)
        
        monitors_panel = Panel(monitors_table, title="🖥️  Active Monitors", style="blue")
        
        # Instructions
        instructions = "[yellow]Ctrl+C to stop[/yellow] | [green]🎫 = Tickets[/green] | [red]🚫 = Blocked[/red] | [yellow]🔐 = Login[/yellow]"
        
        # Layout
        layout.split_column(
            Layout(header, size=3),
            Layout(name="body"),
            Layout(Panel(instructions, style="dim"), size=3)
        )
        layout["body"].split_row(
            Layout(stats_panel),
            Layout(monitors_panel)
        )
        
        return layout
    
    async def run(self, targets):
        """Run the complete monitoring system"""
        self.running = True
        
        console.print(f"[bold cyan]🚀 Starting StealthMaster Final[/bold cyan]")
        console.print(f"[yellow]Monitoring {len(targets)} targets[/yellow]")
        if self.use_proxy:
            console.print(f"[cyan]🌐 Proxy: {self.proxy_config['host']}:{self.proxy_config['port']}[/cyan]")
        else:
            console.print("[yellow]⚠️  Running without proxy (may get blocked)[/yellow]")
        console.print()
        
        # Start monitors
        tasks = []
        for target in targets:
            task = asyncio.create_task(self.monitor_target(target))
            tasks.append(task)
        
        # Display
        try:
            with Live(self.create_dashboard(), refresh_per_second=1, console=console) as live:
                while self.running:
                    live.update(self.create_dashboard())
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.running = False
        
        # Cleanup
        console.print("\n[yellow]🛑 Shutting down...[/yellow]")
        
        for task in tasks:
            task.cancel()
        
        for name, driver in self.drivers.items():
            try:
                driver.quit()
                console.print(f"[green]✓ Closed {name}[/green]")
            except:
                pass
        
        # Summary
        console.print("\n[bold cyan]📊 Final Summary:[/bold cyan]")
        console.print(f"  Runtime: {datetime.now() - self.start_time}")
        console.print(f"  Total checks: {self.stats['checks']}")
        console.print(f"  Tickets found: {self.stats['tickets_found']} times")
        console.print(f"  Blocked: {self.stats['blocks']} times")
        console.print(f"  Errors: {self.stats['errors']}")
        
        if self.stats['tickets_found'] > 0:
            console.print("\n[bold green]🎉 Tickets were found during this session![/bold green]")
        
        console.print("\n[bold green]✅ Shutdown complete[/bold green]")


async def main():
    """Main entry point"""
    # Configuration from config.yaml
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
    
    # Ask about proxy
    use_proxy = console.input("\n[cyan]Enable proxy protection? (recommended) [Y/n]: [/cyan]").lower() != 'n'
    
    monitor = StealthMasterFinal(use_proxy=use_proxy)
    await monitor.run(targets)


if __name__ == "__main__":
    console.print("""
    ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
    ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║
    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║
    ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║
    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝
                F I N A L  v2.0
    """, style="bold cyan")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")

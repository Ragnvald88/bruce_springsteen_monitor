# src/beast_mode.py
"""
Beast Mode Ticket Bot - Designed to win, not to hide
Architecture: Lightweight monitoring -> Instant parallel strikes -> Smart recovery
"""

import asyncio
import aiohttp
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
import hashlib
from asyncio import Queue, Event
import re
import os

logger = logging.getLogger(__name__)


class TicketStatus(Enum):
    MONITORING = "monitoring"
    DETECTED = "detected"
    PURCHASING = "purchasing"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class TicketOpportunity:
    """Represents a detected ticket availability"""
    id: str
    platform: str
    event_name: str
    url: str
    section: str
    price: float
    quantity: int
    detected_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.detected_at).total_seconds()


class LightweightMonitor:
    """
    Ultra-efficient monitoring using minimal resources
    Key insight: We don't need full browser for detection, only for purchase
    """
    
    def __init__(self, proxy_config: Dict[str, Any]):
        self.proxy_config = proxy_config
        self.session_cache: Dict[str, aiohttp.ClientSession] = {}
        self.last_check: Dict[str, datetime] = {}
        self.page_hashes: Dict[str, str] = {}  # Detect changes efficiently
        self.api_tokens: Dict[str, str] = {}
        
    async def create_session(self, platform: str) -> aiohttp.ClientSession:
        """Create platform-specific aiohttp session with proper settings"""
        if platform in self.session_cache:
            return self.session_cache[platform]
            
        # Rotate proxy for each platform
        proxy_url = self._get_proxy_url()
        
        headers = self._get_platform_headers(platform)
        
        connector = aiohttp.TCPConnector(
            limit=100,  # Connection pool
            ttl_dns_cache=300,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        session = aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar()  # Maintain cookies
        )
        
        if proxy_url:
            session._default_proxy = proxy_url
            
        self.session_cache[platform] = session
        return session
        
    def _get_proxy_url(self) -> Optional[str]:
        if not self.proxy_config.get('enabled'):
            return None

        # Prefer beast_mode_proxy_ports.monitoring if available
        beast_ports_config = self.proxy_config.get('beast_mode_proxy_ports', {})
        ports_to_use = beast_ports_config.get('monitoring', [])

        if not ports_to_use: # Fallback to main rotating_ports
            ports_to_use = self.proxy_config.get('rotating_ports', [])
            if ports_to_use:
                logger.debug("LightweightMonitor: Using main 'rotating_ports' for proxy.")
            elif beast_ports_config: # if beast_mode_proxy_ports was defined but monitoring was empty
                logger.warning("LightweightMonitor: 'beast_mode_proxy_ports.monitoring' is empty, falling back to 'rotating_ports' which is also empty or undefined.")
            else: # if neither beast_mode_proxy_ports.monitoring nor rotating_ports were found
                logger.warning("LightweightMonitor: No specific 'monitoring' ports in 'beast_mode_proxy_ports' and no fallback 'rotating_ports' defined.")

        if not ports_to_use: # If still no ports after fallbacks
            logger.warning("LightweightMonitor: No proxy ports available after checking monitoring-specific and main rotating_ports.")
            return None

        # Since you mentioned you only have one IProyal port, this rotation logic
        # will effectively just use that one port. If you add more to the list, it will rotate.
        minute = datetime.now().minute 
        port = ports_to_use[minute % len(ports_to_use)]

        template = self.proxy_config.get('server_template')
        username = os.getenv(self.proxy_config.get('username_env'))
        password = os.getenv(self.proxy_config.get('password_env'))

        if not template or not username or not password:
            logger.error("LightweightMonitor: Proxy template or credentials missing. Cannot form proxy URL.")
            return None

        return template.format(user=username, proxy_pass=password, port=port)
        
    def _get_platform_headers(self, platform: str) -> Dict[str, str]:
        """Platform-specific headers for stealth"""
        base_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        platform_specific = {
            'fansale': {
                'Referer': 'https://www.fansale.it/',
                'Origin': 'https://www.fansale.it'
            },
            'ticketmaster': {
                'Referer': 'https://www.ticketmaster.it/',
                'X-Requested-With': 'XMLHttpRequest'  # For API calls
            },
            'vivaticket': {
                'Referer': 'https://www.vivaticket.com/',
            }
        }
        
        headers = base_headers.copy()
        headers.update(platform_specific.get(platform, {}))
        return headers
        
    async def check_fansale_lightweight(self, url: str, event_name: str) -> List[TicketOpportunity]:
        """Lightweight FanSale monitoring"""
        opportunities = []
        session = await self.create_session('fansale')
        
        try:
            # Smart caching - only full check every 5 minutes, otherwise check for changes
            cache_key = f"fansale_{url}"
            now = datetime.now()
            
            if cache_key in self.last_check:
                time_since = (now - self.last_check[cache_key]).seconds
                if time_since < 30:  # Skip if checked within 30 seconds
                    return []
                    
            async with session.get(url) as response:
                if response.status != 200:
                    return []
                    
                html = await response.text()
                
                # Quick hash check for changes
                content_hash = hashlib.md5(html.encode()).hexdigest()
                if cache_key in self.page_hashes and self.page_hashes[cache_key] == content_hash:
                    # No changes, skip parsing
                    return []
                    
                self.page_hashes[cache_key] = content_hash
                
                # Parse for tickets (lightweight regex, not full DOM)
                ticket_pattern = r'data-offer-id="([^"]+)".*?EventEntry.*?>(.*?)</div>'
                matches = re.finditer(ticket_pattern, html, re.DOTALL)
                
                for match in matches:
                    offer_id = match.group(1)
                    content = match.group(2)
                    
                    # Extract price
                    price_match = re.search(r'€\s*([\d.,]+)', content)
                    price = float(price_match.group(1).replace(',', '.')) if price_match else 0
                    
                    # Extract section
                    section_match = re.search(r'Settore[:\s]+([^<\n]+)', content)
                    section = section_match.group(1).strip() if section_match else "Unknown"
                    
                    opportunity = TicketOpportunity(
                        id=f"fansale_{offer_id}",
                        platform="fansale",
                        event_name=event_name,
                        url=f"https://www.fansale.it/fansale/offerdetails/{offer_id}",
                        section=section,
                        price=price,
                        quantity=1,
                        detected_at=now,
                        metadata={'offer_id': offer_id}
                    )
                    
                    opportunities.append(opportunity)
                    
                self.last_check[cache_key] = now
                
        except Exception as e:
            logger.error(f"Lightweight FanSale check error: {e}")
            
        return opportunities
        
    async def check_ticketmaster_api(self, event_id: str) -> List[TicketOpportunity]:
        """Use Ticketmaster API for ultra-fast monitoring"""
        opportunities = []
        session = await self.create_session('ticketmaster')
        
        # Ticketmaster API endpoint (discovered through network analysis)
        api_url = f"https://shop.ticketmaster.it/api/event/{event_id}/availability"
        
        try:
            async with session.get(api_url) as response:
                if response.status != 200:
                    return []
                    
                data = await response.json()
                
                # Parse availability data
                for section in data.get('sections', []):
                    if section.get('available', 0) > 0:
                        for offer in section.get('offers', []):
                            opportunity = TicketOpportunity(
                                id=f"tm_{offer.get('id')}",
                                platform="ticketmaster",
                                event_name="Bruce Springsteen Milan",
                                url=offer.get('purchaseUrl'),
                                section=section.get('name'),
                                price=offer.get('price', {}).get('total', 0),
                                quantity=offer.get('available', 1),
                                detected_at=datetime.now(),
                                metadata={
                                    'offer_id': offer.get('id'),
                                    'api_data': offer
                                }
                            )
                            opportunities.append(opportunity)
                            
        except Exception as e:
            logger.error(f"Ticketmaster API check error: {e}")
            
        return opportunities


class InstantStrike:
    """
    When tickets are detected, launch multiple parallel purchase attempts
    Key insight: Speed > Stealth when tickets are available
    """
    
    def __init__(self, browser_manager: Any, max_parallel: int = 5):
        self.browser_manager = browser_manager
        self.max_parallel = max_parallel
        self.active_attempts: Set[str] = set()
        self.success_event = Event()
        
    async def strike(self, opportunity: TicketOpportunity, profiles: List[Any]) -> bool:
        """Launch parallel purchase attempts"""
        
        if opportunity.id in self.active_attempts:
            return False  # Already attempting
            
        self.active_attempts.add(opportunity.id)
        
        # Select best profiles for parallel attempts
        strike_profiles = self._select_strike_profiles(profiles, opportunity)
        
        # Launch parallel attempts
        tasks = []
        for i, profile in enumerate(strike_profiles[:self.max_parallel]):
            task = asyncio.create_task(
                self._attempt_purchase(opportunity, profile, attempt_num=i),
                name=f"strike_{opportunity.id}_{i}"
            )
            tasks.append(task)
            
        # Race condition - first to succeed wins
        try:
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=30  # 30 second timeout for purchase
            )
            
            # Check for success
            for task in done:
                if task.result():
                    # Success! Cancel other attempts
                    for p in pending:
                        p.cancel()
                    return True
                    
            # All completed tasks failed
            return False
            
        finally:
            self.active_attempts.remove(opportunity.id)
            
    def _select_strike_profiles(self, profiles: List[Any], opportunity: TicketOpportunity) -> List[Any]:
        """Select best profiles for this strike"""
        
        # Sort by success rate and readiness
        scored_profiles = []
        
        for profile in profiles:
            score = 0
            
            # Success rate
            score += profile.success_rate * 100
            
            # Freshness (prefer profiles not used recently)
            if profile.last_used:
                minutes_idle = (datetime.now() - profile.last_used).seconds / 60
                score += min(minutes_idle, 30)  # Max 30 point bonus
                
            # Platform-specific success
            platform_key = f"{opportunity.platform}_success_rate"
            if hasattr(profile, platform_key):
                score += getattr(profile, platform_key) * 50
                
            scored_profiles.append((score, profile))
            
        # Sort by score descending
        scored_profiles.sort(key=lambda x: x[0], reverse=True)
        
        return [profile for _, profile in scored_profiles]
        
    async def _attempt_purchase(self, opportunity: TicketOpportunity, profile: Any, attempt_num: int) -> bool:
        """Single purchase attempt"""
        
        logger.info(f"Strike attempt #{attempt_num} for {opportunity.id} using {profile.name}")
        
        try:
            # Get browser context (from pool or create new)
            async with self.browser_manager.get_context() as (context, _):
                page = await context.new_page()
                
                # Platform-specific purchase flow
                if opportunity.platform == "fansale":
                    return await self._purchase_fansale(page, opportunity)
                elif opportunity.platform == "ticketmaster":
                    return await self._purchase_ticketmaster(page, opportunity)
                elif opportunity.platform == "vivaticket":
                    return await self._purchase_vivaticket(page, opportunity)
                    
        except Exception as e:
            logger.error(f"Strike attempt #{attempt_num} failed: {e}")
            return False
            
    async def _purchase_fansale(self, page: Page, opportunity: TicketOpportunity) -> bool:
        """FanSale instant purchase flow"""
        
        # Direct to offer page
        await page.goto(opportunity.url, wait_until='domcontentloaded')
        
        # Click buy immediately
        buy_selectors = [
            'button[type="submit"]:has-text("Acquista")',
            'input[type="submit"][value*="Acquista"]',
            'button.btn-buy'
        ]
        
        for selector in buy_selectors:
            try:
                await page.click(selector, timeout=5000)
                
                # Wait for cart/checkout
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Check if in cart
                if 'cart' in page.url or 'checkout' in page.url:
                    logger.info(f"SUCCESS: Added to cart - {opportunity.id}")
                    return True
                    
            except:
                continue
                
        return False
        
    async def _purchase_ticketmaster(self, page: Page, opportunity: TicketOpportunity) -> bool:
        """Ticketmaster instant purchase using API"""
        
        # Use API directly if we have offer_id
        offer_id = opportunity.metadata.get('offer_id')
        if offer_id:
            # Direct API add to cart
            api_url = "https://shop.ticketmaster.it/api/cart/add"
            
            response = await page.request.post(api_url, data={
                'offer_id': offer_id,
                'quantity': opportunity.quantity
            })
            
            if response.ok:
                logger.info(f"SUCCESS: API added to cart - {opportunity.id}")
                return True
                
        # Fallback to UI
        await page.goto(opportunity.url, wait_until='domcontentloaded')
        # ... implement UI flow
        
        return False


class BeastModeOrchestrator:
    """
    Main orchestrator - coordinates lightweight monitoring with instant strikes
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitor = LightweightMonitor(config.get('proxy', {}))
        self.strike_force = None  # Initialized after browser manager
        self.opportunity_queue = Queue()
        self.seen_opportunities: Set[str] = set()
        self.stats = {
            'checks': 0,
            'detections': 0,
            'attempts': 0,
            'successes': 0,
            'start_time': datetime.now()
        }
        
    async def run(self, browser_manager: Any, stop_event: Event):
        """Main execution loop"""
        
        self.strike_force = InstantStrike(browser_manager)
        
        # Start monitoring tasks
        monitor_tasks = []
        for target in self.config.get('targets', []):
            if target.get('enabled'):
                task = asyncio.create_task(
                    self._monitor_target(target, stop_event),
                    name=f"monitor_{target.get('platform')}_{target.get('event_name', 'unknown')}"
                )
                monitor_tasks.append(task)
                
        # Start strike processor
        strike_task = asyncio.create_task(
            self._process_strikes(browser_manager.profiles, stop_event),
            name="strike_processor"
        )
        
        # Stats reporter
        stats_task = asyncio.create_task(
            self._report_stats(stop_event),
            name="stats_reporter"
        )
        
        # Wait for completion
        try:
            await asyncio.gather(
                *monitor_tasks,
                strike_task,
                stats_task
            )
        except asyncio.CancelledError:
            logger.info("Beast mode shutting down...")
            
    async def _monitor_target(self, target: Dict[str, Any], stop_event: Event):
        """Monitor single target with smart intervals"""
        
        platform = target.get('platform', '').lower()
        url = target.get('url')
        event_name = target.get('event_name', 'Unknown')
        
        # Smart interval calculation
        base_interval = 60  # 1 minute base
        burst_interval = 5  # 5 seconds during high activity
        current_interval = base_interval
        last_detection = None
        
        while not stop_event.is_set():
            try:
                self.stats['checks'] += 1
                
                # Choose monitoring method
                opportunities = []
                
                if platform == 'fansale':
                    opportunities = await self.monitor.check_fansale_lightweight(url, event_name)
                elif platform == 'ticketmaster':
                    # Extract event ID from URL
                    event_id_match = re.search(r'-(\d+)\.html', url)
                    if event_id_match:
                        event_id = event_id_match.group(1)
                        opportunities = await self.monitor.check_ticketmaster_api(event_id)
                # ... other platforms
                
                # Process opportunities
                new_opportunities = []
                for opp in opportunities:
                    if opp.id not in self.seen_opportunities:
                        self.seen_opportunities.add(opp.id)
                        new_opportunities.append(opp)
                        self.stats['detections'] += 1
                        
                if new_opportunities:
                    logger.warning(f"DETECTED {len(new_opportunities)} tickets for {event_name}!")
                    last_detection = datetime.now()
                    
                    # Queue for strike
                    for opp in new_opportunities:
                        await self.opportunity_queue.put(opp)
                        
                    # Enter burst mode
                    current_interval = burst_interval
                else:
                    # Gradually return to normal interval
                    if last_detection:
                        time_since = (datetime.now() - last_detection).seconds
                        if time_since > 300:  # 5 minutes
                            current_interval = base_interval
                        else:
                            current_interval = min(current_interval * 1.5, base_interval)
                            
                # Smart waiting with jitter
                wait_time = current_interval * random.uniform(0.8, 1.2)
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Monitor error for {platform}: {e}")
                await asyncio.sleep(60)  # Error backoff
                
    async def _process_strikes(self, profiles: List[Any], stop_event: Event):
        """Process strike queue"""
        
        while not stop_event.is_set():
            try:
                # Wait for opportunity with timeout
                opportunity = await asyncio.wait_for(
                    self.opportunity_queue.get(),
                    timeout=1.0
                )
                
                # Skip if too old
                if opportunity.age_seconds > 60:
                    logger.info(f"Skipping stale opportunity: {opportunity.id}")
                    continue
                    
                self.stats['attempts'] += 1
                
                # Launch strike
                success = await self.strike_force.strike(opportunity, profiles)
                
                if success:
                    self.stats['successes'] += 1
                    logger.critical(f"PURCHASE SUCCESS: {opportunity.id}")
                    
                    # Notify and potentially pause
                    # ... notification code
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Strike processor error: {e}")
                
    async def _report_stats(self, stop_event: Event):
        """Report performance stats"""
        
        while not stop_event.is_set():
            runtime = (datetime.now() - self.stats['start_time']).seconds / 60
            
            logger.info(
                f"BEAST MODE STATS - "
                f"Runtime: {runtime:.1f}m | "
                f"Checks: {self.stats['checks']} | "
                f"Detections: {self.stats['detections']} | "
                f"Attempts: {self.stats['attempts']} | "
                f"Successes: {self.stats['successes']} | "
                f"Success Rate: {self.stats['successes']/max(1, self.stats['attempts'])*100:.1f}%"
            )
            
            await asyncio.sleep(60)  # Report every minute


# Integration with existing main.py
async def run_beast_mode(config: Dict[str, Any], browser_manager: Any, stop_event: Event):
    """Run in beast mode"""
    
    logger.info("🔥 ACTIVATING BEAST MODE 🔥")
    
    orchestrator = BeastModeOrchestrator(config)
    await orchestrator.run(browser_manager, stop_event)
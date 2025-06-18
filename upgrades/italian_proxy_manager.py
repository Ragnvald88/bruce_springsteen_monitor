"""
Italian Proxy Manager
=====================
Manages residential Italian proxies for FanSale.it access
"""

import asyncio
import aiohttp
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class ItalianProxy:
    """Represents an Italian residential proxy"""
    host: str
    port: int
    username: str
    password: str
    protocol: str = 'http'
    city: Optional[str] = None
    region: Optional[str] = None
    isp: Optional[str] = None
    speed_score: float = 1.0
    reliability_score: float = 1.0
    last_used: Optional[datetime] = None
    failures: int = 0
    successes: int = 0
    blocked: bool = False
    block_until: Optional[datetime] = None
    
    @property
    def url(self) -> str:
        """Get proxy URL"""
        return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
    
    @property
    def score(self) -> float:
        """Calculate overall proxy score"""
        if self.blocked:
            return 0.0
        
        # Base score on speed and reliability
        base_score = (self.speed_score + self.reliability_score) / 2
        
        # Penalize recent failures
        if self.failures > 0:
            failure_penalty = min(self.failures * 0.1, 0.5)
            base_score *= (1 - failure_penalty)
        
        # Boost for successes
        if self.successes > 0:
            success_boost = min(self.successes * 0.02, 0.2)
            base_score *= (1 + success_boost)
        
        # Prefer proxies that haven't been used recently
        if self.last_used:
            minutes_since_use = (datetime.now() - self.last_used).total_seconds() / 60
            if minutes_since_use < 5:
                base_score *= 0.5  # Recently used penalty
            elif minutes_since_use > 30:
                base_score *= 1.2  # Long unused boost
        
        return min(base_score, 1.0)


class ItalianProxyManager:
    """
    Manages Italian residential proxies with intelligent rotation
    
    Features:
    - Automatic proxy testing and scoring
    - Geographic distribution (Milan, Rome, etc.)
    - ISP diversity for better success
    - Failure tracking and blacklisting
    - Session stickiness support
    """
    
    def __init__(self):
        self.proxies: List[ItalianProxy] = []
        self.sticky_sessions: Dict[str, ItalianProxy] = {}
        self.proxy_config = self._load_proxy_config()
        self._init_proxies()
        
    def _load_proxy_config(self) -> dict:
        """Load proxy configuration"""
        # Check for proxy config file
        config_path = os.path.join(os.path.dirname(__file__), 'proxy_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration using environment variables
        return {
            'providers': [
                {
                    'name': 'iproyal',
                    'endpoint': os.getenv('IPROYAL_ENDPOINT', 'geo.iproyal.com'),
                    'port': int(os.getenv('IPROYAL_PORT', '12321')),
                    'username': os.getenv('IPROYAL_USERNAME'),
                    'password_template': os.getenv('IPROYAL_PASSWORD', 
                        '{password}_country-it_city-{city}_session-{session}_lifetime-10m')
                }
            ],
            'target_cities': ['milan', 'rome', 'turin', 'naples', 'florence'],
            'min_proxies': 10,
            'max_concurrent': 5
        }
    
    def _init_proxies(self):
        """Initialize proxy pool"""
        for provider in self.proxy_config['providers']:
            if provider['name'] == 'iproyal' and provider['username']:
                # Generate proxies for each city
                for city in self.proxy_config['target_cities']:
                    # Create multiple sessions per city
                    for i in range(2):
                        session_id = f"{city}_{int(time.time())}_{i}"
                        
                        password = provider['password_template'].format(
                            password=provider.get('base_password', 'password'),
                            city=city,
                            session=session_id
                        )
                        
                        proxy = ItalianProxy(
                            host=provider['endpoint'],
                            port=provider['port'],
                            username=provider['username'],
                            password=password,
                            city=city,
                            region=self._get_region(city),
                            isp='Residential'
                        )
                        
                        self.proxies.append(proxy)
        
        logger.info(f"Initialized {len(self.proxies)} Italian proxies")
    
    def _get_region(self, city: str) -> str:
        """Get region for city"""
        regions = {
            'milan': 'Lombardy',
            'rome': 'Lazio',
            'turin': 'Piedmont',
            'naples': 'Campania',
            'florence': 'Tuscany'
        }
        return regions.get(city.lower(), 'Unknown')
    
    async def test_proxy(self, proxy: ItalianProxy) -> bool:
        """Test if proxy is working"""
        test_url = 'https://httpbin.org/ip'
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            ) as session:
                start_time = time.time()
                
                async with session.get(
                    test_url,
                    proxy=proxy.url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_time = time.time() - start_time
                        
                        # Update proxy speed score
                        if response_time < 1:
                            proxy.speed_score = 1.0
                        elif response_time < 3:
                            proxy.speed_score = 0.8
                        else:
                            proxy.speed_score = 0.6
                        
                        # Verify Italian IP
                        # In production, you'd check against an IP geolocation service
                        logger.info(f"Proxy {proxy.city} working: {data['origin']}")
                        return True
            
        except Exception as e:
            logger.debug(f"Proxy test failed for {proxy.city}: {e}")
        
        return False
    
    async def test_all_proxies(self):
        """Test all proxies in parallel"""
        logger.info("Testing all proxies...")
        
        tasks = []
        for proxy in self.proxies:
            tasks.append(self.test_proxy(proxy))
        
        results = await asyncio.gather(*tasks)
        
        # Update reliability scores
        for proxy, success in zip(self.proxies, results):
            if success:
                proxy.reliability_score = min(proxy.reliability_score * 1.1, 1.0)
                proxy.successes += 1
            else:
                proxy.reliability_score *= 0.8
                proxy.failures += 1
        
        working = sum(results)
        logger.info(f"Proxy test complete: {working}/{len(self.proxies)} working")
    
    async def get_best_proxy(self, sticky_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get best available proxy"""
        # Check sticky session
        if sticky_key and sticky_key in self.sticky_sessions:
            proxy = self.sticky_sessions[sticky_key]
            if not proxy.blocked and proxy.score > 0.3:
                proxy.last_used = datetime.now()
                return self._proxy_to_dict(proxy)
        
        # Filter available proxies
        available = [
            p for p in self.proxies
            if not p.blocked and (not p.block_until or p.block_until < datetime.now())
        ]
        
        if not available:
            logger.error("No available proxies!")
            return None
        
        # Sort by score
        available.sort(key=lambda p: p.score, reverse=True)
        
        # Select from top proxies with some randomness
        top_count = min(3, len(available))
        selected = random.choice(available[:top_count])
        
        # Update usage
        selected.last_used = datetime.now()
        
        # Create sticky session if requested
        if sticky_key:
            self.sticky_sessions[sticky_key] = selected
        
        logger.info(f"Selected proxy: {selected.city} (score: {selected.score:.2f})")
        
        return self._proxy_to_dict(selected)
    
    def _proxy_to_dict(self, proxy: ItalianProxy) -> Dict[str, Any]:
        """Convert proxy to Playwright/Selenium format"""
        return {
            'server': f"{proxy.protocol}://{proxy.host}:{proxy.port}",
            'username': proxy.username,
            'password': proxy.password,
            'bypass': 'localhost,127.0.0.1'
        }
    
    def mark_proxy_failed(self, proxy_dict: Dict[str, Any]):
        """Mark proxy as failed"""
        # Find proxy by server URL
        server = proxy_dict['server']
        
        for proxy in self.proxies:
            if f"{proxy.protocol}://{proxy.host}:{proxy.port}" == server:
                proxy.failures += 1
                
                # Block if too many failures
                if proxy.failures > 5:
                    proxy.blocked = True
                    proxy.block_until = datetime.now() + timedelta(hours=1)
                    logger.warning(f"Blocked proxy {proxy.city} due to failures")
                
                break
    
    def mark_proxy_success(self, proxy_dict: Dict[str, Any]):
        """Mark proxy as successful"""
        server = proxy_dict['server']
        
        for proxy in self.proxies:
            if f"{proxy.protocol}://{proxy.host}:{proxy.port}" == server:
                proxy.successes += 1
                proxy.failures = max(0, proxy.failures - 1)  # Reduce failure count
                proxy.reliability_score = min(proxy.reliability_score * 1.05, 1.0)
                break
    
    async def rotate_sticky_session(self, sticky_key: str):
        """Force rotation of sticky session"""
        if sticky_key in self.sticky_sessions:
            old_proxy = self.sticky_sessions[sticky_key]
            
            # Get new proxy excluding the old one
            available = [
                p for p in self.proxies
                if p != old_proxy and not p.blocked
            ]
            
            if available:
                new_proxy = max(available, key=lambda p: p.score)
                self.sticky_sessions[sticky_key] = new_proxy
                logger.info(f"Rotated sticky session from {old_proxy.city} to {new_proxy.city}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        total = len(self.proxies)
        blocked = sum(1 for p in self.proxies if p.blocked)
        working = sum(1 for p in self.proxies if p.score > 0.5)
        
        by_city = {}
        for proxy in self.proxies:
            city = proxy.city or 'unknown'
            if city not in by_city:
                by_city[city] = {'total': 0, 'working': 0, 'blocked': 0}
            
            by_city[city]['total'] += 1
            if proxy.score > 0.5:
                by_city[city]['working'] += 1
            if proxy.blocked:
                by_city[city]['blocked'] += 1
        
        return {
            'total_proxies': total,
            'working_proxies': working,
            'blocked_proxies': blocked,
            'sticky_sessions': len(self.sticky_sessions),
            'by_city': by_city
        }


# Global instance
italian_proxy_manager = ItalianProxyManager()

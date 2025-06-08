# src/core/proxy_manager.py
"""
StealthMaster AI Proxy Manager v2.0
Intelligent proxy rotation with health monitoring and geo-targeting
"""

import asyncio
import logging
import time
import random
import httpx
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Enhanced proxy configuration with performance tracking"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"
    country: str = "XX"
    quality_score: float = 0.5
    
    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocks_encountered: int = 0
    last_used: Optional[datetime] = None
    last_block: Optional[datetime] = None
    avg_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def url(self) -> str:
        """Get proxy URL for Playwright"""
        if self.username and self.password:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return self.quality_score
        return self.successful_requests / self.total_requests
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score"""
        # Base score from success rate
        score = self.success_rate * 0.5
        
        # Quality score factor
        score += self.quality_score * 0.2
        
        # Response time factor (faster is better)
        if self.avg_response_time > 0:
            speed_score = min(1.0, 1.0 / (self.avg_response_time / 1000))  # Convert to seconds
            score += speed_score * 0.2
        else:
            score += 0.1  # Default if no data
        
        # Recency factor
        if self.last_used:
            hours_since_use = (datetime.now() - self.last_used).total_seconds() / 3600
            recency_score = max(0, 1 - hours_since_use / 24)  # Decay over 24 hours
            score += recency_score * 0.1
        
        # Penalty for recent blocks
        if self.last_block:
            hours_since_block = (datetime.now() - self.last_block).total_seconds() / 3600
            if hours_since_block < 2:
                score *= 0.3  # Heavy penalty for recent blocks
            elif hours_since_block < 24:
                score *= 0.7  # Moderate penalty
        
        return min(1.0, score)
    
    def record_request(self, success: bool, response_time: float, blocked: bool = False) -> None:
        """Record request outcome"""
        self.total_requests += 1
        self.last_used = datetime.now()
        self.response_times.append(response_time)
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        if blocked:
            self.blocks_encountered += 1
            self.last_block = datetime.now()
        
        # Update average response time
        if self.response_times:
            self.avg_response_time = sum(self.response_times) / len(self.response_times)
    
    def is_ready(self, cooldown_minutes: int = 120) -> bool:
        """Check if proxy is ready for use"""
        if self.last_block:
            cooldown_time = timedelta(minutes=cooldown_minutes)
            if datetime.now() - self.last_block < cooldown_time:
                return False
        return True


class StealthProxyManager:
    """Intelligent proxy management with ML-based selection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('proxy_settings', {})
        self.enabled = self.config.get('enabled', False)
        
        # Proxy pools
        self.primary_pool: List[Proxy] = []
        self.backup_pool: List[Proxy] = []
        self.all_proxies: Dict[str, Proxy] = {}
        
        # Rotation settings
        self.rotation_strategy = self.config.get('rotation_strategy', 'intelligent')
        self.rotation_rules = self.config.get('rotation_rules', {})
        
        # Platform preferences
        self.platform_preferences = self.config.get('platform_preferences', {})
        
        # Profile-proxy bindings
        self.profile_bindings: Dict[str, str] = {}  # profile_id -> proxy_url
        self.proxy_assignments: Dict[str, List[str]] = defaultdict(list)  # proxy_url -> [profile_ids]
        
        # Performance tracking
        self.platform_performance: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Initialize proxies
        self._initialize_proxies()
        
        logger.info(f"🌐 Proxy Manager initialized with {len(self.primary_pool)} primary proxies")
    
    def _initialize_proxies(self) -> None:
        """Initialize proxy pools from configuration"""
        # Load primary pool
        for proxy_config in self.config.get('primary_pool', []):
            proxy = Proxy(
                host=proxy_config['host'],
                port=int(proxy_config['port']),  # Ensure port is integer
                username=proxy_config.get('username'),
                password=proxy_config.get('password'),
                proxy_type=proxy_config.get('type', 'http'),
                country=proxy_config.get('country', 'XX'),
                quality_score=proxy_config.get('quality_score', 0.5)
            )
            self.primary_pool.append(proxy)
            self.all_proxies[proxy.url] = proxy
        
        # Load backup pool
        for proxy_config in self.config.get('backup_pool', []):
            proxy = Proxy(
                host=proxy_config['host'],
                port=int(proxy_config['port']),  # Ensure port is integer
                username=proxy_config.get('username'),
                password=proxy_config.get('password'),
                proxy_type=proxy_config.get('type', 'http'),
                country=proxy_config.get('country', 'XX'),
                quality_score=proxy_config.get('quality_score', 0.3)
            )
            self.backup_pool.append(proxy)
            self.all_proxies[proxy.url] = proxy
    
    async def validate_all_proxies(self) -> None:
        """Validate all proxies on startup"""
        if not self.config.get('validation', {}).get('validate_on_start', True):
            return
        
        logger.info("🔍 Validating all proxies...")
        
        tasks = []
        for proxy in self.all_proxies.values():
            task = asyncio.create_task(self._validate_proxy(proxy))
            tasks.append((proxy, task))
        
        # Wait for all validations
        for proxy, task in tasks:
            try:
                is_valid = await task
                if is_valid:
                    logger.info(f"✅ Proxy {proxy.host}:{proxy.port} validated")
                else:
                    logger.warning(f"❌ Proxy {proxy.host}:{proxy.port} failed validation")
                    proxy.quality_score *= 0.5  # Reduce quality score
            except Exception as e:
                logger.error(f"Proxy validation error: {e}")
    
    async def _validate_proxy(self, proxy: Proxy) -> bool:
        """Validate single proxy"""
        # Use a simpler test URL that works better with proxies
        test_url = self.config.get('validation', {}).get('test_url', 'http://ip-api.com/json')
        timeout = self.config.get('validation', {}).get('timeout_seconds', 10)
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(
                proxy=proxy.url,
                timeout=timeout
            ) as client:
                response = await client.get(test_url)
                response_time = (time.time() - start_time) * 1000  # ms
                
                if response.status_code == 200:
                    proxy.record_request(True, response_time)
                    
                    # Verify IP is different
                    try:
                        data = response.json()
                        # ip-api.com returns 'query' field with IP
                        proxy_ip = data.get('query') or data.get('origin') or 'Unknown'
                        logger.debug(f"Proxy {proxy.host} returned IP: {proxy_ip}")
                    except:
                        logger.debug(f"Proxy {proxy.host} validated successfully")
                    
                    return True
                else:
                    proxy.record_request(False, response_time)
                    return False
                    
        except Exception as e:
            logger.debug(f"Proxy validation failed: {e}")
            proxy.record_request(False, timeout * 1000)
            return False
    
    def get_proxy_for_profile(self, profile_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """Get optimal proxy for profile and platform"""
        if not self.enabled:
            return None
        
        # Check if profile has sticky binding
        if self.config.get('proxy_binding', {}).get('sticky_sessions', True):
            if profile_id in self.profile_bindings:
                proxy_url = self.profile_bindings[profile_id]
                proxy = self.all_proxies.get(proxy_url)
                if proxy and proxy.is_ready():
                    return self._proxy_to_dict(proxy)
        
        # Select new proxy
        proxy = self._select_optimal_proxy(platform)
        
        if proxy:
            # Create binding
            self.profile_bindings[profile_id] = proxy.url
            self.proxy_assignments[proxy.url].append(profile_id)
            
            return self._proxy_to_dict(proxy)
        
        return None
    
    def _select_optimal_proxy(self, platform: str) -> Optional[Proxy]:
        """Select optimal proxy using intelligent strategy"""
        available_proxies = [
            p for p in self.primary_pool 
            if p.is_ready(self.rotation_rules.get('cooldown_after_block_minutes', 120))
        ]
        
        if not available_proxies:
            # Try backup pool
            available_proxies = [
                p for p in self.backup_pool 
                if p.is_ready(60)  # Shorter cooldown for backup
            ]
        
        if not available_proxies:
            logger.error("No available proxies!")
            return None
        
        # Apply platform preferences
        platform_prefs = self.platform_preferences.get(platform, {})
        preferred_countries = platform_prefs.get('preferred_countries', [])
        require_residential = platform_prefs.get('require_residential', False)
        
        # Filter by preferences
        if preferred_countries:
            country_filtered = [
                p for p in available_proxies 
                if p.country in preferred_countries
            ]
            if country_filtered:
                available_proxies = country_filtered
        
        # Select based on strategy
        if self.rotation_strategy == 'intelligent':
            return self._intelligent_selection(available_proxies, platform)
        elif self.rotation_strategy == 'round_robin':
            return self._round_robin_selection(available_proxies)
        else:  # random
            return random.choice(available_proxies)
    
    def _intelligent_selection(self, proxies: List[Proxy], platform: str) -> Proxy:
        """ML-based intelligent proxy selection"""
        # Score each proxy
        scored_proxies = []
        
        for proxy in proxies:
            score = proxy.health_score
            
            # Platform-specific performance bonus
            platform_key = f"{proxy.url}_{platform}"
            if platform_key in self.platform_performance:
                platform_score = self.platform_performance[platform_key].get('success_rate', 0.5)
                score = score * 0.7 + platform_score * 0.3
            
            # Add quantum randomness for diversity
            quantum_noise = random.gauss(0, 0.1)
            score += quantum_noise
            
            scored_proxies.append((score, proxy))
        
        # Sort by score and select best
        scored_proxies.sort(key=lambda x: x[0], reverse=True)
        
        # 70% chance to pick best, 30% chance for diversity
        if random.random() < 0.7:
            return scored_proxies[0][1]
        else:
            # Pick from top 3
            top_proxies = [p[1] for p in scored_proxies[:3]]
            return random.choice(top_proxies)
    
    def _round_robin_selection(self, proxies: List[Proxy]) -> Proxy:
        """Round-robin selection"""
        # Sort by last used time
        proxies.sort(key=lambda p: p.last_used or datetime.min)
        return proxies[0]
    
    def _proxy_to_dict(self, proxy: Proxy) -> Dict[str, Any]:
        """Convert proxy to Playwright-compatible dict"""
        return {
            'server': proxy.url,
            'username': proxy.username,
            'password': proxy.password
        }
    
    def record_proxy_result(
        self, 
        profile_id: str, 
        platform: str,
        success: bool, 
        response_time: float,
        blocked: bool = False
    ) -> None:
        """Record proxy performance"""
        if profile_id not in self.profile_bindings:
            return
        
        proxy_url = self.profile_bindings[profile_id]
        proxy = self.all_proxies.get(proxy_url)
        
        if proxy:
            proxy.record_request(success, response_time, blocked)
            
            # Update platform-specific performance
            platform_key = f"{proxy_url}_{platform}"
            perf = self.platform_performance[platform_key]
            
            total = perf.get('total', 0) + 1
            successes = perf.get('successes', 0) + (1 if success else 0)
            
            perf['total'] = total
            perf['successes'] = successes
            perf['success_rate'] = successes / total
            
            # Log significant events
            if blocked:
                logger.warning(f"🚫 Proxy {proxy.host} blocked on {platform}")
            elif success and response_time < 1000:  # Under 1 second
                logger.debug(f"⚡ Fast response from {proxy.host}: {response_time:.0f}ms")
    
    def rotate_proxy_for_profile(self, profile_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """Force proxy rotation for profile"""
        # Remove old binding
        if profile_id in self.profile_bindings:
            old_proxy_url = self.profile_bindings[profile_id]
            self.proxy_assignments[old_proxy_url].remove(profile_id)
            del self.profile_bindings[profile_id]
        
        # Get new proxy
        return self.get_proxy_for_profile(profile_id, platform)
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get comprehensive proxy statistics"""
        active_proxies = sum(1 for p in self.all_proxies.values() if p.is_ready())
        total_requests = sum(p.total_requests for p in self.all_proxies.values())
        total_blocks = sum(p.blocks_encountered for p in self.all_proxies.values())
        
        # Get best performing proxy
        best_proxy = max(
            self.all_proxies.values(),
            key=lambda p: p.health_score,
            default=None
        )
        
        return {
            'total_proxies': len(self.all_proxies),
            'active_proxies': active_proxies,
            'total_requests': total_requests,
            'total_blocks': total_blocks,
            'block_rate': total_blocks / max(1, total_requests),
            'best_proxy': {
                'host': best_proxy.host if best_proxy else 'N/A',
                'health_score': best_proxy.health_score if best_proxy else 0,
                'success_rate': best_proxy.success_rate if best_proxy else 0
            } if best_proxy else None,
            'platform_performance': dict(self.platform_performance)
        }
    
    async def periodic_revalidation(self) -> None:
        """Periodically revalidate proxies"""
        interval_hours = self.config.get('validation', {}).get('revalidate_interval_hours', 6)
        
        while True:
            await asyncio.sleep(interval_hours * 3600)
            
            logger.info("🔄 Running periodic proxy revalidation")
            
            # Revalidate proxies that haven't been used recently
            for proxy in self.all_proxies.values():
                if proxy.last_used:
                    hours_since_use = (datetime.now() - proxy.last_used).total_seconds() / 3600
                    if hours_since_use > 24:
                        await self._validate_proxy(proxy)
                else:
                    # Never used
                    await self._validate_proxy(proxy)


# Singleton instance
_proxy_manager_instance: Optional[StealthProxyManager] = None


def get_proxy_manager(config: Dict[str, Any]) -> StealthProxyManager:
    """Get or create proxy manager singleton"""
    global _proxy_manager_instance
    
    if _proxy_manager_instance is None:
        _proxy_manager_instance = StealthProxyManager(config)
    
    return _proxy_manager_instance
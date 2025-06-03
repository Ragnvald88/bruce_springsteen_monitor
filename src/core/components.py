# src/core/components.py - v4.0 - Ultra-Stealth Enhanced
from __future__ import annotations

import asyncio
import logging
import re
import random
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Pattern
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import httpx
from urllib.parse import urlparse, urljoin

# Core imports
from .models import EnhancedTicketOpportunity, DataUsageTracker
from .enums import PlatformType, PriorityLevel
from .managers import ConnectionPoolManager, ResponseCache

# Profile imports - Fixed import path
from src.profiles.manager import ProfileManager
from src.profiles.models import BrowserProfile
from src.profiles.enums import DetectionEvent  # Import from profiles package

logger = logging.getLogger(__name__)

@dataclass
class MonitoringMetrics:
    """Tracks monitoring performance and detection patterns"""
    successful_checks: int = 0
    failed_checks: int = 0
    detections: int = 0
    last_detection: Optional[datetime] = None
    detection_times: deque = field(default_factory=lambda: deque(maxlen=100))
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def avg_response_time(self) -> float:
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0
    
    @property
    def detection_rate(self) -> float:
        total = self.successful_checks + self.failed_checks
        return self.detections / total if total > 0 else 0

class StealthRequestBuilder:
    """Builds HTTP requests with advanced anti-detection features"""
    
    def __init__(self):
        self.header_orders = {
            'chrome': ['host', 'connection', 'cache-control', 'sec-ch-ua', 'sec-ch-ua-mobile', 
                      'sec-ch-ua-platform', 'upgrade-insecure-requests', 'user-agent', 'accept',
                      'sec-fetch-site', 'sec-fetch-mode', 'sec-fetch-user', 'sec-fetch-dest',
                      'referer', 'accept-encoding', 'accept-language', 'cookie'],
            'firefox': ['host', 'user-agent', 'accept', 'accept-language', 'accept-encoding',
                       'connection', 'referer', 'cookie', 'upgrade-insecure-requests',
                       'sec-fetch-dest', 'sec-fetch-mode', 'sec-fetch-site'],
            'safari': ['host', 'accept', 'accept-language', 'connection', 'accept-encoding',
                      'user-agent', 'referer', 'cookie']
        }
    
    def build_headers(self, profile: BrowserProfile, url: str, 
                     additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build browser-specific headers with proper ordering"""
        
        # Determine browser type from user agent
        ua_lower = profile.user_agent.lower()
        if 'chrome' in ua_lower:
            browser_type = 'chrome'
        elif 'firefox' in ua_lower:
            browser_type = 'firefox'
        elif 'safari' in ua_lower:
            browser_type = 'safari'
        else:
            browser_type = 'chrome'  # Default
        
        # Base headers
        parsed_url = urlparse(url)
        headers = {
            'host': parsed_url.netloc,
            'connection': 'keep-alive',
            'cache-control': 'max-age=0',
            'user-agent': profile.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-language': self._generate_accept_language(profile),
            'accept-encoding': 'gzip, deflate, br',
        }
        
        # Browser-specific headers
        if browser_type == 'chrome':
            headers.update({
                'sec-ch-ua': self._generate_sec_ch_ua(profile),
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': f'"{profile.platform}"',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'upgrade-insecure-requests': '1',
            })
        
        # Add referer if not first request
        if hasattr(profile, '_last_url') and profile._last_url:
            headers['referer'] = profile._last_url
        
        # Merge additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        # Order headers according to browser
        ordered_headers = {}
        header_order = self.header_orders.get(browser_type, self.header_orders['chrome'])
        
        for key in header_order:
            if key in headers:
                ordered_headers[key] = headers[key]
        
        # Add any remaining headers
        for key, value in headers.items():
            if key not in ordered_headers:
                ordered_headers[key] = value
        
        return ordered_headers
    
    def _generate_sec_ch_ua(self, profile: BrowserProfile) -> str:
        """Generate Chrome sec-ch-ua header"""
        # Extract Chrome version from user agent
        match = re.search(r'Chrome/(\d+)', profile.user_agent)
        if match:
            version = match.group(1)
            return f'"Chromium";v="{version}", "Not=A?Brand";v="24", "Google Chrome";v="{version}"'
        return '"Chromium";v="120", "Not=A?Brand";v="24"'
    
    def _generate_accept_language(self, profile: BrowserProfile) -> str:
        """Generate realistic accept-language header"""
        languages = getattr(profile, 'languages', ['en-US', 'en'])
        weights = [1.0, 0.9, 0.8, 0.7, 0.6]
        
        lang_parts = []
        for i, lang in enumerate(languages[:5]):
            if i == 0:
                lang_parts.append(lang)
            else:
                weight = weights[min(i, len(weights)-1)]
                lang_parts.append(f"{lang};q={weight}")
        
        return ','.join(lang_parts)

class ProfileAwareLightweightMonitor:
    """Enhanced monitoring with advanced stealth and performance optimizations"""
    
    def __init__(self,
                 config: Dict[str, Any],
                 profile_manager: ProfileManager,
                 connection_pool: ConnectionPoolManager,
                 response_cache: ResponseCache,
                 data_tracker: DataUsageTracker):
        
        self.config = config
        self.profile_manager = profile_manager
        self.connection_pool = connection_pool
        self.response_cache = response_cache
        self.data_tracker = data_tracker
        
        # Components
        self.request_builder = StealthRequestBuilder()
        self.metrics: Dict[str, MonitoringMetrics] = defaultdict(MonitoringMetrics)
        
        # Detection patterns with fallbacks
        self.detection_patterns = self._compile_detection_patterns()
        
        # Timing and rate limiting
        self.last_check_times: Dict[str, datetime] = {}
        self.request_timestamps: deque = deque(maxlen=1000)
        
        # Configuration
        self.monitor_config = self.config.get('monitoring_settings', {})
        self.default_check_interval = self.monitor_config.get('default_target_interval_s', 60)
        self.cache_max_age_s = self.config.get('cache', {}).get('default_ttl_seconds', 30)
        
        # Anti-detection features
        self.jitter_range = (0.8, 1.2)  # 20% timing jitter
        self.burst_detection_threshold = 10  # Max requests in 10 seconds
        self.circuit_breaker_threshold = 5  # Consecutive failures before backing off
        self.backoff_multiplier = 2.0
        
        logger.info(f"ProfileAwareLightweightMonitor initialized with {len(self.detection_patterns)} platform patterns")
    
    def _compile_detection_patterns(self) -> Dict[PlatformType, Dict[str, Pattern]]:
        """Compile detection patterns with intelligent fallbacks"""
        
        # Default patterns if config is missing
        default_patterns = {
            PlatformType.FANSALE: {
                'offers': r'<div[^>]*class="[^"]*offer[^"]*"[^>]*>.*?data-offer-id="(?P<offer_id>[^"]+)".*?'
                         r'<span[^>]*class="[^"]*price[^"]*"[^>]*>.*?(?P<price>[\d,\.]+).*?</span>.*?'
                         r'<div[^>]*class="[^"]*section[^"]*"[^>]*>(?P<section_name>[^<]+)</div>.*?'
                         r'(?:quantity[^>]*>(?P<quantity>\d+))?',
                'json_offers': r'"offers"\s*:\s*\[([^\]]+)\]',
                'availability': r'(?:available|disponibile|verfügbar)[^>]*>(?P<available>\d+)',
            },
            PlatformType.TICKETMASTER: {
                'offers': r'<div[^>]*(?:listing|offer)[^>]*>.*?'
                         r'(?:id|data-id)="(?P<offer_id>[^"]+)".*?'
                         r'(?:price[^>]*>.*?(?P<price>[\d,\.]+)|€\s*(?P<price_alt>[\d,\.]+)).*?'
                         r'(?:section[^>]*>(?P<section>[^<]+)|Row\s*(?P<row>\w+))',
                'api_endpoint': r'/api/v\d+/events/(?P<event_id>[^/]+)/inventory',
            },
            PlatformType.VIVATICKET: {
                'offers': r'<(?:div|li)[^>]*class="[^"]*(?:ticket|biglietto)[^"]*"[^>]*>.*?'
                         r'data-(?:ticket-)?id="(?P<offer_id>[^"]+)".*?'
                         r'(?:€|EUR)\s*(?P<price>[\d,\.]+).*?'
                         r'(?:settore|sector)[^>]*>(?P<section>[^<]+)',
                'json_data': r'window\.__INITIAL_STATE__\s*=\s*({[^;]+});',
            }
        }
        
        # Load from config
        patterns_from_config = self.monitor_config.get('detection_patterns', {})
        compiled_patterns: Dict[PlatformType, Dict[str, Pattern]] = {}
        
        for platform in PlatformType:
            compiled_patterns[platform] = {}
            
            # Use config patterns if available, otherwise use defaults
            platform_patterns = patterns_from_config.get(platform.value, default_patterns.get(platform, {}))
            
            for key, pattern_str in platform_patterns.items():
                try:
                    compiled_patterns[platform][key] = re.compile(
                        pattern_str, 
                        re.DOTALL | re.IGNORECASE | re.MULTILINE
                    )
                except Exception as e:
                    logger.error(f"Failed to compile pattern {key} for {platform.value}: {e}")
                    # Use a simple fallback pattern
                    compiled_patterns[platform][key] = re.compile(r'(?!.*)')  # Never matches
        
        return compiled_patterns
    
    async def _parse_opportunities(self,
                                  platform: PlatformType,
                                  url: str,
                                  event_name: str,
                                  priority: PriorityLevel,
                                  content_bytes: bytes,
                                  from_cache: bool = False) -> List[EnhancedTicketOpportunity]:
        """Advanced parsing with multiple strategies"""
        
        opportunities: List[EnhancedTicketOpportunity] = []
        
        if not content_bytes:
            return opportunities
        
        try:
            content_str = content_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to decode content for {event_name}: {e}")
            return opportunities
        
        # Try JSON parsing first (faster and more reliable)
        json_opportunities = await self._parse_json_opportunities(platform, url, event_name, priority, content_str)
        opportunities.extend(json_opportunities)
        
        # Fall back to regex parsing if no JSON results
        if not opportunities:
            regex_opportunities = await self._parse_regex_opportunities(
                platform, url, event_name, priority, content_str, from_cache
            )
            opportunities.extend(regex_opportunities)
        
        # Deduplicate and enrich opportunities
        unique_opportunities = self._deduplicate_opportunities(opportunities)
        
        # Log detection metrics
        if unique_opportunities:
            self.metrics[f"{platform.value}:{event_name}"].detections += len(unique_opportunities)
            self.metrics[f"{platform.value}:{event_name}"].last_detection = datetime.now()
            logger.warning(f"🎯 DETECTED {len(unique_opportunities)} opportunities for {event_name} on {platform.value}!")
        
        return unique_opportunities
    
    async def _parse_json_opportunities(self,
                                       platform: PlatformType,
                                       url: str,
                                       event_name: str,
                                       priority: PriorityLevel,
                                       content: str) -> List[EnhancedTicketOpportunity]:
        """Parse opportunities from JSON data in page"""
        
        opportunities = []
        
        # Platform-specific JSON extraction
        json_pattern = self.detection_patterns.get(platform, {}).get('json_data')
        if not json_pattern:
            return opportunities
        
        try:
            # Find JSON data in page
            match = json_pattern.search(content)
            if match:
                json_str = match.group(1) if match.lastindex else match.group(0)
                data = json.loads(json_str)
                
                # Extract offers based on platform structure
                if platform == PlatformType.FANSALE:
                    offers = data.get('pageData', {}).get('offers', [])
                elif platform == PlatformType.TICKETMASTER:
                    offers = data.get('_embedded', {}).get('offers', [])
                elif platform == PlatformType.VIVATICKET:
                    offers = data.get('tickets', {}).get('available', [])
                else:
                    offers = []
                
                # Parse each offer
                for offer in offers[:50]:  # Limit to prevent overwhelming
                    try:
                        opp = self._create_opportunity_from_json(
                            platform, url, event_name, priority, offer
                        )
                        if opp:
                            opportunities.append(opp)
                    except Exception as e:
                        logger.debug(f"Failed to parse JSON offer: {e}")
        
        except Exception as e:
            logger.debug(f"JSON parsing failed for {platform.value}: {e}")
        
        return opportunities
    
    async def _parse_regex_opportunities(self,
                                        platform: PlatformType,
                                        url: str,
                                        event_name: str,
                                        priority: PriorityLevel,
                                        content: str,
                                        from_cache: bool) -> List[EnhancedTicketOpportunity]:
        """Parse opportunities using regex patterns"""
        
        opportunities = []
        platform_patterns = self.detection_patterns.get(platform, {})
        
        if not platform_patterns:
            return opportunities
        
        # Try multiple pattern strategies
        for pattern_name, pattern in platform_patterns.items():
            if pattern_name.startswith('json'):  # Skip JSON patterns
                continue
            
            matches_found = 0
            for match in pattern.finditer(content):
                if matches_found >= 100:  # Prevent excessive parsing
                    break
                
                try:
                    offer_data = match.groupdict()
                    
                    # Extract and validate data
                    offer_id = offer_data.get('offer_id', f"{random.randint(10000, 99999)}")
                    price_str = (offer_data.get('price') or offer_data.get('price_alt', '0'))
                    price = self._parse_price(price_str)
                    section = offer_data.get('section') or offer_data.get('section_name', 'General')
                    quantity = int(offer_data.get('quantity', 1))
                    
                    # Skip invalid offers
                    if price <= 0 or not section:
                        continue
                    
                    # Create unique opportunity ID
                    opp_id = self._generate_opportunity_id(
                        platform, event_name, offer_id, section, price
                    )
                    
                    # Build offer URL
                    offer_url = self._build_offer_url(platform, url, offer_id)
                    
                    opp = EnhancedTicketOpportunity(
                        id=opp_id,
                        platform=platform,
                        event_name=event_name,
                        url=url,
                        offer_url=offer_url,
                        section=section.strip(),
                        price=price,
                        quantity=quantity,
                        detected_at=datetime.now(),
                        priority=priority,
                        detection_method=f"regex_{pattern_name}",
                        metadata={
                            'from_cache': from_cache,
                            'pattern': pattern_name,
                            'raw_match': match.group(0)[:200]
                        }
                    )
                    
                    opportunities.append(opp)
                    matches_found += 1
                    
                except Exception as e:
                    logger.debug(f"Error parsing regex match: {e}")
        
        return opportunities
    
    def _create_opportunity_from_json(self,
                                     platform: PlatformType,
                                     url: str,
                                     event_name: str,
                                     priority: PriorityLevel,
                                     offer_data: Dict[str, Any]) -> Optional[EnhancedTicketOpportunity]:
        """Create opportunity from JSON offer data"""
        
        try:
            # Platform-specific field mapping
            if platform == PlatformType.FANSALE:
                offer_id = str(offer_data.get('id', ''))
                price = float(offer_data.get('price', {}).get('amount', 0))
                section = offer_data.get('section', {}).get('name', 'General')
                quantity = offer_data.get('quantity', 1)
                
            elif platform == PlatformType.TICKETMASTER:
                offer_id = offer_data.get('offerId', '')
                price = float(offer_data.get('price', {}).get('total', 0))
                section = offer_data.get('area', {}).get('name', 'General')
                quantity = offer_data.get('quantity', {}).get('available', 1)
                
            elif platform == PlatformType.VIVATICKET:
                offer_id = str(offer_data.get('ticketId', ''))
                price = float(offer_data.get('price', 0))
                section = offer_data.get('sector', 'General')
                quantity = offer_data.get('available', 1)
                
            else:
                return None
            
            if not offer_id or price <= 0:
                return None
            
            opp_id = self._generate_opportunity_id(
                platform, event_name, offer_id, section, price
            )
            
            offer_url = self._build_offer_url(platform, url, offer_id)
            
            return EnhancedTicketOpportunity(
                id=opp_id,
                platform=platform,
                event_name=event_name,
                url=url,
                offer_url=offer_url,
                section=section,
                price=price,
                quantity=quantity,
                detected_at=datetime.now(),
                priority=priority,
                detection_method="json_parse",
                metadata={'source': 'json', 'offer_data': offer_data}
            )
            
        except Exception as e:
            logger.debug(f"Failed to create opportunity from JSON: {e}")
            return None
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price from various formats"""
        if not price_str:
            return 0.0
        
        # Remove currency symbols and normalize
        price_str = re.sub(r'[€$£¥]', '', price_str)
        price_str = price_str.replace('.', '').replace(',', '.')
        price_str = re.sub(r'[^\d.]', '', price_str)
        
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    
    def _generate_opportunity_id(self, platform: PlatformType, event_name: str, 
                                offer_id: str, section: str, price: float) -> str:
        """Generate unique, stable opportunity ID"""
        
        # Create deterministic hash
        hash_input = f"{platform.value}:{event_name}:{offer_id}:{section}:{price:.2f}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        
        # Add timestamp component for uniqueness
        timestamp = int(datetime.now().timestamp())
        
        return f"{platform.value}_{hash_value}_{timestamp}"
    
    def _build_offer_url(self, platform: PlatformType, base_url: str, offer_id: str) -> str:
        """Build platform-specific offer URL"""
        
        if platform == PlatformType.FANSALE:
            return f"{base_url}#offer={offer_id}"
        elif platform == PlatformType.TICKETMASTER:
            return f"{base_url}/checkout?offer={offer_id}"
        elif platform == PlatformType.VIVATICKET:
            return f"{base_url}?ticket={offer_id}"
        else:
            return f"{base_url}#id={offer_id}"
    
    def _deduplicate_opportunities(self, opportunities: List[EnhancedTicketOpportunity]) -> List[EnhancedTicketOpportunity]:
        """Remove duplicate opportunities, keeping best quality"""
        
        seen = {}
        for opp in opportunities:
            # Create deduplication key
            key = (opp.platform, opp.event_name, opp.section, opp.price)
            
            if key not in seen or opp.quantity > seen[key].quantity:
                seen[key] = opp
        
        return list(seen.values())
    
    async def check_ultra_efficient(self,
                                   platform: PlatformType,
                                   url: str,
                                   event_name: str,
                                   priority: PriorityLevel) -> List[EnhancedTicketOpportunity]:
        """Ultra-efficient checking with advanced stealth features"""
        
        check_key = f"{platform.value}:{url}"
        start_time = time.time()
        
        # Anti-burst protection
        await self._enforce_rate_limiting()
        
        # Check minimum interval with jitter
        min_interval = self._calculate_adaptive_interval(platform, priority, url)
        
        if check_key in self.last_check_times:
            elapsed = (datetime.now() - self.last_check_times[check_key]).total_seconds()
            if elapsed < min_interval:
                logger.debug(f"Skipping {check_key}, too soon ({elapsed:.1f}s < {min_interval:.1f}s)")
                return []
        
        # Try cache first
        cached_content = await self.response_cache.get(url, max_age_seconds=self.cache_max_age_s)
        if cached_content:
            logger.info(f"Cache hit for {url} ({event_name})")
            self.metrics[check_key].successful_checks += 1
            self.last_check_times[check_key] = datetime.now()
            return await self._parse_opportunities(platform, url, event_name, priority, cached_content, from_cache=True)
        
        # Check data limits
        if self.data_tracker.is_approaching_limit(threshold=0.9):
            logger.warning(f"Data limit approaching, skipping {event_name}")
            return []
        
        # Select profile with circuit breaker
        profile = await self._select_profile_with_circuit_breaker(platform)
        if not profile:
            logger.warning(f"No suitable profile for {platform.value} - {event_name}")
            return []
        
        logger.debug(f"Selected profile {profile.profile_id} for {event_name}")
        
        try:
            # Get HTTP client with stealth configuration
            http_client = await self.connection_pool.get_client(profile, use_tls_fingerprint=True)
            
            # Build stealth headers
            headers = self.request_builder.build_headers(profile, url)
            
            # Add timing variation
            await self._add_human_timing()
            
            # Make request
            response = await http_client.get(
                url, 
                headers=headers, 
                timeout=self._get_adaptive_timeout(platform),
                follow_redirects=True
            )
            
            response.raise_for_status()
            
            # Process response
            content = await response.aread()
            response_time = time.time() - start_time
            
            # Update metrics
            self.metrics[check_key].successful_checks += 1
            self.metrics[check_key].response_times.append(response_time)
            self.data_tracker.add_usage(len(content), platform.value, profile.profile_id)
            
            # Cache response
            await self.response_cache.put(
                url, 
                content, 
                headers=headers, 
                response_headers=dict(response.headers)
            )
            
            # Update state
            self.last_check_times[check_key] = datetime.now()
            if hasattr(profile, '_last_url'):
                profile._last_url = url
            
            # Record success
            await self.profile_manager.record_feedback(
                profile_id=profile.profile_id,
                event=DetectionEvent.SUCCESS,
                platform=platform.value,
                metadata={
                    'url': url,
                    'status': response.status_code,
                    'response_time': response_time,
                    'size': len(content)
                }
            )
            
            # Parse opportunities
            return await self._parse_opportunities(platform, url, event_name, priority, content)
            
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e, profile, platform, url, check_key)
            return []
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout for {url} with profile {profile.profile_id}")
            self.metrics[check_key].failed_checks += 1
            await self.profile_manager.record_feedback(
                profile_id=profile.profile_id,
                event=DetectionEvent.RATE_LIMIT,
                platform=platform.value,
                metadata={'url': url, 'error': 'timeout'}
            )
            return []
            
        except Exception as e:
            logger.error(f"Unexpected error for {event_name}: {e}", exc_info=True)
            self.metrics[check_key].failed_checks += 1
            await self.profile_manager.record_feedback(
                profile_id=profile.profile_id,
                event=DetectionEvent.HARD_BLOCK,
                platform=platform.value,
                metadata={'url': url, 'error': str(e)}
            )
            return []
    
    async def _enforce_rate_limiting(self):
        """Enforce rate limiting to avoid detection"""
        
        now = time.time()
        self.request_timestamps.append(now)
        
        # Remove old timestamps
        cutoff = now - 10  # 10 second window
        while self.request_timestamps and self.request_timestamps[0] < cutoff:
            self.request_timestamps.popleft()
        
        # Check burst threshold
        if len(self.request_timestamps) >= self.burst_detection_threshold:
            sleep_time = 10 - (now - self.request_timestamps[0])
            if sleep_time > 0:
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
    
    async def _select_profile_with_circuit_breaker(self, platform: PlatformType) -> Optional[BrowserProfile]:
        """Select profile with circuit breaker logic"""
        
        # Try to get a profile that hasn't failed recently
        for attempt in range(3):
            profile = await self.profile_manager.get_profile_for_platform(
                platform=platform.to_core_platform(),
                require_session=False
            )
            
            if profile:
                # Check if profile has recent failures
                recent_failures = getattr(profile, '_recent_failures', 0)
                if recent_failures < self.circuit_breaker_threshold:
                    return profile
                
                # Profile is in circuit breaker state
                logger.debug(f"Profile {profile.profile_id} in circuit breaker state")
                
            await asyncio.sleep(0.5 * (attempt + 1))
        
        return None
    
    async def _add_human_timing(self):
        """Add human-like timing variations"""
        
        # Base delay with jitter
        base_delay = random.uniform(0.1, 0.3)
        
        # Occasionally add longer "thinking" pauses
        if random.random() < 0.1:
            base_delay += random.uniform(0.5, 1.5)
        
        await asyncio.sleep(base_delay)
    
    def _get_adaptive_timeout(self, platform: PlatformType) -> float:
        """Get platform-specific timeout with adaptation"""
        
        base_timeout = 20.0
        
        # Adjust based on platform
        platform_multipliers = {
            PlatformType.TICKETMASTER: 1.5,  # Often slower
            PlatformType.VIVATICKET: 1.2,
            PlatformType.FANSALE: 1.0
        }
        
        timeout = base_timeout * platform_multipliers.get(platform, 1.0)
        
        # Add jitter
        timeout *= random.uniform(0.9, 1.1)
        
        return timeout
    
    def _calculate_adaptive_interval(self, platform: PlatformType, priority: PriorityLevel, url: str) -> float:
        """Calculate adaptive check interval with stealth considerations"""
        
        # Base intervals by platform
        platform_intervals = {
            PlatformType.FANSALE: 45,
            PlatformType.TICKETMASTER: 60,
            PlatformType.VIVATICKET: 50
        }
        
        base_interval = platform_intervals.get(platform, self.default_check_interval)
        
        # Priority adjustments
        priority_multipliers = {
            PriorityLevel.CRITICAL: 0.5,
            PriorityLevel.HIGH: 0.7,
            PriorityLevel.NORMAL: 1.0,
            PriorityLevel.LOW: 1.5,
        }
        
        interval = base_interval * priority_multipliers.get(priority, 1.0)
        
        # Adapt based on metrics
        check_key = f"{platform.value}:{url}"
        metrics = self.metrics.get(check_key)
        
        if metrics:
            # Increase interval if many recent failures
            failure_rate = metrics.failed_checks / max(metrics.successful_checks + metrics.failed_checks, 1)
            if failure_rate > 0.5:
                interval *= 2.0
            elif failure_rate > 0.3:
                interval *= 1.5
            
            # Decrease interval if recent detections
            if metrics.last_detection and (datetime.now() - metrics.last_detection).total_seconds() < 300:
                interval *= 0.7
        
        # Data limit adjustments
        if self.data_tracker.is_approaching_limit(threshold=0.8):
            interval *= 1.5
            logger.debug(f"Data limit >80%, increased interval to {interval:.1f}s")
        elif self.data_tracker.is_approaching_limit(threshold=0.95):
            interval *= 3.0
            logger.warning(f"Data limit >95%, interval now {interval:.1f}s")
        
        # Apply jitter
        jitter = random.uniform(*self.jitter_range)
        interval *= jitter
        
        # Enforce minimum
        min_allowed = self.monitor_config.get('min_monitor_interval_s', 5.0)
        final_interval = max(min_allowed, interval)
        
        logger.debug(f"Adaptive interval for {platform.value} ({priority.name}): {final_interval:.2f}s")
        
        return final_interval
    
    def _handle_http_error(self, error: httpx.HTTPStatusError, profile: BrowserProfile,
                          platform: PlatformType, url: str, check_key: str):
        """Handle HTTP errors with appropriate feedback"""
        
        status_code = error.response.status_code
        self.metrics[check_key].failed_checks += 1
        
        # Track failures on profile
        if not hasattr(profile, '_recent_failures'):
            profile._recent_failures = 0
        profile._recent_failures += 1
        
        # Determine detection event type
        if status_code in [403, 401]:
            event = DetectionEvent.HARD_BLOCK
            logger.warning(f"Hard block detected ({status_code}) for {url}")
        elif status_code == 429:
            event = DetectionEvent.RATE_LIMIT
            logger.warning(f"Rate limit hit for {url}")
        elif status_code >= 500:
            event = DetectionEvent.CAPTCHA  # Server errors might indicate detection
            logger.warning(f"Server error ({status_code}) for {url}")
        else:
            event = DetectionEvent.SOFT_BLOCK
            logger.warning(f"Soft block ({status_code}) for {url}")
        
        # Record feedback asynchronously
        asyncio.create_task(
            self.profile_manager.record_feedback(
                profile_id=profile.profile_id,
                event=event,
                platform=platform.value,
                metadata={
                    'url': url,
                    'status': status_code,
                    'error': str(error)
                }
            )
        )
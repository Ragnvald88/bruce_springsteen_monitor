"""
Advanced Data Usage and Performance Tracking System
Provides real-time monitoring of all system metrics
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import psutil
import json
from pathlib import Path
import aiofiles

from ..utils.logging import get_logger
import re
from collections import deque
import hashlib

logger = get_logger(__name__)


@dataclass
class DataUsageMetrics:
    """Container for data usage metrics"""
    platform: str
    timestamp: datetime = field(default_factory=datetime.now)
    bytes_sent: int = 0
    bytes_received: int = 0
    requests_made: int = 0
    images_blocked: int = 0
    scripts_blocked: int = 0
    
    @property
    def total_bytes(self) -> int:
        return self.bytes_sent + self.bytes_received
    
    @property
    def total_mb(self) -> float:
        return self.total_bytes / (1024 * 1024)


class DataUsageTracker:
    """
    Comprehensive data usage tracking system
    Monitors network usage, performance metrics, and resource consumption
    """
    
    def __init__(self, log_dir: Path = Path("logs/telemetry")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics storage
        self.session_metrics: Dict[str, DataUsageMetrics] = {}
        self.platform_totals: Dict[str, DataUsageMetrics] = {}
        
        # Real-time monitoring
        self.monitoring_active = False
        self.monitor_task = None
        
        # Network baseline
        self._network_baseline = None
        self._last_check = None
        
        # ADDED: Cache for data optimization
        self.request_cache = {}
        self.last_content_hash = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def start_monitoring(self):
        """Start real-time monitoring"""
        self.monitoring_active = True
        self._network_baseline = psutil.net_io_counters()
        self._last_check = time.time()
        
        # Start background monitoring
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Data usage monitoring started")
        
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                current_stats = psutil.net_io_counters()
                current_time = time.time()
                
                # Calculate deltas
                bytes_sent_delta = current_stats.bytes_sent - self._network_baseline.bytes_sent
                bytes_recv_delta = current_stats.bytes_recv - self._network_baseline.bytes_recv
                time_delta = current_time - self._last_check
                
                # Log if significant data usage
                if bytes_sent_delta + bytes_recv_delta > 1024 * 1024:  # 1MB threshold
                    await self.log_data_spike(
                        bytes_sent_delta, 
                        bytes_recv_delta,
                        time_delta
                    )
                
                # Update baseline
                self._network_baseline = current_stats
                self._last_check = current_time
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def stop_monitoring(self):
        """Stop monitoring and cleanup"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Data usage monitoring stopped")
    
    async def log_data_spike(self, bytes_sent: int, bytes_recv: int, time_delta: float):
        """Log significant data usage spike"""
        spike_data = {
            'timestamp': datetime.now().isoformat(),
            'bytes_sent': bytes_sent,
            'bytes_recv': bytes_recv,
            'total_mb': (bytes_sent + bytes_recv) / (1024 * 1024),
            'duration_seconds': time_delta,
            'rate_mbps': ((bytes_sent + bytes_recv) * 8) / (time_delta * 1024 * 1024) if time_delta > 0 else 0
        }
        
        log_file = self.log_dir / f"spikes_{datetime.now().strftime('%Y%m%d')}.jsonl"
        async with aiofiles.open(log_file, 'a') as f:
            await f.write(json.dumps(spike_data) + '\n')
        
        logger.warning(f"Data spike detected: {spike_data['total_mb']:.2f} MB in {time_delta:.1f}s")
    
    async def track_request(self, platform: str, url: str, 
                          method: str = "GET", 
                          response_size: int = 0,
                          blocked_resources: Dict[str, int] = None):
        """Track individual request data usage"""
        
        # Get or create platform metrics
        if platform not in self.platform_totals:
            self.platform_totals[platform] = DataUsageMetrics(platform=platform)
        
        metrics = self.platform_totals[platform]
        metrics.requests_made += 1
        metrics.bytes_received += response_size
        
        # Track blocked resources
        if blocked_resources:
            metrics.images_blocked += blocked_resources.get('images', 0)
            metrics.scripts_blocked += blocked_resources.get('scripts', 0)
        
        # Log detailed request
        await self._log_request({
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'url': url,
            'method': method,
            'response_size': response_size,
            'blocked': blocked_resources or {},
            'total_session_mb': metrics.total_mb
        })
    
    async def _log_request(self, request_data: Dict[str, Any]):
        """Log request details to file"""
        log_file = self.log_dir / f"requests_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        async with aiofiles.open(log_file, 'a') as f:
            await f.write(json.dumps(request_data) + '\n')
    
    def get_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        total_mb = sum(m.total_mb for m in self.platform_totals.values())
        
        return {
            'total_data_mb': round(total_mb, 2),
            'platforms': {
                platform: {
                    'data_mb': round(metrics.total_mb, 2),
                    'requests': metrics.requests_made,
                    'images_blocked': metrics.images_blocked,
                    'scripts_blocked': metrics.scripts_blocked,
                    'efficiency_score': self._calculate_efficiency(metrics)
                }
                for platform, metrics in self.platform_totals.items()
            },
            'recommendations': self._generate_recommendations(total_mb)
        }
    
    def _calculate_efficiency(self, metrics: DataUsageMetrics) -> float:
        """Calculate data efficiency score (0-100)"""
        if metrics.requests_made == 0:
            return 100.0
        
        # Base score on data per request
        mb_per_request = metrics.total_mb / metrics.requests_made
        
        # Ideal is < 0.5 MB per request
        if mb_per_request < 0.5:
            base_score = 100
        elif mb_per_request < 1.0:
            base_score = 80
        elif mb_per_request < 2.0:
            base_score = 60
        else:
            base_score = 40
        
        # Bonus for blocking resources
        block_bonus = min(20, (metrics.images_blocked + metrics.scripts_blocked) * 0.1)
        
        return min(100, base_score + block_bonus)
    
    def _generate_recommendations(self, total_mb: float) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if total_mb > 1000:
            recommendations.append("Enable aggressive image blocking to reduce data usage")
        
        # Platform-specific recommendations
        for platform, metrics in self.platform_totals.items():
            if metrics.requests_made > 0:
                mb_per_request = metrics.total_mb / metrics.requests_made
                if mb_per_request > 2.0:
                    recommendations.append(f"High data usage on {platform} - consider enabling request filtering")
                
                if metrics.images_blocked == 0 and metrics.total_mb > 100:
                    recommendations.append(f"Enable image blocking for {platform} to reduce data usage")
        
        return recommendations
    
    async def generate_report(self) -> str:
        """Generate a detailed usage report"""
        summary = self.get_summary()
        
        report = []
        report.append("=== Data Usage Report ===")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Data Used: {summary['total_data_mb']} MB")
        report.append("")
        
        # Platform breakdown
        report.append("Platform Breakdown:")
        for platform, data in summary['platforms'].items():
            report.append(f"  {platform}:")
            report.append(f"    - Data Used: {data['data_mb']} MB")
            report.append(f"    - Requests: {data['requests']}")
            report.append(f"    - Efficiency: {data['efficiency_score']:.0f}%")
            report.append(f"    - Resources Blocked: {data['images_blocked']} images, {data['scripts_blocked']} scripts")
        
        # Recommendations
        if summary['recommendations']:
            report.append("")
            report.append("Optimization Recommendations:")
            for rec in summary['recommendations']:
                report.append(f"  • {rec}")
        
        return "\n".join(report)
    
    # ADDED: Smart content checking with caching
    async def smart_check(self, page: Any, url: str, platform: str) -> Dict[str, Any]:
        """Only fetch if content likely changed - minimize data usage"""
        cache_key = f"{platform}:{url}"
        
        # Check cache first
        if cache_key in self.request_cache:
            cache_entry = self.request_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                logger.debug(f"Using cached data for {url}")
                return cache_entry['data']
        
        # Try HEAD request first to check if content changed
        try:
            if hasattr(page, 'request'):
                head_response = await page.request.head(url)
                last_modified = head_response.headers.get('last-modified', '')
                etag = head_response.headers.get('etag', '')
                
                # Check if content unchanged
                content_hash = hashlib.md5(f"{last_modified}{etag}".encode()).hexdigest()
                if content_hash == self.last_content_hash.get(cache_key):
                    logger.debug(f"Content unchanged for {url}, using cache")
                    return self.request_cache.get(cache_key, {}).get('data', {})
                
                self.last_content_hash[cache_key] = content_hash
        except:
            pass
        
        # Fetch only ticket-specific elements instead of full page
        if hasattr(page, 'evaluate'):
            # Playwright
            ticket_data = await page.evaluate("""
                () => {
                    const tickets = document.querySelectorAll('[class*="ticket"], [class*="offer"], [class*="biglietto"]');
                    const data = {
                        tickets: [],
                        hasTickets: false,
                        pageTitle: document.title,
                        timestamp: Date.now()
                    };
                    
                    tickets.forEach(ticket => {
                        const ticketInfo = {
                        text: ticket.innerText.slice(0, 200),  // Limit text
                        available: !ticket.classList.contains('sold-out') && 
                                  !ticket.classList.contains('esaurito'),
                        price: null,
                        section: null
                    };
                    
                    // Extract price
                    const priceEl = ticket.querySelector('[class*="price"], [class*="prezzo"]');
                    if (priceEl) {
                        ticketInfo.price = priceEl.innerText;
                    }
                    
                    // Extract section
                    const sectionEl = ticket.querySelector('[class*="section"], [class*="settore"]');
                    if (sectionEl) {
                        ticketInfo.section = sectionEl.innerText;
                    }
                    
                    data.tickets.push(ticketInfo);
                });
                
                data.hasTickets = data.tickets.length > 0;
                return data;
            }
        """)
        else:
            # Selenium
            ticket_data = page.execute_script("""
                const tickets = document.querySelectorAll('[class*="ticket"], [class*="offer"], [class*="biglietto"]');
                const data = {
                    tickets: [],
                    hasTickets: false,
                    pageTitle: document.title,
                    timestamp: Date.now()
                };
                
                tickets.forEach(ticket => {
                    const ticketInfo = {
                        text: ticket.innerText.slice(0, 200),  // Limit text
                        available: !ticket.classList.contains('sold-out') && 
                                  !ticket.classList.contains('esaurito'),
                        price: null,
                        section: null
                    };
                    
                    // Extract price
                    const priceEl = ticket.querySelector('[class*="price"], [class*="prezzo"]');
                    if (priceEl) {
                        ticketInfo.price = priceEl.innerText;
                    }
                    
                    // Extract section
                    const sectionEl = ticket.querySelector('[class*="section"], [class*="settore"]');
                    if (sectionEl) {
                        ticketInfo.section = sectionEl.innerText;
                    }
                    
                    data.tickets.push(ticketInfo);
                });
                
                data.hasTickets = data.tickets.length > 0;
                return data;
            """)
        
        # Cache the result
        self.request_cache[cache_key] = {
            'data': ticket_data,
            'timestamp': time.time()
        }
        
        # Track the optimized request
        await self.track_request(
            platform=platform,
            url=url,
            response_size=len(json.dumps(ticket_data)),  # Much smaller than full page
            blocked_resources={'images': 999, 'scripts': 999}  # Indicate we blocked most resources
        )
        
        return ticket_data

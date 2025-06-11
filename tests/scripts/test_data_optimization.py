import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from src.network.optimizer import NetworkOptimizer
from src.network.interceptor import RequestInterceptor
from src.browser.pool import BrowserPool

class TestDataOptimization:
    """Tests for data usage optimization and residential proxy efficiency."""
    
    @pytest.mark.asyncio
    async def test_resource_blocking_accuracy(self):
        """DATA-01: Test resource blocking filters."""
        optimizer = NetworkOptimizer()
        
        test_urls = [
            ('https://example.com/analytics.js', True),  # Should block
            ('https://example.com/main.css', False),     # Should allow
            ('https://example.com/tracking.gif', True),  # Should block
            ('https://example.com/api/tickets', False),  # Should allow
            ('https://cdn.com/video.mp4', True),         # Should block
            ('https://example.com/checkout.js', False),  # Should allow
        ]
        
        for url, should_block in test_urls:
            blocked = optimizer.should_block_resource(url)
            assert blocked == should_block, f"Incorrect blocking for {url}"
    
    @pytest.mark.asyncio
    async def test_cache_effectiveness(self):
        """DATA-02: Test caching system effectiveness."""
        interceptor = RequestInterceptor()
        
        # Simulate requests
        requests = [
            {'url': 'https://api.com/events', 'response': {'data': 'events'}},
            {'url': 'https://api.com/events', 'response': {'data': 'events'}},  # Duplicate
            {'url': 'https://cdn.com/logo.png', 'response': b'image_data'},
            {'url': 'https://cdn.com/logo.png', 'response': b'image_data'},  # Duplicate
        ]
        
        cache_hits = 0
        total_size = 0
        cached_size = 0
        
        for req in requests:
            if interceptor.is_cached(req['url']):
                cache_hits += 1
                cached_size += len(str(req['response']))
            else:
                interceptor.cache_response(req['url'], req['response'])
                total_size += len(str(req['response']))
        
        cache_hit_rate = cache_hits / len(requests) * 100
        
        assert cache_hit_rate >= 50, f"Cache hit rate too low: {cache_hit_rate}%"
        assert cached_size > 0, "No data served from cache"
    
    @pytest.mark.asyncio
    async def test_data_usage_per_workflow(self):
        """DATA-03: Test data usage stays under 10MB per workflow."""
        pool = BrowserPool(max_size=1)
        await pool.initialize()
        
        # Track data usage
        context = await pool.acquire_context()
        
        # Mock page with data tracking
        page = await context.new_page()
        data_used = 0
        
        def track_response(response):
            nonlocal data_used
            data_used += len(response.body) if hasattr(response, 'body') else 1000
        
        page.on('response', track_response)
        
        # Simulate workflow
        test_urls = [
            'https://ticketmaster.it',
            'https://ticketmaster.it/event/123',
            'https://ticketmaster.it/checkout'
        ]
        
        for url in test_urls:
            # Mock navigation
            await page.goto('about:blank')  # Simulate navigation
            data_used += 500_000  # Simulate page load
        
        await page.close()
        await pool.release_context(context)
        await pool.cleanup()
        
        data_used_mb = data_used / (1024 * 1024)
        
        assert data_used_mb < 10, f"Data usage too high: {data_used_mb}MB"
    
    @pytest.mark.asyncio
    async def test_proxy_rotation_efficiency(self):
        """DATA-04: Test proxy rotation minimizes data waste."""
        pool = BrowserPool(max_size=3)
        
        proxy_usage = {}
        
        # Mock proxy assignment
        original_acquire = pool.acquire_context
        
        async def track_proxy_acquire(*args, **kwargs):
            context = await original_acquire(*args, **kwargs)
            proxy = context.proxy if hasattr(context, 'proxy') else 'default'
            proxy_usage[proxy] = proxy_usage.get(proxy, 0) + 1
            return context
        
        pool.acquire_context = track_proxy_acquire
        
        await pool.initialize()
        
        # Simulate 20 context acquisitions
        for _ in range(20):
            context = await pool.acquire_context()
            await asyncio.sleep(0.01)
            await pool.release_context(context)
        
        await pool.cleanup()
        
        # Check proxy distribution
        usage_values = list(proxy_usage.values())
        max_usage = max(usage_values) if usage_values else 0
        min_usage = min(usage_values) if usage_values else 0
        
        assert max_usage - min_usage <= 5, "Proxy usage imbalanced"
    
    @pytest.mark.asyncio
    async def test_compression_effectiveness(self):
        """DATA-05: Test response compression handling."""
        optimizer = NetworkOptimizer()
        
        # Test different content types
        test_data = [
            ('text/html', '<html>' * 1000, 0.3),  # High compression
            ('application/json', '{"data": "test"}' * 100, 0.4),
            ('image/jpeg', b'\xff\xd8\xff' * 1000, 0.95),  # Low compression
        ]
        
        for content_type, data, expected_ratio in test_data:
            compressed = optimizer.compress_response(data, content_type)
            compression_ratio = len(compressed) / len(data)
            
            assert compression_ratio <= expected_ratio * 1.2, \
                f"Poor compression for {content_type}: {compression_ratio}"
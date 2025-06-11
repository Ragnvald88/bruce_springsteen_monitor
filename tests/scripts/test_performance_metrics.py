import pytest
import asyncio
import time
import psutil
import tracemalloc
from memory_profiler import profile
import aiohttp
from unittest.mock import AsyncMock, patch

from src.browser.pool import BrowserPool
from src.network.optimizer import NetworkOptimizer
from src.orchestration.workflow import WorkflowOrchestrator
from src.main import StealthMaster

class TestPerformanceMetrics:
    """Tests for performance, resource usage, and efficiency."""
    
    @pytest.mark.asyncio
    async def test_browser_pool_acquisition_latency(self):
        """PERF-01: Test browser context acquisition time."""
        pool = BrowserPool(max_size=5)
        await pool.initialize()
        
        acquisition_times = []
        
        for _ in range(20):
            start = time.perf_counter()
            context = await pool.acquire_context()
            acquisition_time = (time.perf_counter() - start) * 1000  # ms
            acquisition_times.append(acquisition_time)
            await pool.release_context(context)
        
        avg_time = sum(acquisition_times) / len(acquisition_times)
        p95_time = sorted(acquisition_times)[int(len(acquisition_times) * 0.95)]
        
        await pool.cleanup()
        
        assert avg_time < 500, f"Average acquisition time too high: {avg_time}ms"
        assert p95_time < 2000, f"P95 acquisition time too high: {p95_time}ms"
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """PERF-02: Test for memory leaks over multiple operations."""
        tracemalloc.start()
        
        async def workflow_iteration():
            pool = BrowserPool(max_size=2)
            await pool.initialize()
            
            # Simulate 10 workflows
            for _ in range(10):
                context = await pool.acquire_context()
                page = await context.new_page()
                await page.goto("about:blank")
                await page.close()
                await pool.release_context(context)
            
            await pool.cleanup()
        
        # Baseline memory
        await workflow_iteration()
        snapshot1 = tracemalloc.take_snapshot()
        
        # Run 5 more iterations
        for _ in range(5):
            await workflow_iteration()
        
        snapshot2 = tracemalloc.take_snapshot()
        
        # Calculate memory growth
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_growth = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
        growth_percentage = (total_growth / snapshot1.size) * 100
        
        tracemalloc.stop()
        
        assert growth_percentage < 5, f"Memory growth too high: {growth_percentage}%"
    
    @pytest.mark.asyncio
    async def test_network_data_usage(self):
        """PERF-03: Test network data usage optimization."""
        optimizer = NetworkOptimizer()
        
        # Mock network requests
        mock_requests = [
            {'url': 'https://example.com/image.jpg', 'size': 500_000},
            {'url': 'https://example.com/script.js', 'size': 100_000},
            {'url': 'https://example.com/style.css', 'size': 50_000},
            {'url': 'https://example.com/data.json', 'size': 20_000},
        ]
        
        # Apply optimization
        optimized_size = 0
        for req in mock_requests:
            if not optimizer.should_block_resource(req['url']):
                optimized_size += req['size'] * optimizer.get_compression_ratio(req['url'])
        
        original_size = sum(req['size'] for req in mock_requests)
        reduction_percentage = ((original_size - optimized_size) / original_size) * 100
        
        assert reduction_percentage > 60, f"Data reduction insufficient: {reduction_percentage}%"
        assert optimized_size < 300_000, f"Optimized size too large: {optimized_size} bytes"
    
    @pytest.mark.asyncio
    async def test_concurrent_context_performance(self):
        """PERF-04: Test performance with maximum concurrent contexts."""
        pool = BrowserPool(max_size=10)
        await pool.initialize()
        
        async def simulate_work(context_id):
            start = time.perf_counter()
            context = await pool.acquire_context()
            
            # Simulate page operations
            page = await context.new_page()
            await page.goto("about:blank")
            await asyncio.sleep(0.5)  # Simulate work
            await page.close()
            
            await pool.release_context(context)
            return time.perf_counter() - start
        
        # Run 20 concurrent operations
        tasks = [simulate_work(i) for i in range(20)]
        start_time = time.perf_counter()
        durations = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        await pool.cleanup()
        
        avg_duration = sum(durations) / len(durations)
        
        assert total_time < 3.0, f"Total execution time too high: {total_time}s"
        assert avg_duration < 2.0, f"Average operation time too high: {avg_duration}s"
    
    @pytest.mark.asyncio
    async def test_cpu_usage_during_operation(self):
        """PERF-05: Monitor CPU usage during intensive operations."""
        process = psutil.Process()
        cpu_samples = []
        
        async def monitor_cpu():
            while len(cpu_samples) < 20:
                cpu_samples.append(process.cpu_percent(interval=0.1))
                await asyncio.sleep(0.1)
        
        # Start CPU monitoring
        monitor_task = asyncio.create_task(monitor_cpu())
        
        # Perform intensive operations
        pool = BrowserPool(max_size=5)
        await pool.initialize()
        
        tasks = []
        for _ in range(10):
            context = await pool.acquire_context()
            page = await context.new_page()
            tasks.append(page.goto("data:text/html,<script>for(let i=0;i<1000000;i++){}</script>"))
        
        await asyncio.gather(*tasks)
        await pool.cleanup()
        
        # Wait for monitoring to complete
        await monitor_task
        
        avg_cpu = sum(cpu_samples) / len(cpu_samples)
        max_cpu = max(cpu_samples)
        
        assert avg_cpu < 80, f"Average CPU usage too high: {avg_cpu}%"
        assert max_cpu < 100, f"Peak CPU usage at maximum: {max_cpu}%"
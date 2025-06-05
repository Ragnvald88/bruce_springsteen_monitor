# src/core/performance_monitor.py - StealthMaster AI Performance Monitor
"""
High-performance monitoring and optimization system
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    connections_active: int
    profiles_active: int
    response_times: Dict[str, float] = field(default_factory=dict)
    cache_hit_rate: float = 0.0
    
    
class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Performance thresholds
        self.cpu_warning_threshold = 80.0
        self.memory_warning_threshold = 85.0
        self.response_time_warning_threshold = 5.0  # seconds
        
        # Component references (set by orchestrator)
        self.connection_manager = None
        self.profile_manager = None
        self.cache_manager = None
        
    def set_components(self, connection_manager=None, profile_manager=None, cache_manager=None):
        """Set component references for monitoring"""
        self.connection_manager = connection_manager
        self.profile_manager = profile_manager
        self.cache_manager = cache_manager
        
    async def start_monitoring(self, interval: float = 30.0):
        """Start performance monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop(interval))
        logger.info(f"Performance monitoring started (interval: {interval}s)")
        
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")
        
    async def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for performance issues
                await self._analyze_performance(metrics)
                
                # Log performance summary every 5 minutes
                if len(self.metrics_history) % 10 == 0:  # Every 10 intervals (5 min if 30s interval)
                    self._log_performance_summary()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Connection metrics
        connections_active = 0
        if self.connection_manager and hasattr(self.connection_manager, 'pools'):
            connections_active = len(self.connection_manager.pools)
        
        # Profile metrics
        profiles_active = 0
        if self.profile_manager:
            if hasattr(self.profile_manager, 'dynamic_profiles'):
                profiles_active += len(self.profile_manager.dynamic_profiles)
            if hasattr(self.profile_manager, 'static_profiles'):
                profiles_active += len(self.profile_manager.static_profiles)
        
        # Cache metrics
        cache_hit_rate = 0.0
        if self.cache_manager and hasattr(self.cache_manager, 'hit_rate'):
            cache_hit_rate = self.cache_manager.hit_rate
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory.used / (1024 * 1024),
            memory_percent=memory.percent,
            connections_active=connections_active,
            profiles_active=profiles_active,
            cache_hit_rate=cache_hit_rate
        )
    
    async def _analyze_performance(self, metrics: PerformanceMetrics):
        """Analyze metrics and trigger optimizations if needed"""
        warnings = []
        
        # CPU check
        if metrics.cpu_percent > self.cpu_warning_threshold:
            warnings.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            await self._optimize_cpu_usage()
        
        # Memory check
        if metrics.memory_percent > self.memory_warning_threshold:
            warnings.append(f"High memory usage: {metrics.memory_percent:.1f}%")
            await self._optimize_memory_usage()
        
        # Connection pool check
        if metrics.connections_active > 50:  # Arbitrary threshold
            warnings.append(f"High connection count: {metrics.connections_active}")
            await self._optimize_connections()
        
        if warnings:
            logger.warning(f"Performance warnings: {'; '.join(warnings)}")
    
    async def _optimize_cpu_usage(self):
        """Optimize CPU usage"""
        logger.info("Optimizing CPU usage...")
        
        # Reduce monitoring frequency temporarily
        if hasattr(self, '_reduce_monitoring_frequency'):
            await self._reduce_monitoring_frequency()
        
        # Request profile manager to reduce background tasks
        if self.profile_manager and hasattr(self.profile_manager, '_reduce_background_activity'):
            await self.profile_manager._reduce_background_activity()
    
    async def _optimize_memory_usage(self):
        """Optimize memory usage"""
        logger.info("Optimizing memory usage...")
        
        # Clear old connections
        if self.connection_manager and hasattr(self.connection_manager, '_cleanup_old_connections'):
            await self.connection_manager._cleanup_old_connections()
        
        # Trigger garbage collection
        import gc
        gc.collect()
        
        # Clear cache if available
        if self.cache_manager and hasattr(self.cache_manager, 'clear_old_entries'):
            await self.cache_manager.clear_old_entries(max_age_seconds=300)  # 5 minutes
    
    async def _optimize_connections(self):
        """Optimize connection usage"""
        logger.info("Optimizing connection usage...")
        
        if self.connection_manager:
            # Mark some clients for rotation
            if hasattr(self.connection_manager, 'force_rotation'):
                await self.connection_manager.force_rotation(max_keep=20)
    
    def _log_performance_summary(self):
        """Log performance summary"""
        if not self.metrics_history:
            return
        
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 measurements
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_mb for m in recent_metrics) / len(recent_metrics)
        current_connections = recent_metrics[-1].connections_active
        current_profiles = recent_metrics[-1].profiles_active
        avg_cache_hit = sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics)
        
        logger.info(
            f"📊 Performance Summary - "
            f"CPU: {avg_cpu:.1f}%, "
            f"Memory: {avg_memory:.0f}MB, "
            f"Connections: {current_connections}, "
            f"Profiles: {current_profiles}, "
            f"Cache Hit Rate: {avg_cache_hit:.2f}"
        )
    
    def get_current_stats(self) -> Optional[Dict[str, Any]]:
        """Get current performance statistics"""
        if not self.metrics_history:
            return None
        
        latest = self.metrics_history[-1]
        
        return {
            "timestamp": latest.timestamp,
            "cpu_percent": latest.cpu_percent,
            "memory_mb": latest.memory_mb,
            "memory_percent": latest.memory_percent,
            "connections_active": latest.connections_active,
            "profiles_active": latest.profiles_active,
            "cache_hit_rate": latest.cache_hit_rate,
            "uptime_seconds": time.time() - self.metrics_history[0].timestamp if self.metrics_history else 0
        }
    
    def get_performance_trend(self) -> Dict[str, str]:
        """Get performance trend analysis"""
        if len(self.metrics_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent = list(self.metrics_history)[-5:]  # Last 5 measurements
        older = list(self.metrics_history)[-10:-5] if len(self.metrics_history) >= 10 else []
        
        if not older:
            return {"trend": "insufficient_history"}
        
        recent_cpu = sum(m.cpu_percent for m in recent) / len(recent)
        older_cpu = sum(m.cpu_percent for m in older) / len(older)
        
        recent_memory = sum(m.memory_mb for m in recent) / len(recent)
        older_memory = sum(m.memory_mb for m in older) / len(older)
        
        trends = {}
        
        # CPU trend
        if recent_cpu > older_cpu * 1.1:
            trends["cpu"] = "increasing"
        elif recent_cpu < older_cpu * 0.9:
            trends["cpu"] = "decreasing"
        else:
            trends["cpu"] = "stable"
        
        # Memory trend
        if recent_memory > older_memory * 1.1:
            trends["memory"] = "increasing"
        elif recent_memory < older_memory * 0.9:
            trends["memory"] = "decreasing"
        else:
            trends["memory"] = "stable"
        
        return trends
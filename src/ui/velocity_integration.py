# stealthmaster/ui/velocity_integration.py
"""
Velocity UI Integration - Connects all UI components for sub-50ms response times
Unifies desktop, mobile, and real-time data flows
"""

import asyncio
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import statistics

from .velocity_dashboard import VelocityDashboard, TicketAlert, PerformanceMetric
from .realtime_engine import RealtimeOrchestrator, RealtimeEvent
from .mobile_interface import MobileInterface


logger = logging.getLogger(__name__)


@dataclass
class VelocityConfig:
    """Configuration for velocity UI system"""
    enable_desktop: bool = True
    enable_mobile: bool = True
    enable_websocket: bool = True
    
    # Performance targets
    target_latency_ms: float = 50.0
    max_latency_ms: float = 100.0
    
    # Network settings
    ws_host: str = "localhost"
    ws_port: int = 8765
    mobile_host: str = "0.0.0.0"
    mobile_port: int = 5000
    
    # Alert settings
    audio_alerts: bool = True
    haptic_feedback: bool = True
    visual_flash: bool = True
    
    # Monitoring
    metrics_interval_ms: int = 100
    performance_tracking: bool = True


class PerformanceMonitor:
    """Monitors and optimizes UI performance"""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.latency_buffer = deque(maxlen=buffer_size)
        self.event_timestamps = {}
        self.performance_alerts = []
        
    def start_event(self, event_id: str) -> float:
        """Start timing an event"""
        timestamp = time.perf_counter()
        self.event_timestamps[event_id] = timestamp
        return timestamp
    
    def end_event(self, event_id: str) -> float:
        """End timing and return latency"""
        if event_id not in self.event_timestamps:
            return 0.0
        
        start_time = self.event_timestamps.pop(event_id)
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        self.latency_buffer.append(latency_ms)
        return latency_ms
    
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self.latency_buffer:
            return {
                'avg': 0.0,
                'p50': 0.0,
                'p95': 0.0,
                'p99': 0.0,
                'max': 0.0
            }
        
        sorted_latencies = sorted(self.latency_buffer)
        
        return {
            'avg': statistics.mean(self.latency_buffer),
            'p50': statistics.median(sorted_latencies),
            'p95': sorted_latencies[int(len(sorted_latencies) * 0.95)],
            'p99': sorted_latencies[int(len(sorted_latencies) * 0.99)],
            'max': max(self.latency_buffer)
        }
    
    def check_sla(self, target_ms: float) -> bool:
        """Check if we're meeting SLA targets"""
        stats = self.get_stats()
        return stats['p95'] <= target_ms


class VelocityUISystem:
    """Main UI system orchestrator"""
    
    def __init__(self, config: VelocityConfig = None):
        self.config = config or VelocityConfig()
        
        # Components
        self.desktop_ui: Optional[VelocityDashboard] = None
        self.mobile_ui: Optional[MobileInterface] = None
        self.realtime_engine: Optional[RealtimeOrchestrator] = None
        
        # Performance monitoring
        self.perf_monitor = PerformanceMonitor()
        
        # Event routing
        self.event_handlers = {}
        self.ticket_callbacks = []
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._running = False
        
        # Stats
        self.total_events = 0
        self.total_tickets = 0
        
    async def initialize(self):
        """Initialize all UI components"""
        logger.info("Initializing Velocity UI System")
        
        # Start realtime engine
        if self.config.enable_websocket:
            self.realtime_engine = RealtimeOrchestrator()
            await self.realtime_engine.start(
                self.config.ws_host,
                self.config.ws_port
            )
        
        # Start mobile interface in thread
        if self.config.enable_mobile:
            self.mobile_ui = MobileInterface(
                self.config.mobile_host,
                self.config.mobile_port
            )
            mobile_thread = threading.Thread(
                target=self.mobile_ui.run,
                daemon=True
            )
            mobile_thread.start()
        
        # Desktop UI will be started separately due to GUI requirements
        
        self._running = True
        
        # Start monitoring
        if self.config.performance_tracking:
            asyncio.create_task(self._performance_loop())
        
        logger.info("Velocity UI System initialized")
    
    def launch_desktop(self):
        """Launch desktop UI (must be called from main thread)"""
        if self.config.enable_desktop:
            self.desktop_ui = VelocityDashboard()
            
            # Connect event handlers
            self._connect_desktop_handlers()
            
            # Run GUI (blocks)
            self.desktop_ui.mainloop()
    
    def _connect_desktop_handlers(self):
        """Connect desktop UI event handlers"""
        if not self.desktop_ui:
            return
        
        # Override methods to route through our system
        original_add_ticket = self.desktop_ui.add_ticket_alert
        
        def wrapped_add_ticket(alert: TicketAlert):
            # Track performance
            event_id = f"ticket_{alert.timestamp}"
            self.perf_monitor.start_event(event_id)
            
            # Call original
            original_add_ticket(alert)
            
            # Record latency
            latency = self.perf_monitor.end_event(event_id)
            
            # Broadcast to other UIs
            self._broadcast_ticket_alert(alert)
        
        self.desktop_ui.add_ticket_alert = wrapped_add_ticket
    
    async def process_ticket_detection(self, 
                                     platform: str,
                                     ticket_data: Dict[str, Any]) -> float:
        """Process ticket detection with velocity optimization"""
        event_id = f"detect_{time.time()}"
        self.perf_monitor.start_event(event_id)
        
        try:
            # Create ticket alert
            alert = TicketAlert(
                timestamp=time.time(),
                platform=platform,
                event_name=ticket_data.get('event_name', 'Unknown Event'),
                section=ticket_data.get('section', ''),
                row=ticket_data.get('row', ''),
                seat=ticket_data.get('seat', ''),
                price=ticket_data.get('price', 0.0),
                availability=ticket_data.get('availability', 1),
                confidence=ticket_data.get('confidence', 1.0),
                latency_ms=0.0  # Will be updated
            )
            
            # Process in parallel
            tasks = []
            
            # Send to desktop UI
            if self.desktop_ui:
                tasks.append(
                    self._send_to_desktop(alert)
                )
            
            # Send to mobile UI
            if self.mobile_ui:
                tasks.append(
                    self._send_to_mobile(alert)
                )
            
            # Send to realtime engine
            if self.realtime_engine:
                tasks.append(
                    self._send_to_realtime(alert)
                )
            
            # Execute all sends in parallel
            await asyncio.gather(*tasks)
            
            # Calculate total latency
            total_latency = self.perf_monitor.end_event(event_id)
            alert.latency_ms = total_latency
            
            # Update stats
            self.total_tickets += 1
            
            # Call registered callbacks
            for callback in self.ticket_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"Ticket callback error: {e}")
            
            return total_latency
            
        except Exception as e:
            logger.error(f"Ticket processing error: {e}")
            return -1.0
    
    async def _send_to_desktop(self, alert: TicketAlert):
        """Send alert to desktop UI"""
        if self.desktop_ui:
            # Desktop UI runs in main thread, use thread-safe method
            self.desktop_ui.after(0, lambda: self.desktop_ui.add_ticket_alert(alert))
    
    async def _send_to_mobile(self, alert: TicketAlert):
        """Send alert to mobile UI"""
        if self.mobile_ui:
            # Convert to dict for mobile
            ticket_data = {
                'platform': alert.platform,
                'event_name': alert.event_name,
                'section': alert.section,
                'row': alert.row,
                'seat': alert.seat,
                'price': alert.price,
                'timestamp': alert.timestamp
            }
            
            # Use executor for thread safety
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.mobile_ui.broadcast_ticket_alert,
                ticket_data
            )
    
    async def _send_to_realtime(self, alert: TicketAlert):
        """Send alert to realtime engine"""
        if self.realtime_engine:
            event = RealtimeEvent(
                event_id=f"ticket_{alert.timestamp}",
                timestamp=alert.timestamp,
                event_type='ticket_found',
                platform=alert.platform,
                priority=9,  # High priority
                data={
                    'event_name': alert.event_name,
                    'section': alert.section,
                    'row': alert.row,
                    'seat': alert.seat,
                    'price': alert.price,
                    'availability': alert.availability,
                    'confidence': alert.confidence
                }
            )
            
            await self.realtime_engine.submit_event(event)
    
    def _broadcast_ticket_alert(self, alert: TicketAlert):
        """Broadcast ticket alert to all connected UIs"""
        # This is called from desktop UI thread
        asyncio.run_coroutine_threadsafe(
            self._async_broadcast_ticket(alert),
            asyncio.get_event_loop()
        )
    
    async def _async_broadcast_ticket(self, alert: TicketAlert):
        """Async broadcast implementation"""
        tasks = []
        
        if self.mobile_ui:
            tasks.append(self._send_to_mobile(alert))
        
        if self.realtime_engine:
            tasks.append(self._send_to_realtime(alert))
        
        await asyncio.gather(*tasks)
    
    async def update_metrics(self, metrics: Dict[str, Any]):
        """Update metrics across all UIs"""
        # Add performance stats
        metrics['ui_performance'] = self.perf_monitor.get_stats()
        
        # Send to all UIs
        tasks = []
        
        if self.mobile_ui:
            tasks.append(
                asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.mobile_ui.broadcast_metrics,
                    metrics
                )
            )
        
        if self.realtime_engine:
            event = RealtimeEvent(
                event_id=f"metrics_{time.time()}",
                timestamp=time.time(),
                event_type='metrics_update',
                platform='system',
                data=metrics
            )
            tasks.append(self.realtime_engine.submit_event(event))
        
        await asyncio.gather(*tasks)
    
    async def _performance_loop(self):
        """Monitor and report performance"""
        while self._running:
            await asyncio.sleep(self.config.metrics_interval_ms / 1000.0)
            
            # Get performance stats
            stats = self.perf_monitor.get_stats()
            
            # Check SLA
            if not self.perf_monitor.check_sla(self.config.target_latency_ms):
                logger.warning(
                    f"Performance SLA breach: p95={stats['p95']:.1f}ms "
                    f"(target={self.config.target_latency_ms}ms)"
                )
            
            # Create performance metric
            metric = PerformanceMetric(
                timestamp=time.time(),
                detection_latency_ms=stats['avg'],
                ui_response_ms=stats['p95'],
                network_latency_ms=0.0,  # Would be measured separately
                cpu_usage=0.0,  # Would get from system
                memory_usage=0.0,  # Would get from system
                active_monitors=0,  # Would get from monitors
                tickets_per_second=self.total_tickets / (time.time() - self._start_time)
            )
            
            # Update metrics
            await self.update_metrics({
                'latency': metric.detection_latency_ms,
                'ui_response': metric.ui_response_ms,
                'tickets_per_second': metric.tickets_per_second,
                'total_tickets': self.total_tickets,
                'total_events': self.total_events
            })
    
    def register_ticket_callback(self, callback: Callable):
        """Register callback for ticket alerts"""
        self.ticket_callbacks.append(callback)
    
    def activate_platform(self, platform: str):
        """Activate platform across all UIs"""
        if self.desktop_ui:
            self.desktop_ui.quick_activate_platform(platform)
        
        # Mobile UI will update via WebSocket broadcast
    
    def emergency_stop(self):
        """Emergency stop all operations"""
        logger.warning("Emergency stop activated")
        
        if self.desktop_ui:
            self.desktop_ui.emergency_stop()
        
        # Broadcast emergency stop
        asyncio.create_task(self._broadcast_emergency_stop())
    
    async def _broadcast_emergency_stop(self):
        """Broadcast emergency stop to all components"""
        if self.realtime_engine:
            event = RealtimeEvent(
                event_id=f"emergency_{time.time()}",
                timestamp=time.time(),
                event_type='emergency_stop',
                platform='system',
                priority=10,
                data={'reason': 'User initiated'}
            )
            await self.realtime_engine.submit_event(event)
    
    async def shutdown(self):
        """Clean shutdown of all components"""
        logger.info("Shutting down Velocity UI System")
        
        self._running = False
        
        if self.realtime_engine:
            await self.realtime_engine.stop()
        
        if self.desktop_ui:
            await self.desktop_ui.shutdown()
        
        self.executor.shutdown(wait=True)
        
        logger.info("Velocity UI System shutdown complete")


# Example usage
async def demo_velocity_ui():
    """Demo of the velocity UI system"""
    # Create config
    config = VelocityConfig(
        enable_desktop=True,
        enable_mobile=True,
        enable_websocket=True,
        target_latency_ms=25.0,
        audio_alerts=True,
        haptic_feedback=True
    )
    
    # Create system
    ui_system = VelocityUISystem(config)
    
    # Initialize
    await ui_system.initialize()
    
    # Simulate ticket detections
    async def simulate_tickets():
        platforms = ['ticketmaster', 'fansale', 'vivaticket']
        events = ['Taylor Swift', 'Coldplay', 'Ed Sheeran']
        
        while True:
            await asyncio.sleep(2)  # Simulate ticket found every 2 seconds
            
            import random
            
            ticket_data = {
                'event_name': random.choice(events),
                'section': random.choice(['A', 'B', 'C', 'VIP']),
                'row': str(random.randint(1, 20)),
                'seat': str(random.randint(1, 30)),
                'price': random.uniform(100, 500),
                'availability': random.randint(1, 4),
                'confidence': random.uniform(0.8, 1.0)
            }
            
            platform = random.choice(platforms)
            
            # Process with velocity optimization
            latency = await ui_system.process_ticket_detection(platform, ticket_data)
            
            print(f"Ticket processed in {latency:.1f}ms")
    
    # Start simulation
    asyncio.create_task(simulate_tickets())
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await ui_system.shutdown()


if __name__ == "__main__":
    # For desktop UI, need to run in main thread
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "desktop":
        # Launch desktop UI
        config = VelocityConfig()
        ui_system = VelocityUISystem(config)
        
        # Initialize in thread
        def init_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ui_system.initialize())
        
        init_thread = threading.Thread(target=init_async)
        init_thread.start()
        init_thread.join()
        
        # Launch desktop (blocks)
        ui_system.launch_desktop()
    else:
        # Run demo
        asyncio.run(demo_velocity_ui())
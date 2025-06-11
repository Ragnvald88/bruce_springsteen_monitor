# stealthmaster/ui/realtime_engine.py
"""
Real-time Data Flow Engine - Sub-50ms latency for all operations
Optimized for maximum throughput and minimal latency
"""

import asyncio
import time
import json
import msgpack
import uvloop
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import aioredis
import aiokafka
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from asyncio import Queue
import websockets
import zmq
import zmq.asyncio


# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@dataclass
class RealtimeEvent:
    """Base real-time event structure"""
    event_id: str
    timestamp: float
    event_type: str
    platform: str
    data: Dict[str, Any]
    priority: int = 0
    ttl_ms: Optional[int] = None


class DataFlowOptimizer:
    """Optimizes data flow for minimal latency"""
    
    def __init__(self):
        self.routing_table = {}
        self.priority_queues = defaultdict(asyncio.PriorityQueue)
        self.batch_settings = {
            'max_batch_size': 100,
            'max_wait_ms': 10,
            'compression': True
        }
    
    def optimize_route(self, event: RealtimeEvent) -> str:
        """Determine optimal routing path"""
        # Route based on event characteristics
        if event.priority > 9:
            return 'express'  # Direct path, no batching
        elif event.ttl_ms and event.ttl_ms < 100:
            return 'fast'  # Minimal processing
        else:
            return 'standard'  # Can be batched
    
    def should_batch(self, events: List[RealtimeEvent]) -> bool:
        """Determine if events should be batched"""
        if not events:
            return False
        
        # Don't batch high priority
        if any(e.priority > 8 for e in events):
            return False
        
        # Batch if we have enough events or time threshold reached
        return len(events) >= self.batch_settings['max_batch_size']


class ZeroMQTransport:
    """Ultra-low latency transport using ZeroMQ"""
    
    def __init__(self):
        self.context = zmq.asyncio.Context()
        self.publishers = {}
        self.subscribers = {}
        
    async def create_publisher(self, endpoint: str, topic: str):
        """Create ZMQ publisher"""
        socket = self.context.socket(zmq.PUB)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.SNDHWM, 10000)
        socket.bind(endpoint)
        
        self.publishers[topic] = socket
        return socket
    
    async def create_subscriber(self, endpoint: str, topics: List[str]):
        """Create ZMQ subscriber"""
        socket = self.context.socket(zmq.SUB)
        socket.connect(endpoint)
        
        for topic in topics:
            socket.setsockopt_string(zmq.SUBSCRIBE, topic)
        
        return socket
    
    async def publish(self, topic: str, data: bytes):
        """Publish data with minimal latency"""
        if topic in self.publishers:
            await self.publishers[topic].send_multipart([
                topic.encode('utf-8'),
                data
            ])
    
    async def close(self):
        """Clean shutdown"""
        for socket in self.publishers.values():
            socket.close()
        for socket in self.subscribers.values():
            socket.close()
        self.context.term()


class RealtimeDataPipeline:
    """High-performance data pipeline"""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost",
                 kafka_brokers: List[str] = None):
        self.redis_url = redis_url
        self.kafka_brokers = kafka_brokers or ["localhost:9092"]
        
        # Components
        self.redis_pool = None
        self.kafka_producer = None
        self.zmq_transport = ZeroMQTransport()
        self.flow_optimizer = DataFlowOptimizer()
        
        # Performance tracking
        self.latency_histogram = defaultdict(list)
        self.throughput_counter = defaultdict(int)
        
        # Processing
        self.processors = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self):
        """Initialize pipeline components"""
        # Redis for caching and pub/sub
        self.redis_pool = await aioredis.create_redis_pool(
            self.redis_url,
            minsize=5,
            maxsize=10
        )
        
        # Kafka for reliable message delivery
        if self.kafka_brokers:
            self.kafka_producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=','.join(self.kafka_brokers),
                compression_type='snappy',
                acks=0,  # Fire and forget for speed
                batch_size=16384,
                linger_ms=10
            )
            await self.kafka_producer.start()
        
        # ZMQ endpoints
        await self.zmq_transport.create_publisher(
            "tcp://*:5555", 
            "tickets"
        )
        await self.zmq_transport.create_publisher(
            "tcp://*:5556",
            "metrics"
        )
    
    async def process_event(self, event: RealtimeEvent) -> float:
        """Process event with minimal latency"""
        start_time = time.perf_counter()
        
        # Determine routing
        route = self.flow_optimizer.optimize_route(event)
        
        # Process based on route
        if route == 'express':
            await self._process_express(event)
        elif route == 'fast':
            await self._process_fast(event)
        else:
            await self._process_standard(event)
        
        # Track latency
        latency = (time.perf_counter() - start_time) * 1000
        self.latency_histogram[event.event_type].append(latency)
        
        return latency
    
    async def _process_express(self, event: RealtimeEvent):
        """Express processing path - minimal overhead"""
        # Direct ZMQ publish
        data = msgpack.packb(asdict(event))
        await self.zmq_transport.publish("tickets", data)
        
        # Cache in Redis with TTL
        if event.ttl_ms:
            await self.redis_pool.setex(
                f"event:{event.event_id}",
                event.ttl_ms // 1000,
                data
            )
    
    async def _process_fast(self, event: RealtimeEvent):
        """Fast processing path"""
        # Light processing
        if event.event_type in self.processors:
            event = await self.processors[event.event_type](event)
        
        # Publish to multiple channels
        tasks = []
        
        # ZMQ
        data = msgpack.packb(asdict(event))
        tasks.append(self.zmq_transport.publish("tickets", data))
        
        # Redis pub/sub
        tasks.append(
            self.redis_pool.publish(
                f"channel:{event.platform}",
                data
            )
        )
        
        await asyncio.gather(*tasks)
    
    async def _process_standard(self, event: RealtimeEvent):
        """Standard processing with all features"""
        # Full processing pipeline
        if event.event_type in self.processors:
            event = await self.processors[event.event_type](event)
        
        # Serialize
        data = msgpack.packb(asdict(event))
        
        # Publish to all channels
        tasks = []
        
        # ZMQ
        tasks.append(self.zmq_transport.publish("tickets", data))
        
        # Redis
        tasks.append(self.redis_pool.publish(f"channel:{event.platform}", data))
        
        # Kafka for durability
        if self.kafka_producer:
            tasks.append(
                self.kafka_producer.send(
                    f"tickets.{event.platform}",
                    data
                )
            )
        
        await asyncio.gather(*tasks)
    
    def register_processor(self, event_type: str, processor: Callable):
        """Register event processor"""
        self.processors[event_type] = processor
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        metrics = {}
        
        # Latency stats
        for event_type, latencies in self.latency_histogram.items():
            if latencies:
                metrics[f"{event_type}_latency"] = {
                    'avg': np.mean(latencies),
                    'p50': np.percentile(latencies, 50),
                    'p95': np.percentile(latencies, 95),
                    'p99': np.percentile(latencies, 99)
                }
        
        # Throughput
        metrics['throughput'] = dict(self.throughput_counter)
        
        return metrics
    
    async def close(self):
        """Clean shutdown"""
        if self.kafka_producer:
            await self.kafka_producer.stop()
        
        self.redis_pool.close()
        await self.redis_pool.wait_closed()
        
        await self.zmq_transport.close()
        
        self.executor.shutdown(wait=True)


class WebSocketBroadcaster:
    """WebSocket broadcaster with connection pooling"""
    
    def __init__(self, max_connections: int = 1000):
        self.max_connections = max_connections
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.connection_stats = defaultdict(lambda: {'messages': 0, 'bytes': 0})
        
    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        if len(self.connections) >= self.max_connections:
            await websocket.close(1008, "Max connections reached")
            return
        
        self.connections.add(websocket)
        connection_id = id(websocket)
        
        try:
            # Send initial state
            await self.send_initial_state(websocket)
            
            # Keep connection alive
            await websocket.wait_closed()
            
        finally:
            self.connections.remove(websocket)
            del self.connection_stats[connection_id]
    
    async def send_initial_state(self, websocket):
        """Send initial state to new connection"""
        # Send current platform states, active tickets, etc.
        initial_data = {
            'type': 'initial_state',
            'timestamp': time.time(),
            'data': {
                'platforms': ['ticketmaster', 'fansale', 'vivaticket'],
                'active_monitors': 0,
                'connection_id': id(websocket)
            }
        }
        
        await websocket.send(json.dumps(initial_data))
    
    async def broadcast(self, message: Dict[str, Any], 
                       filter_fn: Optional[Callable] = None):
        """Broadcast to all or filtered connections"""
        if not self.connections:
            return
        
        # Serialize once
        data = json.dumps(message)
        data_size = len(data)
        
        # Filter connections if needed
        targets = self.connections
        if filter_fn:
            targets = {ws for ws in self.connections if filter_fn(ws)}
        
        # Broadcast concurrently
        if targets:
            tasks = []
            for websocket in targets:
                tasks.append(self._send_to_connection(websocket, data))
                
                # Update stats
                conn_id = id(websocket)
                self.connection_stats[conn_id]['messages'] += 1
                self.connection_stats[conn_id]['bytes'] += data_size
            
            # Send with timeout
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=1.0
            )
    
    async def _send_to_connection(self, websocket, data: str):
        """Send to single connection with error handling"""
        try:
            await websocket.send(data)
        except websockets.exceptions.ConnectionClosed:
            # Connection closed, will be cleaned up
            pass
        except Exception as e:
            print(f"Error sending to websocket: {e}")
    
    async def broadcast_ticket_alert(self, ticket_data: Dict[str, Any]):
        """Specialized broadcast for ticket alerts"""
        message = {
            'type': 'ticket_alert',
            'timestamp': time.time(),
            'priority': 10,  # Highest priority
            'data': ticket_data
        }
        
        await self.broadcast(message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get broadcaster statistics"""
        return {
            'total_connections': len(self.connections),
            'connection_details': dict(self.connection_stats)
        }


class RealtimeOrchestrator:
    """Orchestrates all real-time components"""
    
    def __init__(self):
        self.pipeline = RealtimeDataPipeline()
        self.broadcaster = WebSocketBroadcaster()
        self.ws_server = None
        self._running = False
        
        # Event queue for processing
        self.event_queue = asyncio.Queue(maxsize=10000)
        
    async def start(self, ws_host: str = "localhost", ws_port: int = 8765):
        """Start all real-time services"""
        # Initialize pipeline
        await self.pipeline.initialize()
        
        # Start WebSocket server
        self.ws_server = await websockets.serve(
            self.broadcaster.handle_connection,
            ws_host,
            ws_port
        )
        
        # Start processing loop
        self._running = True
        asyncio.create_task(self._process_events())
        asyncio.create_task(self._metrics_publisher())
        
        print(f"Realtime engine started on ws://{ws_host}:{ws_port}")
    
    async def _process_events(self):
        """Main event processing loop"""
        while self._running:
            try:
                # Get event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=0.1
                )
                
                # Process through pipeline
                latency = await self.pipeline.process_event(event)
                
                # Broadcast if ticket event
                if event.event_type == 'ticket_found':
                    await self.broadcaster.broadcast_ticket_alert(event.data)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Event processing error: {e}")
    
    async def _metrics_publisher(self):
        """Publish metrics at regular intervals"""
        while self._running:
            await asyncio.sleep(1)  # 1Hz metrics
            
            # Gather metrics
            pipeline_metrics = await self.pipeline.get_metrics()
            ws_metrics = self.broadcaster.get_connection_stats()
            
            # Publish metrics
            metrics_event = RealtimeEvent(
                event_id=f"metrics_{time.time()}",
                timestamp=time.time(),
                event_type='system_metrics',
                platform='system',
                data={
                    'pipeline': pipeline_metrics,
                    'websocket': ws_metrics
                }
            )
            
            await self.broadcaster.broadcast({
                'type': 'metrics_update',
                'data': metrics_event.data
            })
    
    async def submit_event(self, event: RealtimeEvent):
        """Submit event for processing"""
        await self.event_queue.put(event)
    
    async def stop(self):
        """Stop all services"""
        self._running = False
        
        if self.ws_server:
            self.ws_server.close()
            await self.ws_server.wait_closed()
        
        await self.pipeline.close()


# Example usage
async def main():
    """Example of running the realtime engine"""
    orchestrator = RealtimeOrchestrator()
    
    # Start services
    await orchestrator.start()
    
    # Simulate ticket events
    for i in range(10):
        event = RealtimeEvent(
            event_id=f"ticket_{i}",
            timestamp=time.time(),
            event_type='ticket_found',
            platform='ticketmaster',
            priority=9,
            data={
                'event': 'Taylor Swift Concert',
                'section': 'A',
                'row': str(i + 1),
                'seat': str(i + 10),
                'price': 250.00 + (i * 10),
                'available': True
            }
        )
        
        await orchestrator.submit_event(event)
        await asyncio.sleep(0.5)
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
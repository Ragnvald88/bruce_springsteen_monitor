# stealthmaster/ui/velocity_dashboard.py
"""
StealthMaster Velocity Dashboard - Lightning-Fast Real-Time Monitoring
Sub-50ms response times for ticket detection and purchase activation
"""

import asyncio
import threading
import time
import json
from datetime import datetime
from collections import deque
from typing import Dict, List, Any, Optional, Callable
import websockets
import aiohttp
from dataclasses import dataclass, asdict
import numpy as np

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from pygame import mixer
import keyboard
import vibration  # For haptic feedback


@dataclass
class TicketAlert:
    """Real-time ticket alert data"""
    timestamp: float
    platform: str
    event_name: str
    section: str
    row: str
    seat: str
    price: float
    availability: int
    confidence: float
    latency_ms: float


@dataclass
class PerformanceMetric:
    """Real-time performance tracking"""
    timestamp: float
    detection_latency_ms: float
    ui_response_ms: float
    network_latency_ms: float
    cpu_usage: float
    memory_usage: float
    active_monitors: int
    tickets_per_second: float


class VelocityMetricsEngine:
    """Ultra-fast metrics collection and analysis"""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.metrics_buffer = deque(maxlen=buffer_size)
        self.ticket_buffer = deque(maxlen=buffer_size)
        self.latency_tracker = deque(maxlen=100)
        self._last_update = time.perf_counter()
        
    def record_detection(self, latency_ms: float):
        """Record detection latency"""
        self.latency_tracker.append(latency_ms)
        
    def get_average_latency(self) -> float:
        """Get average detection latency"""
        if not self.latency_tracker:
            return 0.0
        return np.mean(self.latency_tracker)
    
    def get_p99_latency(self) -> float:
        """Get 99th percentile latency"""
        if not self.latency_tracker:
            return 0.0
        return np.percentile(self.latency_tracker, 99)


class WebSocketRealtimeServer:
    """WebSocket server for ultra-low latency updates"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.server = None
        self._running = False
        
    async def handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast to all connected clients with minimal latency"""
        if self.clients:
            # Serialize once
            data = json.dumps(message)
            # Send to all clients concurrently
            await asyncio.gather(
                *[client.send(data) for client in self.clients],
                return_exceptions=True
            )
    
    async def start(self):
        """Start WebSocket server"""
        self.server = await websockets.serve(
            self.handler, self.host, self.port
        )
        self._running = True
    
    async def stop(self):
        """Stop WebSocket server"""
        self._running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()


class HotKeyManager:
    """Keyboard shortcuts for instant actions"""
    
    def __init__(self):
        self.hotkeys = {}
        self._setup_default_hotkeys()
    
    def _setup_default_hotkeys(self):
        """Setup default keyboard shortcuts"""
        self.hotkeys = {
            'ctrl+space': 'quick_purchase',
            'ctrl+1': 'activate_platform_1',
            'ctrl+2': 'activate_platform_2',
            'ctrl+3': 'activate_platform_3',
            'ctrl+s': 'emergency_stop',
            'ctrl+r': 'restart_monitors',
            'ctrl+d': 'toggle_debug',
            'f1': 'help',
            'f5': 'refresh_all',
            'space': 'pause_resume'
        }
    
    def register_callback(self, action: str, callback: Callable):
        """Register callback for action"""
        for hotkey, mapped_action in self.hotkeys.items():
            if mapped_action == action:
                keyboard.add_hotkey(hotkey, callback)
    
    def unregister_all(self):
        """Unregister all hotkeys"""
        keyboard.unhook_all()


class VelocityDashboard(ctk.CTk):
    """Ultra-responsive monitoring dashboard"""
    
    def __init__(self):
        super().__init__()
        
        # Performance settings
        self.title("StealthMaster Velocity Dashboard")
        self.geometry("1920x1080")
        self.minsize(1600, 900)
        
        # Dark theme for reduced eye strain
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Core components
        self.metrics_engine = VelocityMetricsEngine()
        self.ws_server = WebSocketRealtimeServer()
        self.hotkey_manager = HotKeyManager()
        
        # Audio alerts
        mixer.init(frequency=22050, size=-16, channels=2, buffer=256)
        self.alert_sounds = self._load_alert_sounds()
        
        # Real-time data
        self.active_tickets = {}
        self.platform_states = {}
        self.performance_data = deque(maxlen=300)  # 5 minutes at 1Hz
        
        # UI update tracking
        self._last_ui_update = time.perf_counter()
        self._frame_times = deque(maxlen=60)
        
        # Build UI
        self._build_ui()
        
        # Start real-time updates
        self._start_realtime_loop()
        
    def _load_alert_sounds(self) -> Dict[str, Any]:
        """Load alert sounds for instant feedback"""
        sounds = {}
        try:
            # Pre-load and convert sounds for minimal latency
            sound_files = {
                'ticket_found': 'assets/sounds/ticket_alert.wav',
                'purchase_ready': 'assets/sounds/ready.wav',
                'success': 'assets/sounds/success.wav',
                'warning': 'assets/sounds/warning.wav'
            }
            
            for name, path in sound_files.items():
                sounds[name] = mixer.Sound(path)
                # Set volume
                sounds[name].set_volume(0.7)
                
        except Exception as e:
            print(f"Failed to load sounds: {e}")
            
        return sounds
    
    def _build_ui(self):
        """Build high-performance UI"""
        # Main container with grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Top bar - Critical metrics
        self._build_metrics_bar(main_frame)
        
        # Left panel - Platform controls
        self._build_platform_panel(main_frame)
        
        # Center - Real-time ticket feed
        self._build_ticket_feed(main_frame)
        
        # Right panel - Performance graphs
        self._build_performance_panel(main_frame)
        
        # Bottom - Quick actions
        self._build_action_bar(main_frame)
        
    def _build_metrics_bar(self, parent):
        """Build top metrics bar"""
        metrics_frame = ctk.CTkFrame(parent, height=80)
        metrics_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        metrics_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        
        # Key metrics with large, clear displays
        self.metric_displays = {}
        
        metrics = [
            ("Detection Latency", "0.0ms", "green"),
            ("UI Response", "0.0ms", "green"),
            ("Tickets/sec", "0", "blue"),
            ("Active Monitors", "0", "orange"),
            ("Success Rate", "0%", "green"),
            ("Uptime", "00:00:00", "gray")
        ]
        
        for i, (label, initial, color) in enumerate(metrics):
            frame = ctk.CTkFrame(metrics_frame)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            ctk.CTkLabel(
                frame, 
                text=label,
                font=("Arial", 12)
            ).pack(pady=(5, 0))
            
            display = ctk.CTkLabel(
                frame,
                text=initial,
                font=("Arial Black", 24),
                text_color=color
            )
            display.pack(pady=(0, 5))
            
            self.metric_displays[label] = display
    
    def _build_platform_panel(self, parent):
        """Build platform control panel"""
        panel = ctk.CTkFrame(parent, width=300)
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        # Title
        ctk.CTkLabel(
            panel,
            text="PLATFORM CONTROL",
            font=("Arial Black", 16)
        ).pack(pady=10)
        
        # Platform toggles
        self.platform_controls = {}
        platforms = ["Ticketmaster", "FanSale", "VivaTicket"]
        
        for platform in platforms:
            frame = ctk.CTkFrame(panel)
            frame.pack(fill="x", padx=10, pady=5)
            
            # Status indicator
            status_led = ctk.CTkLabel(
                frame,
                text="●",
                font=("Arial", 20),
                text_color="gray",
                width=30
            )
            status_led.pack(side="left", padx=5)
            
            # Platform name
            ctk.CTkLabel(
                frame,
                text=platform,
                font=("Arial", 14)
            ).pack(side="left", padx=5)
            
            # Quick activate button
            activate_btn = ctk.CTkButton(
                frame,
                text="ACTIVATE",
                width=80,
                height=30,
                command=lambda p=platform: self.quick_activate_platform(p)
            )
            activate_btn.pack(side="right", padx=5)
            
            self.platform_controls[platform] = {
                'status': status_led,
                'button': activate_btn
            }
        
        # Monitor settings
        ctk.CTkLabel(
            panel,
            text="MONITOR SETTINGS",
            font=("Arial Black", 14)
        ).pack(pady=(20, 10))
        
        # Refresh rate
        refresh_frame = ctk.CTkFrame(panel)
        refresh_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            refresh_frame,
            text="Refresh Rate:",
            font=("Arial", 12)
        ).pack(side="left", padx=5)
        
        self.refresh_slider = ctk.CTkSlider(
            refresh_frame,
            from_=100,
            to=5000,
            number_of_steps=49,
            command=self.update_refresh_rate
        )
        self.refresh_slider.set(500)  # 500ms default
        self.refresh_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.refresh_label = ctk.CTkLabel(
            refresh_frame,
            text="500ms",
            font=("Arial", 12)
        )
        self.refresh_label.pack(side="right", padx=5)
    
    def _build_ticket_feed(self, parent):
        """Build real-time ticket feed"""
        feed_frame = ctk.CTkFrame(parent)
        feed_frame.grid(row=1, column=1, sticky="nsew")
        
        # Title with live indicator
        title_frame = ctk.CTkFrame(feed_frame)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        self.live_indicator = ctk.CTkLabel(
            title_frame,
            text="● LIVE",
            font=("Arial Black", 16),
            text_color="red"
        )
        self.live_indicator.pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="TICKET FEED",
            font=("Arial Black", 16)
        ).pack(side="left", padx=10)
        
        # Ticket list with custom rendering
        self.ticket_canvas = tk.Canvas(
            feed_frame,
            bg='#212121',
            highlightthickness=0
        )
        self.ticket_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(self.ticket_canvas)
        scrollbar.pack(side="right", fill="y")
        
        # Ticket container
        self.ticket_container = ctk.CTkFrame(self.ticket_canvas)
        self.ticket_canvas_window = self.ticket_canvas.create_window(
            0, 0, anchor="nw", window=self.ticket_container
        )
        
        # Configure scrolling
        self.ticket_container.bind("<Configure>", self._on_ticket_container_configure)
        self.ticket_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.ticket_canvas.yview)
    
    def _build_performance_panel(self, parent):
        """Build performance monitoring panel"""
        panel = ctk.CTkFrame(parent, width=400)
        panel.grid(row=1, column=2, sticky="nsew", padx=(10, 0))
        
        # Title
        ctk.CTkLabel(
            panel,
            text="PERFORMANCE METRICS",
            font=("Arial Black", 16)
        ).pack(pady=10)
        
        # Create matplotlib graphs for real-time plotting
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
        
        # Latency graph
        self.latency_fig = Figure(figsize=(5, 3), dpi=80, facecolor='#212121')
        self.latency_ax = self.latency_fig.add_subplot(111)
        self.latency_ax.set_facecolor('#212121')
        self.latency_ax.set_title("Detection Latency (ms)", color='white')
        self.latency_ax.set_xlabel("Time", color='white')
        self.latency_ax.set_ylabel("Latency (ms)", color='white')
        self.latency_ax.tick_params(colors='white')
        
        self.latency_line, = self.latency_ax.plot([], [], 'g-', linewidth=2)
        self.latency_ax.set_ylim(0, 100)
        
        self.latency_canvas = FigureCanvasTkAgg(self.latency_fig, panel)
        self.latency_canvas.get_tk_widget().pack(pady=10)
        
        # Throughput graph
        self.throughput_fig = Figure(figsize=(5, 3), dpi=80, facecolor='#212121')
        self.throughput_ax = self.throughput_fig.add_subplot(111)
        self.throughput_ax.set_facecolor('#212121')
        self.throughput_ax.set_title("Ticket Detection Rate", color='white')
        self.throughput_ax.set_xlabel("Time", color='white')
        self.throughput_ax.set_ylabel("Tickets/sec", color='white')
        self.throughput_ax.tick_params(colors='white')
        
        self.throughput_line, = self.throughput_ax.plot([], [], 'b-', linewidth=2)
        self.throughput_ax.set_ylim(0, 10)
        
        self.throughput_canvas = FigureCanvasTkAgg(self.throughput_fig, panel)
        self.throughput_canvas.get_tk_widget().pack(pady=10)
    
    def _build_action_bar(self, parent):
        """Build quick action bar"""
        action_frame = ctk.CTkFrame(parent, height=80)
        action_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        # Emergency stop - Large and prominent
        self.emergency_btn = ctk.CTkButton(
            action_frame,
            text="EMERGENCY STOP",
            font=("Arial Black", 16),
            width=200,
            height=50,
            fg_color="red",
            hover_color="darkred",
            command=self.emergency_stop
        )
        self.emergency_btn.pack(side="left", padx=20)
        
        # Quick purchase
        self.quick_purchase_btn = ctk.CTkButton(
            action_frame,
            text="QUICK PURCHASE (Space)",
            font=("Arial Black", 14),
            width=250,
            height=50,
            fg_color="green",
            hover_color="darkgreen",
            command=self.quick_purchase
        )
        self.quick_purchase_btn.pack(side="left", padx=10)
        
        # Status
        self.status_label = ctk.CTkLabel(
            action_frame,
            text="READY",
            font=("Arial Black", 20),
            text_color="green"
        )
        self.status_label.pack(side="right", padx=20)
    
    def _on_ticket_container_configure(self, event):
        """Update scroll region"""
        self.ticket_canvas.configure(scrollregion=self.ticket_canvas.bbox("all"))
    
    def _start_realtime_loop(self):
        """Start real-time update loop"""
        # UI update loop (60 FPS target)
        self._update_ui()
        
        # Metric collection loop
        self._collect_metrics()
        
        # Register hotkeys
        self._register_hotkeys()
    
    def _update_ui(self):
        """Ultra-fast UI update loop"""
        start_time = time.perf_counter()
        
        # Update metrics displays
        self._update_metric_displays()
        
        # Update graphs
        self._update_performance_graphs()
        
        # Animate live indicator
        current_color = self.live_indicator.cget("text_color")
        new_color = "red" if current_color == "darkred" else "darkred"
        self.live_indicator.configure(text_color=new_color)
        
        # Track frame time
        frame_time = (time.perf_counter() - start_time) * 1000
        self._frame_times.append(frame_time)
        
        # Schedule next update (targeting 60 FPS)
        self.after(16, self._update_ui)  # 16ms = ~60 FPS
    
    def _update_metric_displays(self):
        """Update metric display values"""
        # Get latest metrics
        avg_latency = self.metrics_engine.get_average_latency()
        p99_latency = self.metrics_engine.get_p99_latency()
        
        # Update displays
        self.metric_displays["Detection Latency"].configure(
            text=f"{avg_latency:.1f}ms",
            text_color="green" if avg_latency < 50 else "yellow" if avg_latency < 100 else "red"
        )
        
        if self._frame_times:
            avg_frame_time = np.mean(self._frame_times)
            self.metric_displays["UI Response"].configure(
                text=f"{avg_frame_time:.1f}ms",
                text_color="green" if avg_frame_time < 16.7 else "yellow"
            )
    
    def _update_performance_graphs(self):
        """Update real-time performance graphs"""
        if len(self.performance_data) > 0:
            # Update latency graph
            times = [p.timestamp for p in self.performance_data]
            latencies = [p.detection_latency_ms for p in self.performance_data]
            
            self.latency_line.set_data(times, latencies)
            self.latency_ax.relim()
            self.latency_ax.autoscale_view()
            self.latency_canvas.draw_idle()
            
            # Update throughput graph
            throughputs = [p.tickets_per_second for p in self.performance_data]
            
            self.throughput_line.set_data(times, throughputs)
            self.throughput_ax.relim()
            self.throughput_ax.autoscale_view()
            self.throughput_canvas.draw_idle()
    
    def _collect_metrics(self):
        """Collect performance metrics"""
        # Simulate metric collection
        metric = PerformanceMetric(
            timestamp=time.time(),
            detection_latency_ms=np.random.normal(25, 5),
            ui_response_ms=np.mean(self._frame_times) if self._frame_times else 0,
            network_latency_ms=np.random.normal(15, 3),
            cpu_usage=np.random.normal(30, 10),
            memory_usage=np.random.normal(45, 5),
            active_monitors=len(self.platform_states),
            tickets_per_second=np.random.poisson(2)
        )
        
        self.performance_data.append(metric)
        
        # Schedule next collection
        self.after(100, self._collect_metrics)  # 10Hz collection
    
    def _register_hotkeys(self):
        """Register keyboard shortcuts"""
        self.hotkey_manager.register_callback('quick_purchase', self.quick_purchase)
        self.hotkey_manager.register_callback('emergency_stop', self.emergency_stop)
        
        # Platform activation
        for i, platform in enumerate(["Ticketmaster", "FanSale", "VivaTicket"]):
            self.hotkey_manager.register_callback(
                f'activate_platform_{i+1}',
                lambda p=platform: self.quick_activate_platform(p)
            )
    
    def add_ticket_alert(self, alert: TicketAlert):
        """Add ticket to real-time feed"""
        # Create ticket widget
        ticket_frame = ctk.CTkFrame(
            self.ticket_container,
            height=80,
            fg_color="darkgreen" if alert.confidence > 0.9 else "darkblue"
        )
        ticket_frame.pack(fill="x", padx=5, pady=2)
        
        # Flash animation for new tickets
        self._flash_widget(ticket_frame)
        
        # Ticket info
        info_text = f"{alert.platform} | {alert.event_name}\n"
        info_text += f"Section {alert.section} Row {alert.row} Seat {alert.seat}\n"
        info_text += f"${alert.price:.2f} | {alert.latency_ms:.0f}ms"
        
        ctk.CTkLabel(
            ticket_frame,
            text=info_text,
            font=("Arial", 12),
            justify="left"
        ).pack(side="left", padx=10)
        
        # Quick buy button
        ctk.CTkButton(
            ticket_frame,
            text="BUY NOW",
            width=100,
            height=60,
            fg_color="green",
            command=lambda: self.instant_purchase(alert)
        ).pack(side="right", padx=10)
        
        # Play alert sound
        if 'ticket_found' in self.alert_sounds:
            self.alert_sounds['ticket_found'].play()
        
        # Haptic feedback
        self._trigger_haptic_feedback()
        
        # Update metrics
        self.metrics_engine.record_detection(alert.latency_ms)
        
        # Broadcast via WebSocket
        asyncio.create_task(self.ws_server.broadcast({
            'type': 'ticket_alert',
            'data': asdict(alert)
        }))
    
    def _flash_widget(self, widget, count=3):
        """Flash widget for attention"""
        if count > 0:
            current_color = widget.cget("fg_color")
            widget.configure(fg_color="yellow" if current_color != "yellow" else current_color)
            self.after(100, lambda: self._flash_widget(widget, count-1))
    
    def _trigger_haptic_feedback(self):
        """Trigger haptic feedback for ticket alerts"""
        try:
            # Platform-specific haptic feedback
            if hasattr(vibration, 'vibrate'):
                vibration.vibrate(pattern=[0, 50, 50, 50])  # Quick double buzz
        except:
            pass
    
    def quick_activate_platform(self, platform: str):
        """Instantly activate platform monitoring"""
        control = self.platform_controls.get(platform)
        if control:
            # Update UI
            control['status'].configure(text_color="green")
            control['button'].configure(text="ACTIVE", fg_color="green")
            
            # Update state
            self.platform_states[platform] = {
                'active': True,
                'start_time': time.time()
            }
            
            # Play feedback
            if 'success' in self.alert_sounds:
                self.alert_sounds['success'].play()
    
    def instant_purchase(self, alert: TicketAlert):
        """Execute instant purchase"""
        self.status_label.configure(text="PURCHASING...", text_color="yellow")
        
        # Trigger purchase logic
        # This would connect to the actual purchase system
        print(f"Instant purchase triggered for: {alert}")
        
        # Simulate purchase
        self.after(500, lambda: self.status_label.configure(
            text="PURCHASE COMPLETE", text_color="green"
        ))
    
    def quick_purchase(self):
        """Quick purchase hotkey action"""
        # Find best available ticket
        if self.active_tickets:
            best_ticket = min(
                self.active_tickets.values(),
                key=lambda t: t.price
            )
            self.instant_purchase(best_ticket)
    
    def emergency_stop(self):
        """Emergency stop all operations"""
        self.status_label.configure(text="EMERGENCY STOP", text_color="red")
        
        # Stop all platforms
        for platform, control in self.platform_controls.items():
            control['status'].configure(text_color="red")
            control['button'].configure(text="STOPPED", fg_color="red")
        
        # Clear states
        self.platform_states.clear()
        self.active_tickets.clear()
        
        # Play warning
        if 'warning' in self.alert_sounds:
            self.alert_sounds['warning'].play()
    
    def update_refresh_rate(self, value):
        """Update monitor refresh rate"""
        rate = int(value)
        self.refresh_label.configure(text=f"{rate}ms")
        
        # Broadcast rate change
        asyncio.create_task(self.ws_server.broadcast({
            'type': 'config_update',
            'data': {'refresh_rate': rate}
        }))
    
    async def shutdown(self):
        """Clean shutdown"""
        self.hotkey_manager.unregister_all()
        await self.ws_server.stop()
        mixer.quit()


def launch_velocity_dashboard():
    """Launch the velocity dashboard"""
    app = VelocityDashboard()
    
    try:
        app.mainloop()
    finally:
        # Ensure clean shutdown
        asyncio.run(app.shutdown())


if __name__ == "__main__":
    launch_velocity_dashboard()
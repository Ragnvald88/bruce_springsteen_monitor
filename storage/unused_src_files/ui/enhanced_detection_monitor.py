"""
StealthMaster AI v3.0 - Real-Time Detection Monitor
Provides clear visibility into bot detection events and system status
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Detection threat levels"""
    CLEAR = ("clear", "#2ECC71", "✅")  # Green
    LOW = ("low", "#F39C12", "⚠️")  # Orange
    MEDIUM = ("medium", "#E74C3C", "⚡")  # Red
    HIGH = ("high", "#8E44AD", "🚨")  # Purple
    CRITICAL = ("critical", "#2C3E50", "💀")  # Dark


@dataclass
class DetectionEvent:
    """Single detection event"""
    timestamp: datetime
    platform: str
    event_type: str
    threat_level: ThreatLevel
    message: str
    details: Dict[str, Any]
    resolved: bool = False


class DetectionMonitor:
    """
    Real-time detection monitoring dashboard
    Shows bot detection events, system health, and provides quick actions
    """
    
    def __init__(self, parent: Optional[tk.Widget] = None):
        # Create root window if not provided
        self.root = parent or tk.Tk()
        if not parent:
            self.root.title("StealthMaster AI v3.0 - Detection Monitor")
            self.root.geometry("800x600")
            
        # Event queue for thread-safe updates
        self.event_queue = queue.Queue()
        
        # Detection history
        self.detection_events: List[DetectionEvent] = []
        self.active_threats: Dict[str, DetectionEvent] = {}
        
        # System status
        self.system_status = {
            'stealth_score': 100.0,
            'active_monitors': 0,
            'proxy_health': 100.0,
            'data_usage_mb': 0.0,
            'success_rate': 0.0
        }
        
        # UI elements
        self.setup_ui()
        
        # Start update loop
        self.running = True
        self.update_loop()
        
    def setup_ui(self):
        """Create the monitoring interface"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 1. Header with overall status
        self.create_header(main_frame)
        
        # 2. Active threats panel
        self.create_threats_panel(main_frame)
        
        # 3. Detection log
        self.create_detection_log(main_frame)
        
        # 4. Quick actions bar
        self.create_actions_bar(main_frame)
        
        # 5. Status bar
        self.create_status_bar(main_frame)
        
    def create_header(self, parent):
        """Create header with overall system status"""
        
        header_frame = ttk.LabelFrame(parent, text="System Status", padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Stealth Score (big and prominent)
        score_frame = ttk.Frame(header_frame)
        score_frame.grid(row=0, column=0, padx=20)
        
        self.score_label = tk.Label(
            score_frame, 
            text="100", 
            font=("Arial", 48, "bold"),
            fg="#2ECC71"
        )
        self.score_label.pack()
        
        tk.Label(score_frame, text="Stealth Score", font=("Arial", 12)).pack()
        
        # Other metrics
        metrics_frame = ttk.Frame(header_frame)
        metrics_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        self.metric_labels = {}
        metrics = [
            ("Active Monitors", "active_monitors", "🖥️"),
            ("Proxy Health", "proxy_health", "🌐"),
            ("Data Usage", "data_usage_mb", "📊"),
            ("Success Rate", "success_rate", "🎯")
        ]
        
        for i, (name, key, icon) in enumerate(metrics):
            frame = ttk.Frame(metrics_frame)
            frame.grid(row=i // 2, column=i % 2, padx=10, pady=5, sticky=tk.W)
            
            tk.Label(frame, text=f"{icon} {name}:", font=("Arial", 10)).pack(side=tk.LEFT)
            self.metric_labels[key] = tk.Label(frame, text="--", font=("Arial", 10, "bold"))
            self.metric_labels[key].pack(side=tk.LEFT, padx=(5, 0))
            
    def create_threats_panel(self, parent):
        """Create active threats panel"""
        
        threats_frame = ttk.LabelFrame(parent, text="Active Threats", padding="10")
        threats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Threat indicators
        self.threat_frame = ttk.Frame(threats_frame)
        self.threat_frame.pack(fill=tk.X)
        
        # Initially show "All Clear"
        self.all_clear_label = tk.Label(
            self.threat_frame,
            text="✅ All Systems Clear",
            font=("Arial", 14),
            fg="#2ECC71"
        )
        self.all_clear_label.pack(pady=10)
        
    def create_detection_log(self, parent):
        """Create scrollable detection event log"""
        
        log_frame = ttk.LabelFrame(parent, text="Detection Log", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Scrolled text widget
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=80,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for different threat levels
        for level in ThreatLevel:
            _, color, _ = level.value
            self.log_text.tag_configure(level.name, foreground=color)
            
        # Initial message
        self.log_text.insert(tk.END, "🚀 Detection Monitor Started\n", "CLEAR")
        self.log_text.insert(tk.END, "-" * 80 + "\n", "CLEAR")
        
    def create_actions_bar(self, parent):
        """Create quick actions bar"""
        
        actions_frame = ttk.Frame(parent)
        actions_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Action buttons
        ttk.Button(
            actions_frame,
            text="🔄 Rotate All Proxies",
            command=self.rotate_proxies
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            actions_frame,
            text="🛡️ Ultra Stealth Mode",
            command=self.enable_ultra_stealth
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            actions_frame,
            text="⏸️ Pause All",
            command=self.pause_all
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            actions_frame,
            text="🧹 Clear Resolved",
            command=self.clear_resolved
        ).pack(side=tk.LEFT, padx=5)
        
        # Export button
        ttk.Button(
            actions_frame,
            text="💾 Export Log",
            command=self.export_log
        ).pack(side=tk.RIGHT)
        
    def create_status_bar(self, parent):
        """Create status bar at bottom"""
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)
        
    def add_detection_event(
        self,
        platform: str,
        event_type: str,
        threat_level: ThreatLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Add a new detection event"""
        
        event = DetectionEvent(
            timestamp=datetime.now(),
            platform=platform,
            event_type=event_type,
            threat_level=threat_level,
            message=message,
            details=details or {}
        )
        
        # Thread-safe queue
        self.event_queue.put(('detection', event))
        
    def update_system_status(self, status: Dict[str, Any]):
        """Update system status metrics"""
        self.event_queue.put(('status', status))
        
    def update_loop(self):
        """Main update loop for UI"""
        
        # Process queued events
        try:
            while True:
                event_type, data = self.event_queue.get_nowait()
                
                if event_type == 'detection':
                    self._process_detection_event(data)
                elif event_type == 'status':
                    self._update_status_display(data)
                    
        except queue.Empty:
            pass
            
        # Update threat display
        self._update_threat_display()
        
        # Schedule next update
        if self.running:
            self.root.after(100, self.update_loop)
            
    def _process_detection_event(self, event: DetectionEvent):
        """Process a detection event"""
        
        # Add to history
        self.detection_events.append(event)
        
        # Add to active threats if not resolved
        if not event.resolved and event.threat_level.value[0] in ['medium', 'high', 'critical']:
            self.active_threats[f"{event.platform}_{event.event_type}"] = event
            
        # Log the event
        self._log_event(event)
        
        # Update stealth score
        self._update_stealth_score(event)
        
        # Update status
        self.status_label.config(text=f"Last event: {event.message}")
        
    def _log_event(self, event: DetectionEvent):
        """Log event to display"""
        
        timestamp = event.timestamp.strftime("%H:%M:%S")
        icon = event.threat_level.value[2]
        
        # Format log entry
        log_entry = f"[{timestamp}] {icon} {event.platform.upper()} - {event.message}"
        
        # Add details if present
        if event.details:
            for key, value in event.details.items():
                log_entry += f"\n    {key}: {value}"
                
        log_entry += "\n"
        
        # Insert with color tag
        self.log_text.insert(tk.END, log_entry, event.threat_level.name)
        self.log_text.see(tk.END)  # Auto-scroll
        
    def _update_stealth_score(self, event: DetectionEvent):
        """Update stealth score based on detection event"""
        
        # Score penalties
        penalties = {
            ThreatLevel.LOW: 5,
            ThreatLevel.MEDIUM: 15,
            ThreatLevel.HIGH: 30,
            ThreatLevel.CRITICAL: 50
        }
        
        penalty = penalties.get(event.threat_level, 0)
        self.system_status['stealth_score'] = max(0, self.system_status['stealth_score'] - penalty)
        
        # Update display
        score = int(self.system_status['stealth_score'])
        self.score_label.config(text=str(score))
        
        # Update color based on score
        if score >= 80:
            color = "#2ECC71"  # Green
        elif score >= 60:
            color = "#F39C12"  # Orange
        elif score >= 40:
            color = "#E74C3C"  # Red
        else:
            color = "#8E44AD"  # Purple
            
        self.score_label.config(fg=color)
        
    def _update_status_display(self, status: Dict[str, Any]):
        """Update status metrics display"""
        
        self.system_status.update(status)
        
        # Update metric labels
        for key, label in self.metric_labels.items():
            if key in self.system_status:
                value = self.system_status[key]
                
                if key == 'data_usage_mb':
                    text = f"{value:.1f} MB"
                elif key == 'success_rate':
                    text = f"{value:.1%}"
                elif key == 'proxy_health':
                    text = f"{value:.0f}%"
                else:
                    text = str(value)
                    
                label.config(text=text)
                
    def _update_threat_display(self):
        """Update active threats display"""
        
        # Clear existing widgets
        for widget in self.threat_frame.winfo_children():
            widget.destroy()
            
        if not self.active_threats:
            # Show all clear
            self.all_clear_label = tk.Label(
                self.threat_frame,
                text="✅ All Systems Clear",
                font=("Arial", 14),
                fg="#2ECC71"
            )
            self.all_clear_label.pack(pady=10)
        else:
            # Show active threats
            for threat_id, event in self.active_threats.items():
                threat_widget = self._create_threat_widget(event)
                threat_widget.pack(fill=tk.X, padx=5, pady=2)
                
    def _create_threat_widget(self, event: DetectionEvent) -> tk.Frame:
        """Create widget for single threat"""
        
        frame = tk.Frame(self.threat_frame, relief=tk.RAISED, bd=1)
        
        # Threat info
        _, color, icon = event.threat_level.value
        
        info_text = f"{icon} {event.platform.upper()}: {event.message}"
        label = tk.Label(frame, text=info_text, fg=color, font=("Arial", 10))
        label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Resolve button
        resolve_btn = tk.Button(
            frame,
            text="✓ Resolve",
            command=lambda: self.resolve_threat(f"{event.platform}_{event.event_type}"),
            font=("Arial", 8)
        )
        resolve_btn.pack(side=tk.RIGHT, padx=5)
        
        return frame
        
    def resolve_threat(self, threat_id: str):
        """Mark threat as resolved"""
        
        if threat_id in self.active_threats:
            event = self.active_threats[threat_id]
            event.resolved = True
            del self.active_threats[threat_id]
            
            # Log resolution
            self._log_event(DetectionEvent(
                timestamp=datetime.now(),
                platform=event.platform,
                event_type="resolution",
                threat_level=ThreatLevel.CLEAR,
                message=f"Resolved: {event.message}",
                details={},
                resolved=True
            ))
            
            # Restore some stealth score
            self.system_status['stealth_score'] = min(100, self.system_status['stealth_score'] + 10)
            
    def rotate_proxies(self):
        """Trigger proxy rotation"""
        logger.info("Rotating all proxies")
        self.status_label.config(text="Rotating proxies...")
        # In real implementation, this would trigger actual proxy rotation
        
    def enable_ultra_stealth(self):
        """Enable ultra stealth mode"""
        logger.info("Enabling ultra stealth mode")
        self.status_label.config(text="Ultra stealth mode activated")
        # In real implementation, this would trigger mode change
        
    def pause_all(self):
        """Pause all monitoring"""
        logger.info("Pausing all monitors")
        self.status_label.config(text="All monitors paused")
        # In real implementation, this would pause the system
        
    def clear_resolved(self):
        """Clear resolved events from log"""
        self.detection_events = [e for e in self.detection_events if not e.resolved]
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "🧹 Cleared resolved events\n", "CLEAR")
        self.log_text.insert(tk.END, "-" * 80 + "\n", "CLEAR")
        
    def export_log(self):
        """Export detection log to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detection_log_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write("StealthMaster AI v3.0 - Detection Log\n")
            f.write("=" * 80 + "\n\n")
            
            for event in self.detection_events:
                f.write(f"[{event.timestamp}] {event.platform} - {event.message}\n")
                f.write(f"  Threat Level: {event.threat_level.name}\n")
                f.write(f"  Type: {event.event_type}\n")
                
                if event.details:
                    f.write("  Details:\n")
                    for key, value in event.details.items():
                        f.write(f"    {key}: {value}\n")
                        
                f.write("\n")
                
        self.status_label.config(text=f"Log exported to {filename}")
        
    def stop(self):
        """Stop the monitor"""
        self.running = False
        

def create_detection_monitor(parent=None) -> DetectionMonitor:
    """Factory function to create detection monitor"""
    return DetectionMonitor(parent)
    

if __name__ == "__main__":
    # Test the detection monitor
    monitor = create_detection_monitor()
    
    # Simulate some events
    def simulate_events():
        import random
        
        platforms = ["fansale", "ticketmaster", "vivaticket"]
        
        # Initial good status
        monitor.update_system_status({
            'active_monitors': 3,
            'proxy_health': 95.0,
            'data_usage_mb': 12.5,
            'success_rate': 0.85
        })
        
        # Simulate detection events
        events = [
            ("CDP detection attempt", ThreatLevel.LOW, "Runtime.Enable detected and blocked"),
            ("Cloudflare challenge", ThreatLevel.MEDIUM, "Cloudflare bot check triggered"),
            ("Rate limit hit", ThreatLevel.HIGH, "Too many requests - entering backoff"),
            ("Account flagged", ThreatLevel.CRITICAL, "Account temporarily suspended")
        ]
        
        for i in range(5):
            monitor.root.after(2000 * i, lambda: monitor.add_detection_event(
                platform=random.choice(platforms),
                event_type="bot_detection",
                threat_level=random.choice(list(ThreatLevel)),
                message=random.choice(events)[0],
                details={"ip": "1.2.3.4", "proxy": "geo.iproyal.com"}
            ))
            
    simulate_events()
    
    # Run the GUI
    monitor.root.mainloop()
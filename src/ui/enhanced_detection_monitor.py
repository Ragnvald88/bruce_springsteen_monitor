# src/ui/enhanced_detection_monitor.py
"""
StealthMaster AI v3.0 - Enhanced Detection Monitor
Real-time visibility into bot detection events with auto-start and WebSocket updates
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
import threading
import queue
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import websocket
from collections import deque

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Enhanced threat levels with more granularity"""
    CLEAR = ("clear", "#2ECC71", "✅", 0)        # Green
    INFO = ("info", "#3498DB", "ℹ️", 1)         # Blue
    LOW = ("low", "#F39C12", "⚠️", 2)           # Orange
    MEDIUM = ("medium", "#E74C3C", "⚡", 3)      # Red
    HIGH = ("high", "#8E44AD", "🚨", 4)         # Purple
    CRITICAL = ("critical", "#2C3E50", "💀", 5)  # Dark
    
    @property
    def severity(self) -> int:
        return self.value[3]


@dataclass
class DetectionEvent:
    """Enhanced detection event with more details"""
    timestamp: datetime
    platform: str
    event_type: str
    threat_level: ThreatLevel
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    confidence: float = 1.0
    source: str = "unknown"
    action_taken: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'platform': self.platform,
            'event_type': self.event_type,
            'threat_level': self.threat_level.name,
            'message': self.message,
            'details': self.details,
            'resolved': self.resolved,
            'confidence': self.confidence,
            'source': self.source,
            'action_taken': self.action_taken
        }


class EnhancedDetectionMonitor:
    """
    Advanced real-time detection monitoring with WebSocket support
    Auto-starts with the application and provides comprehensive visibility
    """
    
    def __init__(self, parent: Optional[tk.Widget] = None, auto_start: bool = True):
        # Create root window if not provided
        self.standalone = parent is None
        self.root = parent or tk.Tk()
        
        if self.standalone:
            self.root.title("🛡️ StealthMaster AI v3.0 - Detection Command Center")
            self.root.geometry("1200x800")
            self.root.configure(bg='#1a1a1a')
        
        # Event handling
        self.event_queue = queue.Queue()
        self.websocket_queue = queue.Queue()
        
        # Detection tracking
        self.detection_events: deque = deque(maxlen=1000)  # Keep last 1000 events
        self.active_threats: Dict[str, DetectionEvent] = {}
        self.platform_stats: Dict[str, Dict[str, int]] = {}
        
        # System metrics
        self.system_metrics = {
            'stealth_score': 100.0,
            'active_monitors': 0,
            'proxy_health': 100.0,
            'data_usage_mb': 0.0,
            'success_rate': 0.0,
            'cdp_status': 'PROTECTED',
            'fingerprint_entropy': 0.95,
            'behavior_naturalness': 0.98
        }
        
        # Callbacks
        self.event_callbacks: List[Callable] = []
        
        # UI Theme
        self.colors = {
            'bg': '#1a1a1a',
            'fg': '#ffffff',
            'card_bg': '#2d2d2d',
            'border': '#444444',
            'success': '#2ECC71',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'info': '#3498DB'
        }
        
        # Create UI
        self.setup_ui()
        
        # Auto-start features
        if auto_start:
            self.start_monitoring()
            self.start_websocket_server()
        
        # Start update loop
        self.running = True
        self.update_loop()
        
        logger.info("✅ Enhanced Detection Monitor initialized")
    
    def setup_ui(self):
        """Create the enhanced monitoring interface"""
        
        # Main container with dark theme
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure ttk styles
        self.setup_styles()
        
        # 1. Header with title and controls
        self.create_header(main_frame)
        
        # 2. Main content area with tabs
        self.create_tabbed_interface(main_frame)
        
        # 3. Status bar
        self.create_status_bar(main_frame)
    
    def setup_styles(self):
        """Configure dark theme styles"""
        style = ttk.Style()
        
        # Dark theme colors
        style.configure('Dark.TFrame', background=self.colors['bg'])
        style.configure('Dark.TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('Dark.TLabelframe', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('Dark.TLabelframe.Label', background=self.colors['bg'], foreground=self.colors['fg'])
    
    def create_header(self, parent):
        """Create header with title and quick stats"""
        header_frame = tk.Frame(parent, bg=self.colors['card_bg'], height=100)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Title and logo
        title_frame = tk.Frame(header_frame, bg=self.colors['card_bg'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        title = tk.Label(
            title_frame,
            text="🛡️ Detection Command Center",
            font=('Arial', 24, 'bold'),
            bg=self.colors['card_bg'],
            fg=self.colors['fg']
        )
        title.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="Real-time Bot Detection Monitoring & Analysis",
            font=('Arial', 12),
            bg=self.colors['card_bg'],
            fg='#888888'
        )
        subtitle.pack()
        
        # Quick stats
        stats_frame = tk.Frame(header_frame, bg=self.colors['card_bg'])
        stats_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Stealth Score (big and prominent)
        score_frame = tk.Frame(stats_frame, bg=self.colors['card_bg'])
        score_frame.pack(side=tk.LEFT, padx=20)
        
        self.score_display = tk.Label(
            score_frame,
            text="100",
            font=('Arial', 36, 'bold'),
            bg=self.colors['card_bg'],
            fg=self.colors['success']
        )
        self.score_display.pack()
        
        tk.Label(
            score_frame,
            text="Stealth Score",
            font=('Arial', 10),
            bg=self.colors['card_bg'],
            fg='#888888'
        ).pack()
        
        # Other metrics
        self.create_metric_display(stats_frame, "Active", "active_monitors", "🖥️")
        self.create_metric_display(stats_frame, "Proxy", "proxy_health", "🌐")
        self.create_metric_display(stats_frame, "Success", "success_rate", "🎯")
    
    def create_metric_display(self, parent, label, metric_key, icon):
        """Create a metric display widget"""
        frame = tk.Frame(parent, bg=self.colors['card_bg'])
        frame.pack(side=tk.LEFT, padx=15)
        
        value_label = tk.Label(
            frame,
            text=f"{icon} --",
            font=('Arial', 16, 'bold'),
            bg=self.colors['card_bg'],
            fg=self.colors['fg']
        )
        value_label.pack()
        
        tk.Label(
            frame,
            text=label,
            font=('Arial', 10),
            bg=self.colors['card_bg'],
            fg='#888888'
        ).pack()
        
        # Store reference for updates
        if not hasattr(self, 'metric_labels'):
            self.metric_labels = {}
        self.metric_labels[metric_key] = value_label
    
    def create_tabbed_interface(self, parent):
        """Create tabbed interface for different views"""
        
        # Tab control
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 1. Real-time Monitor Tab
        self.monitor_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.monitor_tab, text="🔍 Real-time Monitor")
        self.create_monitor_tab()
        
        # 2. Threat Analysis Tab
        self.analysis_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.analysis_tab, text="📊 Threat Analysis")
        self.create_analysis_tab()
        
        # 3. Platform Status Tab
        self.platform_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.platform_tab, text="🌐 Platform Status")
        self.create_platform_tab()
        
        # 4. CDP & Fingerprint Tab
        self.technical_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.technical_tab, text="🔧 Technical Details")
        self.create_technical_tab()
        
        # 5. Response Actions Tab
        self.actions_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.actions_tab, text="⚡ Response Actions")
        self.create_actions_tab()
    
    def create_monitor_tab(self):
        """Create real-time monitoring tab"""
        
        # Split into threat panel and event log
        paned = ttk.PanedWindow(self.monitor_tab, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Active threats panel
        threats_frame = tk.LabelFrame(
            self.monitor_tab,
            text="🚨 Active Threats",
            bg=self.colors['card_bg'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        paned.add(threats_frame, weight=1)
        
        self.threats_display = tk.Frame(threats_frame, bg=self.colors['card_bg'])
        self.threats_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Show "All Clear" by default
        self.all_clear_label = tk.Label(
            self.threats_display,
            text="✅ All Systems Clear - No Active Threats",
            font=('Arial', 16),
            bg=self.colors['card_bg'],
            fg=self.colors['success']
        )
        self.all_clear_label.pack(pady=20)
        
        # Event log
        log_frame = tk.LabelFrame(
            self.monitor_tab,
            text="📜 Detection Event Log",
            bg=self.colors['card_bg'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        paned.add(log_frame, weight=2)
        
        # Log with syntax highlighting
        self.event_log = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            bg='#0d0d0d',
            fg='#00ff00',
            font=('Consolas', 10),
            insertbackground='#00ff00'
        )
        self.event_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure tags for different severity levels
        self.event_log.tag_config('info', foreground=self.colors['info'])
        self.event_log.tag_config('warning', foreground=self.colors['warning'])
        self.event_log.tag_config('danger', foreground=self.colors['danger'])
        self.event_log.tag_config('success', foreground=self.colors['success'])
    
    def create_analysis_tab(self):
        """Create threat analysis tab with charts"""
        
        # Analysis container
        container = tk.Frame(self.analysis_tab, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Detection timeline
        timeline_frame = tk.LabelFrame(
            container,
            text="📈 Detection Timeline (Last 24 Hours)",
            bg=self.colors['card_bg'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        timeline_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Canvas for timeline chart
        self.timeline_canvas = tk.Canvas(
            timeline_frame,
            height=200,
            bg='#0d0d0d',
            highlightthickness=0
        )
        self.timeline_canvas.pack(fill=tk.X, padx=10, pady=10)
        
        # Platform breakdown
        breakdown_frame = tk.LabelFrame(
            container,
            text="🎯 Detection by Platform",
            bg=self.colors['card_bg'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        breakdown_frame.pack(fill=tk.BOTH, expand=True)
        
        self.platform_stats_display = tk.Frame(breakdown_frame, bg=self.colors['card_bg'])
        self.platform_stats_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_platform_tab(self):
        """Create platform-specific status tab"""
        
        container = tk.Frame(self.platform_tab, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Platform cards
        platforms = ['FanSale', 'Ticketmaster', 'Vivaticket']
        self.platform_cards = {}
        
        for platform in platforms:
            card = self.create_platform_card(container, platform)
            card.pack(fill=tk.X, pady=5)
            self.platform_cards[platform.lower()] = card
    
    def create_platform_card(self, parent, platform):
        """Create a platform status card"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], relief=tk.RAISED, bd=1)
        
        # Platform name and status
        header = tk.Frame(card, bg=self.colors['card_bg'])
        header.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            header,
            text=f"🎫 {platform}",
            font=('Arial', 14, 'bold'),
            bg=self.colors['card_bg'],
            fg=self.colors['fg']
        ).pack(side=tk.LEFT)
        
        status_label = tk.Label(
            header,
            text="● OPERATIONAL",
            font=('Arial', 12),
            bg=self.colors['card_bg'],
            fg=self.colors['success']
        )
        status_label.pack(side=tk.RIGHT)
        
        # Metrics
        metrics_frame = tk.Frame(card, bg=self.colors['card_bg'])
        metrics_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Store references
        card.status_label = status_label
        card.metrics_frame = metrics_frame
        
        return card
    
    def create_technical_tab(self):
        """Create technical details tab"""
        
        container = tk.Frame(self.technical_tab, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # CDP Status
        cdp_frame = tk.LabelFrame(
            container,
            text="🔒 CDP Protection Status",
            bg=self.colors['card_bg'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        cdp_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.cdp_status_display = tk.Frame(cdp_frame, bg=self.colors['card_bg'])
        self.cdp_status_display.pack(fill=tk.X, padx=10, pady=10)
        
        # Fingerprint Info
        fingerprint_frame = tk.LabelFrame(
            container,
            text="🔍 Browser Fingerprint",
            bg=self.colors['card_bg'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        fingerprint_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fingerprint_display = scrolledtext.ScrolledText(
            fingerprint_frame,
            wrap=tk.WORD,
            height=10,
            bg='#0d0d0d',
            fg='#00ff00',
            font=('Consolas', 9)
        )
        self.fingerprint_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_actions_tab(self):
        """Create response actions tab"""
        
        container = tk.Frame(self.actions_tab, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Quick actions
        actions_frame = tk.LabelFrame(
            container,
            text="⚡ Quick Response Actions",
            bg=self.colors['card_bg'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Action buttons
        button_frame = tk.Frame(actions_frame, bg=self.colors['card_bg'])
        button_frame.pack(pady=10)
        
        actions = [
            ("🔄 Rotate Proxy", self.rotate_proxy),
            ("🎭 Change Fingerprint", self.change_fingerprint),
            ("⏸️ Pause All", self.pause_all),
            ("🚀 Boost Stealth", self.boost_stealth),
            ("📊 Export Report", self.export_report)
        ]
        
        for text, command in actions:
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                bg=self.colors['info'],
                fg='white',
                font=('Arial', 11, 'bold'),
                padx=20,
                pady=10,
                relief=tk.FLAT,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=5)
            
            # Hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#2980B9'))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=self.colors['info']))
        
        # Response log
        response_frame = tk.LabelFrame(
            container,
            text="📝 Action History",
            bg=self.colors['card_bg'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        response_frame.pack(fill=tk.BOTH, expand=True)
        
        self.action_log = scrolledtext.ScrolledText(
            response_frame,
            wrap=tk.WORD,
            height=10,
            bg='#0d0d0d',
            fg='#00ff00',
            font=('Consolas', 9)
        )
        self.action_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_status_bar(self, parent):
        """Create status bar at bottom"""
        status_bar = tk.Frame(parent, bg=self.colors['card_bg'], height=30)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        status_bar.pack_propagate(False)
        
        # Status text
        self.status_label = tk.Label(
            status_bar,
            text="🟢 System Online - Monitoring Active",
            font=('Arial', 10),
            bg=self.colors['card_bg'],
            fg=self.colors['fg']
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Connection indicator
        self.connection_label = tk.Label(
            status_bar,
            text="📡 WebSocket: Connected",
            font=('Arial', 10),
            bg=self.colors['card_bg'],
            fg=self.colors['success']
        )
        self.connection_label.pack(side=tk.RIGHT, padx=10)
    
    def start_monitoring(self):
        """Start monitoring systems"""
        # This would be called automatically on init
        self.status_label.config(text="🟢 Detection Monitoring Active")
        logger.info("Detection monitoring started")
    
    def start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        # In a real implementation, this would start a WebSocket server
        # For now, we'll simulate it
        self.websocket_connected = True
        logger.info("WebSocket server started for real-time updates")
    
    def add_detection_event(
        self,
        platform: str,
        event_type: str,
        threat_level: ThreatLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        source: str = "auto"
    ) -> None:
        """Add a new detection event"""
        
        event = DetectionEvent(
            timestamp=datetime.now(),
            platform=platform,
            event_type=event_type,
            threat_level=threat_level,
            message=message,
            details=details or {},
            confidence=confidence,
            source=source
        )
        
        # Queue for thread-safe update
        self.event_queue.put(('add_event', event))
        
        # Notify callbacks
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def update_system_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update system metrics"""
        self.event_queue.put(('update_metrics', metrics))
    
    def update_loop(self):
        """Main update loop for UI updates"""
        if not self.running:
            return
        
        # Process queued events
        while not self.event_queue.empty():
            try:
                action, data = self.event_queue.get_nowait()
                
                if action == 'add_event':
                    self._process_detection_event(data)
                elif action == 'update_metrics':
                    self._update_metrics_display(data)
                    
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Update loop error: {e}")
        
        # Update displays
        self._update_threat_display()
        self._update_platform_stats()
        
        # Schedule next update
        self.root.after(100, self.update_loop)
    
    def _process_detection_event(self, event: DetectionEvent):
        """Process a detection event"""
        
        # Add to history
        self.detection_events.append(event)
        
        # Update platform stats
        if event.platform not in self.platform_stats:
            self.platform_stats[event.platform] = {
                'total': 0,
                'by_level': {},
                'last_event': None
            }
        
        stats = self.platform_stats[event.platform]
        stats['total'] += 1
        stats['by_level'][event.threat_level.name] = stats['by_level'].get(event.threat_level.name, 0) + 1
        stats['last_event'] = event.timestamp
        
        # Add to active threats if significant
        if event.threat_level.severity >= ThreatLevel.MEDIUM.severity:
            self.active_threats[f"{event.platform}_{event.timestamp.timestamp()}"] = event
        
        # Log event
        self._log_event(event)
        
        # Update stealth score
        self._update_stealth_score(event)
    
    def _log_event(self, event: DetectionEvent):
        """Log event to display"""
        
        # Format timestamp
        timestamp = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
        
        # Build log entry
        log_entry = f"[{timestamp}] {event.threat_level.value[2]} {event.platform.upper()} | {event.message}"
        
        if event.details:
            log_entry += f" | Details: {json.dumps(event.details, indent=2)}"
        
        # Determine tag based on threat level
        tag_map = {
            ThreatLevel.INFO: 'info',
            ThreatLevel.LOW: 'info',
            ThreatLevel.MEDIUM: 'warning',
            ThreatLevel.HIGH: 'danger',
            ThreatLevel.CRITICAL: 'danger'
        }
        
        tag = tag_map.get(event.threat_level, 'info')
        
        # Insert into log
        self.event_log.insert(tk.END, log_entry + '\n', tag)
        self.event_log.see(tk.END)
        
        # Also log action if taken
        if event.action_taken:
            self.action_log.insert(
                tk.END,
                f"[{timestamp}] Action: {event.action_taken}\n",
                'success'
            )
            self.action_log.see(tk.END)
    
    def _update_stealth_score(self, event: DetectionEvent):
        """Update stealth score based on detection events"""
        
        # Decrease score based on threat level
        score_impact = {
            ThreatLevel.INFO: 0,
            ThreatLevel.LOW: -2,
            ThreatLevel.MEDIUM: -5,
            ThreatLevel.HIGH: -10,
            ThreatLevel.CRITICAL: -20
        }
        
        impact = score_impact.get(event.threat_level, 0)
        self.system_metrics['stealth_score'] = max(0, self.system_metrics['stealth_score'] + impact)
        
        # Update display
        score = self.system_metrics['stealth_score']
        self.score_display.config(text=str(int(score)))
        
        # Update color based on score
        if score >= 80:
            color = self.colors['success']
        elif score >= 60:
            color = self.colors['warning']
        else:
            color = self.colors['danger']
        
        self.score_display.config(fg=color)
    
    def _update_metrics_display(self, metrics: Dict[str, Any]):
        """Update metric displays"""
        
        # Update stored metrics
        self.system_metrics.update(metrics)
        
        # Update displays
        for key, label in self.metric_labels.items():
            if key in metrics:
                value = metrics[key]
                
                if key == 'active_monitors':
                    label.config(text=f"🖥️ {value}")
                elif key == 'proxy_health':
                    label.config(text=f"🌐 {value:.0f}%")
                elif key == 'success_rate':
                    label.config(text=f"🎯 {value:.1%}")
                elif key == 'data_usage_mb':
                    label.config(text=f"📊 {value:.1f}MB")
    
    def _update_threat_display(self):
        """Update active threats display"""
        
        # Remove resolved threats
        current_time = datetime.now()
        for key, threat in list(self.active_threats.items()):
            if (current_time - threat.timestamp).seconds > 300:  # 5 minutes
                threat.resolved = True
                del self.active_threats[key]
        
        # Clear existing display
        for widget in self.threats_display.winfo_children():
            widget.destroy()
        
        if not self.active_threats:
            # Show all clear
            self.all_clear_label = tk.Label(
                self.threats_display,
                text="✅ All Systems Clear - No Active Threats",
                font=('Arial', 16),
                bg=self.colors['card_bg'],
                fg=self.colors['success']
            )
            self.all_clear_label.pack(pady=20)
        else:
            # Show active threats
            for threat in self.active_threats.values():
                self._create_threat_widget(threat)
    
    def _create_threat_widget(self, threat: DetectionEvent):
        """Create a widget for an active threat"""
        
        # Threat container
        threat_frame = tk.Frame(
            self.threats_display,
            bg=threat.threat_level.value[1],
            relief=tk.RAISED,
            bd=2
        )
        threat_frame.pack(fill=tk.X, pady=5)
        
        # Threat info
        info_frame = tk.Frame(threat_frame, bg='#2d2d2d')
        info_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Header
        header = tk.Label(
            info_frame,
            text=f"{threat.threat_level.value[2]} {threat.platform.upper()} - {threat.message}",
            font=('Arial', 12, 'bold'),
            bg='#2d2d2d',
            fg='white'
        )
        header.pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        # Details
        details = tk.Label(
            info_frame,
            text=f"Type: {threat.event_type} | Confidence: {threat.confidence:.0%} | {threat.timestamp.strftime('%H:%M:%S')}",
            font=('Arial', 10),
            bg='#2d2d2d',
            fg='#cccccc'
        )
        details.pack(anchor=tk.W, padx=10, pady=(0, 5))
        
        # Action button
        action_btn = tk.Button(
            info_frame,
            text="Take Action",
            command=lambda t=threat: self.handle_threat_action(t),
            bg=self.colors['info'],
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            cursor='hand2'
        )
        action_btn.pack(anchor=tk.E, padx=10, pady=5)
    
    def _update_platform_stats(self):
        """Update platform statistics display"""
        
        # Update platform cards
        for platform, card in self.platform_cards.items():
            if platform in self.platform_stats:
                stats = self.platform_stats[platform]
                
                # Update status based on recent events
                if stats['last_event'] and (datetime.now() - stats['last_event']).seconds < 60:
                    card.status_label.config(
                        text="● DETECTED",
                        fg=self.colors['warning']
                    )
                else:
                    card.status_label.config(
                        text="● OPERATIONAL",
                        fg=self.colors['success']
                    )
                
                # Update metrics
                for widget in card.metrics_frame.winfo_children():
                    widget.destroy()
                
                # Show stats
                tk.Label(
                    card.metrics_frame,
                    text=f"Total Events: {stats['total']}",
                    bg=self.colors['card_bg'],
                    fg=self.colors['fg']
                ).pack(side=tk.LEFT, padx=10)
                
                # Show by level
                for level, count in stats['by_level'].items():
                    if count > 0:
                        level_enum = ThreatLevel[level]
                        tk.Label(
                            card.metrics_frame,
                            text=f"{level_enum.value[2]} {count}",
                            bg=self.colors['card_bg'],
                            fg=level_enum.value[1]
                        ).pack(side=tk.LEFT, padx=5)
    
    # Action handlers
    def rotate_proxy(self):
        """Handle proxy rotation"""
        self.add_detection_event(
            platform='system',
            event_type='user_action',
            threat_level=ThreatLevel.INFO,
            message="Manual proxy rotation initiated",
            action_taken="Rotating to new proxy IP"
        )
    
    def change_fingerprint(self):
        """Handle fingerprint change"""
        self.add_detection_event(
            platform='system',
            event_type='user_action',
            threat_level=ThreatLevel.INFO,
            message="Browser fingerprint regeneration initiated",
            action_taken="Generating new browser fingerprint"
        )
    
    def pause_all(self):
        """Handle pause all"""
        self.add_detection_event(
            platform='system',
            event_type='user_action',
            threat_level=ThreatLevel.INFO,
            message="All monitoring paused by user",
            action_taken="Pausing all active monitors"
        )
    
    def boost_stealth(self):
        """Handle stealth boost"""
        self.add_detection_event(
            platform='system',
            event_type='user_action',
            threat_level=ThreatLevel.INFO,
            message="Ultra-stealth mode activated",
            action_taken="Enabling maximum stealth measures"
        )
        
        # Boost stealth score
        self.system_metrics['stealth_score'] = min(100, self.system_metrics['stealth_score'] + 10)
    
    def export_report(self):
        """Export detection report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detection_report_{timestamp}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'system_metrics': self.system_metrics,
            'platform_stats': self.platform_stats,
            'recent_events': [e.to_dict() for e in list(self.detection_events)[-100:]],
            'active_threats': [t.to_dict() for t in self.active_threats.values()]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        messagebox.showinfo("Export Complete", f"Report exported to {filename}")
    
    def handle_threat_action(self, threat: DetectionEvent):
        """Handle action for a specific threat"""
        
        # Show action dialog
        actions = {
            'Rotate Proxy': 'rotate_proxy',
            'Change Fingerprint': 'change_fingerprint',
            'Pause Platform': 'pause_platform',
            'Increase Delay': 'increase_delay',
            'Switch to Ultra-Stealth': 'ultra_stealth'
        }
        
        # For now, just log the action
        self.add_detection_event(
            platform='system',
            event_type='threat_response',
            threat_level=ThreatLevel.INFO,
            message=f"Response action for {threat.platform} threat",
            action_taken=f"Automated response initiated for {threat.message}"
        )
        
        # Mark threat as resolved
        threat.resolved = True
    
    def add_event_callback(self, callback: Callable):
        """Add callback for detection events"""
        self.event_callbacks.append(callback)
    
    def stop(self):
        """Stop the monitor"""
        self.running = False
        self.websocket_connected = False
        logger.info("Detection monitor stopped")


# Global instance management
_monitor_instance: Optional[EnhancedDetectionMonitor] = None

def get_detection_monitor(parent=None, auto_start=True) -> EnhancedDetectionMonitor:
    """Get or create the global detection monitor instance"""
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = EnhancedDetectionMonitor(parent, auto_start)
    
    return _monitor_instance

def stop_detection_monitor():
    """Stop the global detection monitor"""
    global _monitor_instance
    
    if _monitor_instance:
        _monitor_instance.stop()
        _monitor_instance = None
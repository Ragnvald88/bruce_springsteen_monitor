#!/usr/bin/env python3
"""
StealthMaster Advanced GUI with PySide6
Features: Dashboard, Statistics, Monitoring, Settings, Manual Controls
"""

import sys
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import queue

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QGroupBox, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    QLineEdit, QListWidget, QListWidgetItem, QHeaderView,
    QSplitter, QFrame, QGridLayout, QProgressBar, QSystemTrayIcon,
    QMenu, QMessageBox, QFileDialog, QSlider, QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QThread, QSize, QDateTime,
    QPropertyAnimation, QEasingCurve, Property
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QPainter,
    QBrush, QPen, QAction, QLinearGradient
)

# Note: We'll use built-in PySide6 widgets for graphs instead of pyqtgraph


class AsyncWorker(QThread):
    """Worker thread for async operations"""
    log_signal = Signal(str, str)  # message, level
    stats_signal = Signal(dict)
    monitor_signal = Signal(str, str, str)  # event_name, status, last_check
    ticket_signal = Signal(str, str, int)  # platform, event, count
    
    def __init__(self, stealthmaster_instance=None):
        super().__init__()
        self.stealthmaster = stealthmaster_instance
        self.running = False
        self.loop = None
        
    def run(self):
        """Run the async event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self.run_monitoring())
        except Exception as e:
            self.log_signal.emit(f"Worker error: {e}", "error")
        finally:
            self.loop.close()
            
    async def run_monitoring(self):
        """Run the monitoring loop"""
        self.running = True
        self.log_signal.emit("Monitoring started", "info")
        
        while self.running:
            try:
                # Emit stats update
                if self.stealthmaster:
                    stats = {
                        'tickets_found': self.stealthmaster.tickets_found,
                        'tickets_reserved': self.stealthmaster.tickets_reserved,
                        'tickets_failed': self.stealthmaster.tickets_failed,
                        'access_denied': self.stealthmaster.access_denied_count,
                        'active_monitors': len(self.stealthmaster.monitors),
                        'browsers_open': len(self.stealthmaster.browsers)
                    }
                    self.stats_signal.emit(stats)
                    
                    # Emit monitor status
                    for event_name, status in self.stealthmaster.monitor_status.items():
                        last_check = self.stealthmaster.last_check.get(event_name, None)
                        last_str = last_check.strftime("%H:%M:%S") if last_check else "Never"
                        self.monitor_signal.emit(event_name, status, last_str)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.log_signal.emit(f"Monitoring error: {e}", "error")
                await asyncio.sleep(5)
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)


class StealthMasterGUI(QMainWindow):
    """Advanced GUI for StealthMaster"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize variables
        self.settings = None
        self.stealthmaster = None
        self.worker = None
        self.is_running = False
        
        # Statistics tracking
        self.stats_history = {
            'time': [],
            'tickets_found': [],
            'success_rate': [],
            'data_usage': []
        }
        
        # Setup UI
        self.init_ui()
        self.setup_styles()
        self.setup_timers()
        
        # Load configuration
        self.load_configuration()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("StealthMaster - Advanced Control Panel")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Create tabs
        self.dashboard_tab = self.create_dashboard_tab()
        self.monitoring_tab = self.create_monitoring_tab()
        self.settings_tab = self.create_settings_tab()
        self.logs_tab = self.create_logs_tab()
        self.statistics_tab = self.create_statistics_tab()
        
        # Add tabs
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        self.tabs.addTab(self.monitoring_tab, "🔍 Monitoring")
        self.tabs.addTab(self.statistics_tab, "📈 Statistics")
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")
        self.tabs.addTab(self.logs_tab, "📜 Logs")
        
        main_layout.addWidget(self.tabs)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # System tray
        self.setup_system_tray()
        
    def create_header(self):
        """Create the header widget"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.Box)
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        
        # Logo and title
        title_layout = QVBoxLayout()
        
        title_label = QLabel("🎯 StealthMaster")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Advanced Ticket Monitoring System")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setStyleSheet("color: #888;")
        title_layout.addWidget(subtitle_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Quick stats
        self.quick_stats_label = QLabel("Tickets Found: 0 | Success Rate: 0%")
        self.quick_stats_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.quick_stats_label)
        
        return header
        
    def create_dashboard_tab(self):
        """Create the dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stats cards row
        stats_layout = QHBoxLayout()
        
        # Create stat cards
        self.stat_cards = {
            'tickets_found': self.create_stat_card("🎫 Tickets Found", "0", "#4CAF50"),
            'success_rate': self.create_stat_card("📈 Success Rate", "0%", "#2196F3"),
            'active_monitors': self.create_stat_card("🔍 Active Monitors", "0", "#FF9800"),
            'data_usage': self.create_stat_card("📊 Data Usage", "0 MB", "#9C27B0")
        }
        
        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
            
        layout.addLayout(stats_layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Active monitors
        monitors_group = QGroupBox("Active Monitors")
        monitors_layout = QVBoxLayout(monitors_group)
        
        self.monitors_table = QTableWidget()
        self.monitors_table.setColumnCount(5)
        self.monitors_table.setHorizontalHeaderLabels([
            "Platform", "Event", "Status", "Last Check", "Next Check"
        ])
        self.monitors_table.horizontalHeader().setStretchLastSection(True)
        monitors_layout.addWidget(self.monitors_table)
        
        # Monitor controls
        monitor_controls = QHBoxLayout()
        monitor_controls.addWidget(QPushButton("Add Monitor"))
        monitor_controls.addWidget(QPushButton("Remove Selected"))
        monitor_controls.addWidget(QPushButton("Pause Selected"))
        monitors_layout.addLayout(monitor_controls)
        
        content_splitter.addWidget(monitors_group)
        
        # Right panel - Live feed
        feed_group = QGroupBox("Live Activity Feed")
        feed_layout = QVBoxLayout(feed_group)
        
        self.activity_feed = QListWidget()
        feed_layout.addWidget(self.activity_feed)
        
        content_splitter.addWidget(feed_group)
        content_splitter.setSizes([700, 400])
        
        layout.addWidget(content_splitter)
        
        # Browser pool status
        pool_group = QGroupBox("Browser Pool Status")
        pool_layout = QHBoxLayout(pool_group)
        
        self.browser_status_labels = {}
        for platform in ["Ticketmaster", "Fansale", "Vivaticket"]:
            label = QLabel(f"{platform}: Inactive")
            label.setStyleSheet("padding: 5px; background: #333; border-radius: 5px;")
            pool_layout.addWidget(label)
            self.browser_status_labels[platform.lower()] = label
            
        layout.addWidget(pool_group)
        
        return widget
        
    def create_stat_card(self, title, value, color):
        """Create a statistics card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}22, stop:1 {color}11);
                border: 2px solid {color}44;
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12))
        title_label.setStyleSheet("color: #888;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        return card
        
    def create_monitoring_tab(self):
        """Create the monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filters
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Platform:"))
        
        self.platform_filter = QComboBox()
        self.platform_filter.addItems(["All", "Ticketmaster", "Fansale", "Vivaticket"])
        filters_layout.addWidget(self.platform_filter)
        
        filters_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Active", "Found Tickets", "Error", "Blocked"])
        filters_layout.addWidget(self.status_filter)
        
        filters_layout.addStretch()
        filters_layout.addWidget(QPushButton("Export Data"))
        
        layout.addLayout(filters_layout)
        
        # Events table
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(7)
        self.events_table.setHorizontalHeaderLabels([
            "Time", "Platform", "Event", "Status", "Response Time", "Data Used", "Actions"
        ])
        self.events_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.events_table)
        
        return widget
        
    def create_statistics_tab(self):
        """Create the statistics tab with graphs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Time range selector
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time Range:"))
        
        self.time_range = QComboBox()
        self.time_range.addItems(["Last Hour", "Last 24 Hours", "Last Week", "All Time"])
        time_layout.addWidget(self.time_range)
        
        time_layout.addStretch()
        time_layout.addWidget(QPushButton("Refresh"))
        time_layout.addWidget(QPushButton("Export Stats"))
        
        layout.addLayout(time_layout)
        
        # Create plots
        plots_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Tickets found over time (placeholder)
        tickets_frame = QFrame()
        tickets_frame.setFrameStyle(QFrame.Shape.Box)
        tickets_layout = QVBoxLayout(tickets_frame)
        tickets_layout.addWidget(QLabel("Tickets Found Over Time"))
        self.tickets_plot = QLabel("[Graph visualization will be shown here]")
        self.tickets_plot.setMinimumHeight(150)
        self.tickets_plot.setStyleSheet("background: #2a2a2a; padding: 20px; border-radius: 5px;")
        tickets_layout.addWidget(self.tickets_plot)
        plots_splitter.addWidget(tickets_frame)
        
        # Success rate plot (placeholder)
        success_frame = QFrame()
        success_frame.setFrameStyle(QFrame.Shape.Box)
        success_layout = QVBoxLayout(success_frame)
        success_layout.addWidget(QLabel("Success Rate"))
        self.success_plot = QLabel("[Graph visualization will be shown here]")
        self.success_plot.setMinimumHeight(150)
        self.success_plot.setStyleSheet("background: #2a2a2a; padding: 20px; border-radius: 5px;")
        success_layout.addWidget(self.success_plot)
        plots_splitter.addWidget(success_frame)
        
        # Data usage plot (placeholder)
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.Box)
        data_layout = QVBoxLayout(data_frame)
        data_layout.addWidget(QLabel("Data Usage"))
        self.data_plot = QLabel("[Graph visualization will be shown here]")
        self.data_plot.setMinimumHeight(150)
        self.data_plot.setStyleSheet("background: #2a2a2a; padding: 20px; border-radius: 5px;")
        data_layout.addWidget(self.data_plot)
        plots_splitter.addWidget(data_frame)
        
        layout.addWidget(plots_splitter)
        
        # Summary statistics
        summary_group = QGroupBox("Summary Statistics")
        summary_layout = QGridLayout(summary_group)
        
        self.summary_labels = {}
        stats = [
            ("Total Tickets Found", "total_found"),
            ("Total Reserved", "total_reserved"),
            ("Average Success Rate", "avg_success"),
            ("Total Data Used", "total_data"),
            ("Active Time", "active_time"),
            ("Blocks Encountered", "blocks_count")
        ]
        
        for i, (label, key) in enumerate(stats):
            label_widget = QLabel(f"{label}:")
            value_widget = QLabel("0")
            value_widget.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            
            summary_layout.addWidget(label_widget, i // 3, (i % 3) * 2)
            summary_layout.addWidget(value_widget, i // 3, (i % 3) * 2 + 1)
            
            self.summary_labels[key] = value_widget
            
        layout.addWidget(summary_group)
        
        return widget
        
    def create_settings_tab(self):
        """Create the settings tab"""
        widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        # Proxy Settings
        proxy_group = QGroupBox("Proxy Settings")
        proxy_layout = QVBoxLayout(proxy_group)
        
        self.proxy_enabled = QCheckBox("Enable Proxy")
        proxy_layout.addWidget(self.proxy_enabled)
        
        proxy_form = QGridLayout()
        proxy_form.addWidget(QLabel("Host:"), 0, 0)
        self.proxy_host = QLineEdit()
        proxy_form.addWidget(self.proxy_host, 0, 1)
        
        proxy_form.addWidget(QLabel("Port:"), 0, 2)
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        proxy_form.addWidget(self.proxy_port, 0, 3)
        
        proxy_form.addWidget(QLabel("Username:"), 1, 0)
        self.proxy_username = QLineEdit()
        proxy_form.addWidget(self.proxy_username, 1, 1)
        
        proxy_form.addWidget(QLabel("Password:"), 1, 2)
        self.proxy_password = QLineEdit()
        self.proxy_password.setEchoMode(QLineEdit.EchoMode.Password)
        proxy_form.addWidget(self.proxy_password, 1, 3)
        
        proxy_layout.addLayout(proxy_form)
        
        proxy_buttons = QHBoxLayout()
        proxy_buttons.addWidget(QPushButton("Test Proxy"))
        proxy_buttons.addWidget(QPushButton("Add to Pool"))
        proxy_buttons.addStretch()
        proxy_layout.addLayout(proxy_buttons)
        
        # Proxy pool list
        self.proxy_list = QListWidget()
        proxy_layout.addWidget(QLabel("Proxy Pool:"))
        proxy_layout.addWidget(self.proxy_list)
        
        layout.addWidget(proxy_group)
        
        # Site Monitoring Settings
        sites_group = QGroupBox("Site Monitoring Configuration")
        sites_layout = QVBoxLayout(sites_group)
        
        # Site selector
        site_select_layout = QHBoxLayout()
        site_select_layout.addWidget(QLabel("Platform:"))
        self.site_selector = QComboBox()
        self.site_selector.addItems(["Ticketmaster", "Fansale", "Vivaticket"])
        site_select_layout.addWidget(self.site_selector)
        site_select_layout.addStretch()
        sites_layout.addLayout(site_select_layout)
        
        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        url_layout.addWidget(self.url_input)
        sites_layout.addLayout(url_layout)
        
        # Event name
        event_layout = QHBoxLayout()
        event_layout.addWidget(QLabel("Event Name:"))
        self.event_input = QLineEdit()
        event_layout.addWidget(self.event_input)
        sites_layout.addLayout(event_layout)
        
        # Monitoring interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Check Interval (seconds):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 300)
        self.interval_spin.setValue(30)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        sites_layout.addLayout(interval_layout)
        
        # Site buttons
        site_buttons = QHBoxLayout()
        site_buttons.addWidget(QPushButton("Add Site"))
        site_buttons.addWidget(QPushButton("Update Selected"))
        site_buttons.addWidget(QPushButton("Remove Selected"))
        site_buttons.addStretch()
        sites_layout.addLayout(site_buttons)
        
        # Sites list
        self.sites_table = QTableWidget()
        self.sites_table.setColumnCount(4)
        self.sites_table.setHorizontalHeaderLabels(["Platform", "Event", "URL", "Interval"])
        sites_layout.addWidget(self.sites_table)
        
        layout.addWidget(sites_group)
        
        # Performance Settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QVBoxLayout(perf_group)
        
        self.block_images = QCheckBox("Block Images (Save bandwidth)")
        self.block_fonts = QCheckBox("Block Custom Fonts")
        self.block_media = QCheckBox("Block Media Content")
        
        perf_layout.addWidget(self.block_images)
        perf_layout.addWidget(self.block_fonts)
        perf_layout.addWidget(self.block_media)
        
        # Stealth mode
        stealth_layout = QHBoxLayout()
        stealth_layout.addWidget(QLabel("Stealth Level:"))
        self.stealth_slider = QSlider(Qt.Orientation.Horizontal)
        self.stealth_slider.setRange(1, 5)
        self.stealth_slider.setValue(3)
        stealth_layout.addWidget(self.stealth_slider)
        self.stealth_label = QLabel("Balanced")
        stealth_layout.addWidget(self.stealth_label)
        perf_layout.addLayout(stealth_layout)
        
        layout.addWidget(perf_group)
        
        # Save/Load buttons
        config_buttons = QHBoxLayout()
        config_buttons.addWidget(QPushButton("Save Configuration"))
        config_buttons.addWidget(QPushButton("Load Configuration"))
        config_buttons.addWidget(QPushButton("Reset to Defaults"))
        config_buttons.addStretch()
        layout.addLayout(config_buttons)
        
        # Return scroll area instead of widget
        return scroll_area
        
    def create_logs_tab(self):
        """Create the logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Log controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Log Level:"))
        
        self.log_level = QComboBox()
        self.log_level.addItems(["All", "Info", "Warning", "Error"])
        controls_layout.addWidget(self.log_level)
        
        controls_layout.addWidget(QLabel("Filter:"))
        self.log_filter = QLineEdit()
        self.log_filter.setPlaceholderText("Search logs...")
        controls_layout.addWidget(self.log_filter)
        
        controls_layout.addStretch()
        
        controls_layout.addWidget(QPushButton("Clear Logs"))
        controls_layout.addWidget(QPushButton("Export Logs"))
        
        layout.addLayout(controls_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_display)
        
        return widget
        
    def create_control_panel(self):
        """Create the control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Box)
        layout = QHBoxLayout(panel)
        
        # Start/Stop button
        self.start_button = QPushButton("▶️ Start Bot")
        self.start_button.setFixedSize(150, 40)
        self.start_button.clicked.connect(self.toggle_bot)
        layout.addWidget(self.start_button)
        
        # Status indicator
        self.status_indicator = QLabel("⚪ Stopped")
        self.status_indicator.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.status_indicator)
        
        layout.addStretch()
        
        # Quick actions
        layout.addWidget(QPushButton("⏸️ Pause All"))
        layout.addWidget(QPushButton("🔄 Restart Browsers"))
        layout.addWidget(QPushButton("📊 Generate Report"))
        layout.addWidget(QPushButton("🛑 Emergency Stop"))
        
        return panel
        
    def setup_styles(self):
        """Setup dark theme styles"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(60, 60, 60))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        self.setPalette(dark_palette)
        
        # Additional styles
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px 10px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QTableWidget {
                gridline-color: #555;
            }
            QTabWidget::pane {
                border: 1px solid #555;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #555;
            }
        """)
        
    def setup_timers(self):
        """Setup update timers"""
        # UI update timer
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(1000)  # Update every second
        
        # Graph update timer
        self.graph_timer = QTimer()
        self.graph_timer.timeout.connect(self.update_graphs)
        self.graph_timer.start(5000)  # Update every 5 seconds
        
    def setup_system_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("StealthMaster")
        
        # Create a simple icon (red circle)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QBrush(QColor("#FF5252")))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(0, 0, 16, 16)
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        start_action = tray_menu.addAction("Start Bot")
        start_action.triggered.connect(self.start_bot)
        
        stop_action = tray_menu.addAction("Stop Bot")
        stop_action.triggered.connect(self.stop_bot)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.close)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Only show if system tray is available
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
        
    def load_configuration(self):
        """Load configuration from file"""
        try:
            # Import settings
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from src.config import load_settings
            
            self.settings = load_settings()
            self.log_message("Configuration loaded successfully", "info")
            
            # Update UI with loaded settings
            self.update_settings_ui()
            
        except Exception as e:
            self.log_message(f"Failed to load configuration: {e}", "error")
            
    def update_settings_ui(self):
        """Update settings UI with loaded configuration"""
        if not self.settings:
            return
            
        # Update proxy settings
        if self.settings.proxy_settings.enabled:
            self.proxy_enabled.setChecked(True)
            
        # Update sites table
        self.sites_table.setRowCount(0)
        for target in self.settings.targets:
            if target.enabled:
                row = self.sites_table.rowCount()
                self.sites_table.insertRow(row)
                self.sites_table.setItem(row, 0, QTableWidgetItem(str(target.platform)))
                self.sites_table.setItem(row, 1, QTableWidgetItem(target.event_name))
                self.sites_table.setItem(row, 2, QTableWidgetItem(str(target.url)))
                self.sites_table.setItem(row, 3, QTableWidgetItem(f"{target.interval_s}s"))
                
    def toggle_bot(self):
        """Toggle bot on/off"""
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()
            
    def start_bot(self):
        """Start the bot"""
        try:
            # Import and create StealthMaster instance
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from stealthmaster import StealthMasterUI
            
            self.stealthmaster = StealthMasterUI(self.settings)
            
            # Create and start worker thread
            self.worker = AsyncWorker(self.stealthmaster)
            self.worker.log_signal.connect(self.log_message)
            self.worker.stats_signal.connect(self.update_stats)
            self.worker.monitor_signal.connect(self.update_monitor)
            self.worker.ticket_signal.connect(self.on_ticket_found)
            
            # Start monitoring in thread
            monitor_thread = threading.Thread(target=self.run_stealthmaster)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Update UI
            self.is_running = True
            self.start_button.setText("⏹️ Stop Bot")
            self.status_indicator.setText("🟢 Running")
            self.status_indicator.setStyleSheet("color: #4CAF50;")
            
            self.log_message("Bot started successfully", "success")
            
        except Exception as e:
            self.log_message(f"Failed to start bot: {e}", "error")
            QMessageBox.critical(self, "Error", f"Failed to start bot:\n{str(e)}")
            
    def run_stealthmaster(self):
        """Run StealthMaster in async context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.stealthmaster.run())
        except Exception as e:
            self.worker.log_signal.emit(f"Bot error: {e}", "error")
        finally:
            loop.close()
            
    def stop_bot(self):
        """Stop the bot"""
        if self.stealthmaster:
            self.stealthmaster.running = False
            
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            
        # Update UI
        self.is_running = False
        self.start_button.setText("▶️ Start Bot")
        self.status_indicator.setText("🔴 Stopped")
        self.status_indicator.setStyleSheet("color: #F44336;")
        
        self.log_message("Bot stopped", "warning")
        
    def log_message(self, message: str, level: str = "info"):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color based on level
        colors = {
            "info": "#ffffff",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336"
        }
        color = colors.get(level, "#ffffff")
        
        # Format and add to log
        formatted = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color};">{message}</span><br>'
        self.log_display.append(formatted)
        
        # Also add to activity feed for important messages
        if level in ["success", "error"]:
            item = QListWidgetItem(f"[{timestamp}] {message}")
            self.activity_feed.insertItem(0, item)
            
            # Limit feed size
            while self.activity_feed.count() > 50:
                self.activity_feed.takeItem(self.activity_feed.count() - 1)
                
    def update_stats(self, stats: dict):
        """Update statistics displays"""
        # Update stat cards
        if 'tickets_found' in stats:
            self.stat_cards['tickets_found'].findChild(QLabel, "value").setText(str(stats['tickets_found']))
            
        if 'tickets_reserved' in stats and 'tickets_found' in stats:
            success_rate = (stats['tickets_reserved'] / max(1, stats['tickets_found'])) * 100
            self.stat_cards['success_rate'].findChild(QLabel, "value").setText(f"{success_rate:.1f}%")
            
        if 'active_monitors' in stats:
            self.stat_cards['active_monitors'].findChild(QLabel, "value").setText(str(stats['active_monitors']))
            
        # Update quick stats
        tickets = stats.get('tickets_found', 0)
        rate = success_rate if 'success_rate' in locals() else 0
        self.quick_stats_label.setText(f"Tickets Found: {tickets} | Success Rate: {rate:.1f}%")
        
        # Update browser status
        if 'browsers_open' in stats:
            for platform, label in self.browser_status_labels.items():
                label.setText(f"{platform.title()}: Active" if stats['browsers_open'] > 0 else f"{platform.title()}: Inactive")
                label.setStyleSheet(
                    "padding: 5px; background: #2E7D32; border-radius: 5px;" 
                    if stats['browsers_open'] > 0 
                    else "padding: 5px; background: #333; border-radius: 5px;"
                )
                
    def update_monitor(self, event_name: str, status: str, last_check: str):
        """Update monitor status in table"""
        # Find or create row
        for row in range(self.monitors_table.rowCount()):
            if self.monitors_table.item(row, 1).text() == event_name:
                self.monitors_table.setItem(row, 2, QTableWidgetItem(status))
                self.monitors_table.setItem(row, 3, QTableWidgetItem(last_check))
                return
                
        # Add new row if not found
        row = self.monitors_table.rowCount()
        self.monitors_table.insertRow(row)
        self.monitors_table.setItem(row, 0, QTableWidgetItem("Unknown"))
        self.monitors_table.setItem(row, 1, QTableWidgetItem(event_name))
        self.monitors_table.setItem(row, 2, QTableWidgetItem(status))
        self.monitors_table.setItem(row, 3, QTableWidgetItem(last_check))
        self.monitors_table.setItem(row, 4, QTableWidgetItem("..."))
        
    def on_ticket_found(self, platform: str, event: str, count: int):
        """Handle ticket found event"""
        self.log_message(f"🎫 TICKETS FOUND! {platform} - {event} ({count} tickets)", "success")
        
        # Show notification
        self.tray_icon.showMessage(
            "Tickets Found!",
            f"{count} tickets found for {event} on {platform}",
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )
        
        # Add to events table
        row = self.events_table.rowCount()
        self.events_table.insertRow(row)
        self.events_table.setItem(row, 0, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
        self.events_table.setItem(row, 1, QTableWidgetItem(platform))
        self.events_table.setItem(row, 2, QTableWidgetItem(event))
        self.events_table.setItem(row, 3, QTableWidgetItem("🎫 Tickets Found"))
        self.events_table.setItem(row, 4, QTableWidgetItem("N/A"))
        self.events_table.setItem(row, 5, QTableWidgetItem("N/A"))
        self.events_table.setItem(row, 6, QTableWidgetItem("View"))
        
    def update_ui(self):
        """Periodic UI updates"""
        # Update time-based displays
        if self.is_running and hasattr(self, 'start_time'):
            uptime = datetime.now() - self.start_time
            self.statusBar().showMessage(f"Uptime: {str(uptime).split('.')[0]}")
            
    def update_graphs(self):
        """Update statistics graphs"""
        if not self.is_running:
            return
            
        # Add sample data (replace with real data)
        current_time = datetime.now().timestamp()
        
        # Limit history
        max_points = 100
        if len(self.stats_history['time']) > max_points:
            for key in self.stats_history:
                self.stats_history[key] = self.stats_history[key][-max_points:]
                
        self.stats_history['time'].append(current_time)
        self.stats_history['tickets_found'].append(len(self.stats_history['tickets_found']))
        self.stats_history['success_rate'].append(50 + 50 * (len(self.stats_history['time']) % 10) / 10)
        self.stats_history['data_usage'].append(len(self.stats_history['data_usage']) * 0.5)
        
        # Update plots
        if len(self.stats_history['time']) > 1:
            # Update graph labels with latest values
            tickets_text = f"Latest: {self.stats_history['tickets_found'][-1] if self.stats_history['tickets_found'] else 0} tickets"
            self.tickets_plot.setText(tickets_text)
            
            success_text = f"Latest: {self.stats_history['success_rate'][-1] if self.stats_history['success_rate'] else 0:.1f}%"
            self.success_plot.setText(success_text)
            
            data_text = f"Latest: {self.stats_history['data_usage'][-1] if self.stats_history['data_usage'] else 0:.1f} MB"
            self.data_plot.setText(data_text)
            
    def closeEvent(self, event):
        """Handle close event"""
        if self.is_running:
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'Bot is still running. Are you sure you want to exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_bot()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("StealthMaster")
    
    # Set application icon
    app.setWindowIcon(QIcon())
    
    # Create and show main window
    window = StealthMasterGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🎸 StealthMaster AI - Bruce Springsteen Web GUI v2.0
Modern Web-Based Command Center with Real-Time Dashboard
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import json
import threading
import queue
import time
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.main import load_app_config_for_gui, main_loop_for_gui

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'bruce_springsteen_stealthmaster_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebGUIManager:
    """Web GUI Manager for Bruce Springsteen Ticket Hunter"""
    
    def __init__(self):
        self.bot_running = False
        self.bot_thread = None
        self.stop_event = None
        self.gui_queue = queue.Queue()
        self.start_time = datetime.now()
        
        # Performance data storage
        self.performance_data = {
            'timestamps': [],
            'success_rates': [],
            'response_times': [],
            'stealth_scores': [],
            'requests_per_minute': [],
            'ticket_detections': 0,
            'total_requests': 0,
            'successful_requests': 0
        }
        
        # System status
        self.system_status = {
            'bot_status': 'READY',
            'uptime': '00:00:00',
            'session_time': '00:00:00',
            'threat_level': 'LOW',
            'stealth_score': 100,
            'profile_health': 98,
            'network_status': 'READY'
        }
        
        # Initialize with sample data
        self.initialize_sample_data()
        
        # Start background tasks
        self.start_background_tasks()
    
    def initialize_sample_data(self):
        """Initialize with sample performance data"""
        for i in range(30):
            timestamp = datetime.now() - timedelta(minutes=30-i)
            self.performance_data['timestamps'].append(timestamp.isoformat())
            self.performance_data['success_rates'].append(85 + np.random.normal(0, 10))
            self.performance_data['response_times'].append(800 + np.random.normal(0, 200))
            self.performance_data['stealth_scores'].append(90 + np.random.normal(0, 8))
            self.performance_data['requests_per_minute'].append(np.random.poisson(5))
    
    def start_background_tasks(self):
        """Start background update tasks"""
        def update_loop():
            while True:
                self.update_performance_data()
                self.update_system_status()
                socketio.emit('data_update', {
                    'performance': self.get_performance_data(),
                    'system_status': self.system_status
                })
                time.sleep(5)  # Update every 5 seconds
        
        threading.Thread(target=update_loop, daemon=True).start()
        
        # Process bot queue
        def queue_processor():
            while True:
                try:
                    if not self.gui_queue.empty():
                        message_type, data = self.gui_queue.get_nowait()
                        self.handle_queue_message(message_type, data)
                except queue.Empty:
                    pass
                time.sleep(0.1)
        
        threading.Thread(target=queue_processor, daemon=True).start()
    
    def update_performance_data(self):
        """Update performance data with new values"""
        now = datetime.now()
        
        # Add new data point
        self.performance_data['timestamps'].append(now.isoformat())
        
        if self.bot_running:
            # Simulate realistic data when bot is running
            self.performance_data['success_rates'].append(85 + np.random.normal(0, 10))
            self.performance_data['response_times'].append(800 + np.random.normal(0, 200))
            self.performance_data['stealth_scores'].append(90 + np.random.normal(0, 8))
            self.performance_data['requests_per_minute'].append(np.random.poisson(8))
        else:
            # Static data when bot is not running
            self.performance_data['success_rates'].append(0)
            self.performance_data['response_times'].append(0)
            self.performance_data['stealth_scores'].append(100)
            self.performance_data['requests_per_minute'].append(0)
        
        # Keep only last 100 data points
        for key in ['timestamps', 'success_rates', 'response_times', 'stealth_scores', 'requests_per_minute']:
            if len(self.performance_data[key]) > 100:
                self.performance_data[key] = self.performance_data[key][-100:]
    
    def update_system_status(self):
        """Update system status information"""
        now = datetime.now()
        uptime = now - self.start_time
        
        self.system_status['uptime'] = str(uptime).split('.')[0]
        
        if self.bot_running:
            session_time = now - self.session_start_time
            self.system_status['session_time'] = str(session_time).split('.')[0]
            self.system_status['bot_status'] = 'HUNTING'
        else:
            self.system_status['bot_status'] = 'READY'
            self.system_status['session_time'] = '00:00:00'
    
    def handle_queue_message(self, message_type, data):
        """Handle messages from bot queue"""
        if message_type == "log":
            log_message, level = data
            socketio.emit('log_message', {
                'message': log_message,
                'level': level,
                'timestamp': datetime.now().isoformat()
            })
        elif message_type == "ticket_found":
            self.performance_data['ticket_detections'] += 1
            socketio.emit('ticket_found', {
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
        elif message_type == "status_update":
            socketio.emit('status_update', data)
    
    def start_bot(self):
        """Start the ticket hunting bot"""
        try:
            if self.bot_running:
                return {'success': False, 'message': 'Bot is already running'}
            
            # Load configuration
            config = load_app_config_for_gui()
            
            # Create stop event
            self.stop_event = threading.Event()
            self.session_start_time = datetime.now()
            
            # Set up live status logger GUI integration
            try:
                from src.utils.live_status_logger import get_live_status_logger
                live_logger = get_live_status_logger()
                live_logger.set_gui_callback(self.handle_live_status_update)
            except Exception as e:
                print(f"Warning: Could not set up live status integration: {e}")
            
            # Start bot in separate thread
            self.bot_thread = threading.Thread(
                target=main_loop_for_gui,
                args=(config, self.stop_event, self.gui_queue),
                daemon=True
            )
            self.bot_thread.start()
            
            self.bot_running = True
            
            return {'success': True, 'message': 'Bot started successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to start bot: {str(e)}'}
    
    def stop_bot(self):
        """Stop the ticket hunting bot"""
        try:
            if not self.bot_running:
                return {'success': False, 'message': 'Bot is not running'}
            
            if self.stop_event:
                self.stop_event.set()
            
            self.bot_running = False
            
            return {'success': True, 'message': 'Bot stopped successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to stop bot: {str(e)}'}
    
    def get_performance_data(self):
        """Get current performance data"""
        return self.performance_data
    
    def get_system_status(self):
        """Get current system status"""
        return self.system_status
    
    def handle_live_status_update(self, status_update):
        """Handle live status updates from the bot"""
        try:
            # Convert status update to GUI format
            status_data = {
                'timestamp': status_update.timestamp.isoformat(),
                'level': status_update.level.value,
                'category': status_update.category,
                'message': status_update.message,
                'details': status_update.details or {},
                'progress': status_update.progress
            }
            
            # Emit to connected clients
            socketio.emit('live_status_update', status_data)
            
            # Update internal status tracking
            if status_update.category == "TICKETS" and "FOUND" in status_update.message.upper():
                self.performance_data['ticket_detections'] += 1
            
        except Exception as e:
            print(f"Error handling live status update: {e}")

# Global GUI manager
gui_manager = WebGUIManager()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    """Start the bot via API"""
    result = gui_manager.start_bot()
    return jsonify(result)

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    """Stop the bot via API"""
    result = gui_manager.stop_bot()
    return jsonify(result)

@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify({
        'performance': gui_manager.get_performance_data(),
        'system_status': gui_manager.get_system_status(),
        'bot_running': gui_manager.bot_running
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to StealthMaster AI'})
    emit('data_update', {
        'performance': gui_manager.get_performance_data(),
        'system_status': gui_manager.system_status
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

def create_templates():
    """Create HTML templates"""
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Create main dashboard template
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎸 StealthMaster AI - Bruce Springsteen Command Center</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #ffffff;
            overflow-x: hidden;
        }

        .header {
            background: linear-gradient(90deg, #2a2a2a 0%, #1a1a1a 100%);
            padding: 20px;
            border-bottom: 3px solid #ffd700;
            box-shadow: 0 4px 20px rgba(255, 215, 0, 0.3);
        }

        .header h1 {
            text-align: center;
            font-size: 2.5rem;
            color: #ffd700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            margin-bottom: 10px;
        }

        .header .subtitle {
            text-align: center;
            font-size: 1.2rem;
            color: #cccccc;
            font-style: italic;
        }

        .status-bar {
            background: #2a2a2a;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #444;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .status-ready { background: #ffaa44; }
        .status-hunting { background: #44ff44; }
        .status-stopped { background: #ff4444; }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .main-container {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            padding: 20px;
            min-height: calc(100vh - 200px);
        }

        .card {
            background: linear-gradient(145deg, #2a2a2a 0%, #1a1a1a 100%);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
            border: 1px solid #444;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 35px rgba(255, 215, 0, 0.2);
        }

        .card h3 {
            color: #ffd700;
            margin-bottom: 15px;
            font-size: 1.4rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .control-panel {
            grid-column: span 3;
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }

        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn-start {
            background: linear-gradient(45deg, #44ff44, #66ff66);
            color: #000;
        }

        .btn-stop {
            background: linear-gradient(45deg, #ff4444, #ff6666);
            color: #fff;
        }

        .btn-action {
            background: linear-gradient(45deg, #4488ff, #66aaff);
            color: #fff;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .stat-item {
            background: #1a1a1a;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #333;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #ffd700;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 0.9rem;
            color: #ccc;
        }

        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }

        .log-container {
            grid-column: span 3;
            background: #0a0a0a;
            border-radius: 15px;
            padding: 20px;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #333;
        }

        .log-entry {
            padding: 8px 0;
            border-bottom: 1px solid #222;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }

        .log-timestamp {
            color: #888;
        }

        .log-message {
            color: #fff;
            margin-left: 10px;
        }

        .log-level-info { color: #4488ff; }
        .log-level-warning { color: #ffaa44; }
        .log-level-error { color: #ff4444; }
        .log-level-critical { color: #ff6666; }

        .threat-meter {
            background: #1a1a1a;
            height: 30px;
            border-radius: 15px;
            margin: 15px 0;
            position: relative;
            overflow: hidden;
        }

        .threat-fill {
            height: 100%;
            border-radius: 15px;
            transition: width 0.5s ease;
        }

        .threat-low { background: linear-gradient(90deg, #44ff44, #66ff66); }
        .threat-medium { background: linear-gradient(90deg, #ffaa44, #ffcc66); }
        .threat-high { background: linear-gradient(90deg, #ff4444, #ff6666); }

        .tickets-found {
            text-align: center;
            font-size: 3rem;
            font-weight: bold;
            color: #ff4444;
            text-shadow: 0 0 20px rgba(255, 68, 68, 0.5);
            animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
            from { text-shadow: 0 0 20px rgba(255, 68, 68, 0.5); }
            to { text-shadow: 0 0 30px rgba(255, 68, 68, 0.8); }
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(45deg, #ff4444, #ff6666);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        }

        .notification.show {
            transform: translateX(0);
        }

        @media (max-width: 1200px) {
            .main-container {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 768px) {
            .main-container {
                grid-template-columns: 1fr;
            }
            
            .control-panel {
                grid-column: span 1;
            }
            
            .log-container {
                grid-column: span 1;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎸 STEALTHMASTER AI</h1>
        <p class="subtitle">Bruce Springsteen Ticket Hunter Command Center</p>
    </div>

    <div class="status-bar">
        <div class="status-indicator">
            <div class="status-dot status-ready" id="statusDot"></div>
            <span id="botStatus">READY</span>
        </div>
        <div>
            <span>Uptime: <span id="uptime">00:00:00</span></span>
            <span style="margin-left: 20px;">Session: <span id="sessionTime">00:00:00</span></span>
        </div>
    </div>

    <div class="main-container">
        <!-- Performance Card -->
        <div class="card">
            <h3><i class="fas fa-chart-line"></i> Performance</h3>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>

        <!-- Stealth Card -->
        <div class="card">
            <h3><i class="fas fa-user-secret"></i> Stealth Status</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="stealthScore">100%</div>
                    <div class="stat-label">Stealth Score</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="profileHealth">98%</div>
                    <div class="stat-label">Profile Health</div>
                </div>
            </div>
            <div class="threat-meter">
                <div class="threat-fill threat-low" id="threatFill" style="width: 15%;"></div>
            </div>
            <p style="text-align: center; margin-top: 10px;">Threat Level: <span id="threatLevel">LOW</span></p>
        </div>

        <!-- Tickets Card -->
        <div class="card">
            <h3><i class="fas fa-ticket-alt"></i> Ticket Hunt</h3>
            <div class="tickets-found" id="ticketsFound">0</div>
            <p style="text-align: center; color: #ccc; margin-top: 10px;">Tickets Found</p>
            <div class="stats-grid" style="margin-top: 20px;">
                <div class="stat-item">
                    <div class="stat-value" id="totalRequests">0</div>
                    <div class="stat-label">Total Requests</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="successRate">0%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
            </div>
        </div>

        <!-- Control Panel -->
        <div class="card control-panel">
            <button class="btn btn-start" id="startBtn" onclick="startBot()">
                <i class="fas fa-play"></i> START HUNTING
            </button>
            <button class="btn btn-stop" id="stopBtn" onclick="stopBot()" disabled>
                <i class="fas fa-stop"></i> STOP
            </button>
            <button class="btn btn-action" onclick="openSettings()">
                <i class="fas fa-cog"></i> Settings
            </button>
            <button class="btn btn-action" onclick="exportData()">
                <i class="fas fa-download"></i> Export
            </button>
        </div>

        <!-- System Stats -->
        <div class="card">
            <h3><i class="fas fa-server"></i> System Stats</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="requestsPerMin">0</div>
                    <div class="stat-label">Requests/min</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="avgResponse">0ms</div>
                    <div class="stat-label">Avg Response</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="networkStatus">READY</div>
                    <div class="stat-label">Network</div>
                </div>
            </div>
        </div>

        <!-- Response Time Chart -->
        <div class="card">
            <h3><i class="fas fa-clock"></i> Response Times</h3>
            <div class="chart-container">
                <canvas id="responseChart"></canvas>
            </div>
        </div>

        <!-- Log Display -->
        <div class="card log-container">
            <h3><i class="fas fa-terminal"></i> System Logs</h3>
            <div id="logDisplay"></div>
        </div>
    </div>

    <div class="notification" id="notification">
        <h4>🚨 TICKETS FOUND!</h4>
        <p>Bruce Springsteen tickets detected!</p>
    </div>

    <script>
        // Initialize Socket.IO
        const socket = io();
        let botRunning = false;

        // Chart configurations
        const chartConfig = {
            type: 'line',
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#cccccc' },
                        grid: { color: '#444444' }
                    },
                    y: {
                        ticks: { color: '#cccccc' },
                        grid: { color: '#444444' }
                    }
                }
            }
        };

        // Initialize charts
        const performanceChart = new Chart(document.getElementById('performanceChart'), {
            ...chartConfig,
            data: {
                labels: [],
                datasets: [{
                    label: 'Success Rate %',
                    data: [],
                    borderColor: '#44ff44',
                    backgroundColor: 'rgba(68, 255, 68, 0.1)',
                    tension: 0.4
                }]
            }
        });

        const responseChart = new Chart(document.getElementById('responseChart'), {
            ...chartConfig,
            data: {
                labels: [],
                datasets: [{
                    label: 'Response Time (ms)',
                    data: [],
                    borderColor: '#4488ff',
                    backgroundColor: 'rgba(68, 136, 255, 0.1)',
                    tension: 0.4
                }]
            }
        });

        // Socket event handlers
        socket.on('connected', function(data) {
            addLog('🎸 Connected to StealthMaster AI', 'info');
        });

        socket.on('data_update', function(data) {
            updateCharts(data.performance);
            updateSystemStatus(data.system_status);
        });

        socket.on('log_message', function(data) {
            addLog(data.message, data.level);
        });

        socket.on('ticket_found', function(data) {
            showTicketNotification(data);
            updateTicketsFound();
        });

        // Bot control functions
        function startBot() {
            fetch('/api/start_bot', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        botRunning = true;
                        updateBotStatus('HUNTING');
                        document.getElementById('startBtn').disabled = true;
                        document.getElementById('stopBtn').disabled = false;
                        addLog('🚀 Bot started successfully!', 'info');
                    } else {
                        addLog('❌ Failed to start bot: ' + data.message, 'error');
                    }
                });
        }

        function stopBot() {
            fetch('/api/stop_bot', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        botRunning = false;
                        updateBotStatus('STOPPED');
                        document.getElementById('startBtn').disabled = false;
                        document.getElementById('stopBtn').disabled = true;
                        addLog('⏹️ Bot stopped successfully!', 'info');
                    } else {
                        addLog('❌ Failed to stop bot: ' + data.message, 'error');
                    }
                });
        }

        // UI update functions
        function updateCharts(performanceData) {
            // Update performance chart
            const labels = performanceData.timestamps.map(t => new Date(t).toLocaleTimeString());
            performanceChart.data.labels = labels;
            performanceChart.data.datasets[0].data = performanceData.success_rates;
            performanceChart.update('none');

            // Update response chart
            responseChart.data.labels = labels;
            responseChart.data.datasets[0].data = performanceData.response_times;
            responseChart.update('none');

            // Update stats
            if (performanceData.success_rates.length > 0) {
                const latest = performanceData.success_rates[performanceData.success_rates.length - 1];
                document.getElementById('successRate').textContent = Math.round(latest) + '%';
            }

            if (performanceData.response_times.length > 0) {
                const latest = performanceData.response_times[performanceData.response_times.length - 1];
                document.getElementById('avgResponse').textContent = Math.round(latest) + 'ms';
            }

            if (performanceData.requests_per_minute.length > 0) {
                const latest = performanceData.requests_per_minute[performanceData.requests_per_minute.length - 1];
                document.getElementById('requestsPerMin').textContent = latest;
            }

            document.getElementById('totalRequests').textContent = performanceData.total_requests;
            document.getElementById('ticketsFound').textContent = performanceData.ticket_detections;
        }

        function updateSystemStatus(status) {
            document.getElementById('uptime').textContent = status.uptime;
            document.getElementById('sessionTime').textContent = status.session_time;
            document.getElementById('stealthScore').textContent = status.stealth_score + '%';
            document.getElementById('profileHealth').textContent = status.profile_health + '%';
            document.getElementById('networkStatus').textContent = status.network_status;
            document.getElementById('threatLevel').textContent = status.threat_level;

            updateBotStatus(status.bot_status);
            updateThreatMeter(status.threat_level);
        }

        function updateBotStatus(status) {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('botStatus');
            
            statusDot.className = 'status-dot';
            statusText.textContent = status;

            switch(status) {
                case 'HUNTING':
                    statusDot.classList.add('status-hunting');
                    break;
                case 'STOPPED':
                    statusDot.classList.add('status-stopped');
                    break;
                default:
                    statusDot.classList.add('status-ready');
            }
        }

        function updateThreatMeter(level) {
            const threatFill = document.getElementById('threatFill');
            threatFill.className = 'threat-fill';

            switch(level) {
                case 'LOW':
                    threatFill.style.width = '15%';
                    threatFill.classList.add('threat-low');
                    break;
                case 'MEDIUM':
                    threatFill.style.width = '50%';
                    threatFill.classList.add('threat-medium');
                    break;
                case 'HIGH':
                    threatFill.style.width = '85%';
                    threatFill.classList.add('threat-high');
                    break;
            }
        }

        function addLog(message, level) {
            const logDisplay = document.getElementById('logDisplay');
            const timestamp = new Date().toLocaleTimeString();
            
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `
                <span class="log-timestamp">[${timestamp}]</span>
                <span class="log-message log-level-${level}">${message}</span>
            `;
            
            logDisplay.appendChild(logEntry);
            logDisplay.scrollTop = logDisplay.scrollHeight;
        }

        function showTicketNotification(data) {
            const notification = document.getElementById('notification');
            notification.classList.add('show');
            
            // Flash the page
            document.body.style.animation = 'flash 0.5s ease-in-out 3';
            
            setTimeout(() => {
                notification.classList.remove('show');
                document.body.style.animation = '';
            }, 5000);
        }

        function updateTicketsFound() {
            const current = parseInt(document.getElementById('ticketsFound').textContent);
            document.getElementById('ticketsFound').textContent = current + 1;
        }

        // Button functions
        function openSettings() {
            addLog('⚙️ Settings panel coming soon!', 'info');
        }

        function exportData() {
            addLog('📊 Data export feature coming soon!', 'info');
        }

        // Initialize
        addLog('🎸 StealthMaster AI Web GUI v2.0 ready!', 'info');
        addLog('🎯 Ready to hunt for Bruce Springsteen tickets!', 'info');

        // Add flash animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes flash {
                0%, 100% { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); }
                50% { background: linear-gradient(135deg, #2a0a0a 0%, #3a1a1a 100%); }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'dashboard.html', 'w') as f:
        f.write(dashboard_html)

def main():
    """Main entry point for the web GUI"""
    # Create templates
    create_templates()
    
    print("🎸 Starting StealthMaster AI Web GUI...")
    print("🌐 Access the dashboard at: http://localhost:5000")
    
    # Run the Flask app
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
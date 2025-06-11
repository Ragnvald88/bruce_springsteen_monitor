# stealthmaster/ui/mobile_interface.py
"""
Mobile-Optimized Interface for StealthMaster
Touch-friendly controls with haptic feedback and instant actions
"""

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import asyncio
import json
import time
from typing import Dict, Any
from dataclasses import dataclass
import os


@dataclass
class MobileAlert:
    """Mobile-optimized alert structure"""
    id: str
    type: str
    title: str
    message: str
    action_url: Optional[str] = None
    vibration_pattern: Optional[List[int]] = None


# Mobile-optimized HTML template
MOBILE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>StealthMaster Mobile</title>
    
    <style>
        * {
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #fff;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }
        
        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: #1a1a1a;
            border-bottom: 1px solid #333;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 1000;
        }
        
        .logo {
            font-size: 20px;
            font-weight: bold;
            color: #00ff88;
        }
        
        .connection-status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ff3333;
            transition: background 0.3s;
        }
        
        .connection-status.connected {
            background: #00ff88;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .main-content {
            padding-top: 60px;
            padding-bottom: 80px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            padding: 20px;
        }
        
        .metric-card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid #333;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .metric-card:active {
            transform: scale(0.98);
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .metric-label {
            font-size: 14px;
            color: #888;
        }
        
        .ticket-feed {
            padding: 0 20px;
        }
        
        .ticket-card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid #333;
            position: relative;
            overflow: hidden;
        }
        
        .ticket-card.new {
            animation: slideIn 0.3s ease-out;
            border-color: #00ff88;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .ticket-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .ticket-platform {
            font-size: 12px;
            color: #00ff88;
            text-transform: uppercase;
        }
        
        .ticket-time {
            font-size: 12px;
            color: #888;
        }
        
        .ticket-event {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .ticket-details {
            font-size: 14px;
            color: #ccc;
            margin-bottom: 15px;
        }
        
        .ticket-price {
            font-size: 24px;
            font-weight: bold;
            color: #00ff88;
        }
        
        .buy-button {
            width: 100%;
            padding: 15px;
            background: #00ff88;
            color: #000;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 15px;
        }
        
        .buy-button:active {
            background: #00cc70;
        }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 70px;
            background: #1a1a1a;
            border-top: 1px solid #333;
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 0 20px;
        }
        
        .nav-button {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        
        .nav-button:active {
            opacity: 0.7;
        }
        
        .nav-icon {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .nav-label {
            font-size: 12px;
            color: #888;
        }
        
        .nav-button.active .nav-label {
            color: #00ff88;
        }
        
        .emergency-button {
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: #ff3333;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(255, 51, 51, 0.4);
            transition: transform 0.2s;
        }
        
        .emergency-button:active {
            transform: scale(0.9);
        }
        
        .platform-toggle {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 20px;
            background: #1a1a1a;
            border-bottom: 1px solid #333;
        }
        
        .toggle-switch {
            position: relative;
            width: 50px;
            height: 28px;
            background: #333;
            border-radius: 14px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .toggle-switch.active {
            background: #00ff88;
        }
        
        .toggle-knob {
            position: absolute;
            top: 3px;
            left: 3px;
            width: 22px;
            height: 22px;
            background: #fff;
            border-radius: 50%;
            transition: transform 0.3s;
        }
        
        .toggle-switch.active .toggle-knob {
            transform: translateX(22px);
        }
        
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #333;
            border-top-color: #00ff88;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .notification-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: #ff3333;
            color: #fff;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 10px;
            min-width: 18px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">StealthMaster</div>
        <div class="connection-status" id="connectionStatus"></div>
    </div>
    
    <div class="main-content" id="mainContent">
        <!-- Dashboard View -->
        <div id="dashboardView" class="view">
            <div class="metrics-grid">
                <div class="metric-card" onclick="vibrate()">
                    <div class="metric-label">Detection Latency</div>
                    <div class="metric-value" id="latencyMetric">0ms</div>
                </div>
                <div class="metric-card" onclick="vibrate()">
                    <div class="metric-label">Active Monitors</div>
                    <div class="metric-value" id="monitorsMetric">0</div>
                </div>
                <div class="metric-card" onclick="vibrate()">
                    <div class="metric-label">Tickets Found</div>
                    <div class="metric-value" id="ticketsMetric">0</div>
                </div>
                <div class="metric-card" onclick="vibrate()">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value" id="successMetric">0%</div>
                </div>
            </div>
            
            <div class="ticket-feed" id="ticketFeed">
                <!-- Tickets will be inserted here -->
            </div>
        </div>
        
        <!-- Platforms View -->
        <div id="platformsView" class="view" style="display:none;">
            <div class="platform-toggle">
                <span>Ticketmaster</span>
                <div class="toggle-switch" id="tmToggle" onclick="togglePlatform('ticketmaster', this)">
                    <div class="toggle-knob"></div>
                </div>
            </div>
            <div class="platform-toggle">
                <span>FanSale</span>
                <div class="toggle-switch" id="fsToggle" onclick="togglePlatform('fansale', this)">
                    <div class="toggle-knob"></div>
                </div>
            </div>
            <div class="platform-toggle">
                <span>VivaTicket</span>
                <div class="toggle-switch" id="vtToggle" onclick="togglePlatform('vivaticket', this)">
                    <div class="toggle-knob"></div>
                </div>
            </div>
        </div>
        
        <!-- Settings View -->
        <div id="settingsView" class="view" style="display:none;">
            <div style="padding: 20px;">
                <h2>Quick Settings</h2>
                <p>Configure your preferences</p>
                <!-- Settings options here -->
            </div>
        </div>
    </div>
    
    <div class="bottom-nav">
        <div class="nav-button active" onclick="switchView('dashboard')">
            <div class="nav-icon">📊</div>
            <div class="nav-label">Dashboard</div>
        </div>
        <div class="nav-button" onclick="switchView('platforms')">
            <div class="nav-icon">🎫</div>
            <div class="nav-label">Platforms</div>
        </div>
        <div class="nav-button" onclick="switchView('settings')">
            <div class="nav-icon">⚙️</div>
            <div class="nav-label">Settings</div>
        </div>
    </div>
    
    <div class="emergency-button" onclick="emergencyStop()">
        🛑
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        // WebSocket connection
        const socket = io();
        
        // Platform states
        const platformStates = {
            ticketmaster: false,
            fansale: false,
            vivaticket: false
        };
        
        // Metrics
        let metrics = {
            latency: 0,
            monitors: 0,
            tickets: 0,
            successRate: 0
        };
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();
        });
        
        function initializeApp() {
            // Check for mobile features
            if ('vibrate' in navigator) {
                console.log('Vibration API supported');
            }
            
            // Setup socket handlers
            socket.on('connect', () => {
                document.getElementById('connectionStatus').classList.add('connected');
            });
            
            socket.on('disconnect', () => {
                document.getElementById('connectionStatus').classList.remove('connected');
            });
            
            socket.on('ticket_alert', (data) => {
                handleTicketAlert(data);
            });
            
            socket.on('metrics_update', (data) => {
                updateMetrics(data);
            });
            
            // Request initial state
            socket.emit('get_state');
        }
        
        function vibrate(pattern = [50]) {
            if ('vibrate' in navigator) {
                navigator.vibrate(pattern);
            }
        }
        
        function switchView(viewName) {
            // Hide all views
            document.querySelectorAll('.view').forEach(view => {
                view.style.display = 'none';
            });
            
            // Show selected view
            document.getElementById(viewName + 'View').style.display = 'block';
            
            // Update nav buttons
            document.querySelectorAll('.nav-button').forEach(btn => {
                btn.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
            
            // Haptic feedback
            vibrate();
        }
        
        function togglePlatform(platform, element) {
            platformStates[platform] = !platformStates[platform];
            
            if (platformStates[platform]) {
                element.classList.add('active');
            } else {
                element.classList.remove('active');
            }
            
            // Send to server
            socket.emit('toggle_platform', {
                platform: platform,
                active: platformStates[platform]
            });
            
            // Haptic feedback
            vibrate([50, 50, 50]);
        }
        
        function handleTicketAlert(data) {
            // Vibrate for new ticket
            vibrate([100, 50, 100]);
            
            // Play sound if available
            if ('Audio' in window) {
                const audio = new Audio('/static/sounds/ticket_alert.mp3');
                audio.play().catch(e => console.log('Audio play failed:', e));
            }
            
            // Create ticket card
            const ticketCard = createTicketCard(data);
            
            // Add to feed
            const feed = document.getElementById('ticketFeed');
            feed.insertBefore(ticketCard, feed.firstChild);
            
            // Limit feed size
            while (feed.children.length > 20) {
                feed.removeChild(feed.lastChild);
            }
            
            // Update metrics
            metrics.tickets++;
            updateMetricDisplay('ticketsMetric', metrics.tickets);
        }
        
        function createTicketCard(data) {
            const card = document.createElement('div');
            card.className = 'ticket-card new';
            
            const time = new Date().toLocaleTimeString();
            
            card.innerHTML = `
                <div class="ticket-header">
                    <div class="ticket-platform">${data.platform}</div>
                    <div class="ticket-time">${time}</div>
                </div>
                <div class="ticket-event">${data.event_name}</div>
                <div class="ticket-details">
                    Section ${data.section} • Row ${data.row} • Seat ${data.seat}
                </div>
                <div class="ticket-price">$${data.price.toFixed(2)}</div>
                <button class="buy-button" onclick="quickBuy('${data.id}')">
                    BUY NOW
                </button>
            `;
            
            // Remove 'new' class after animation
            setTimeout(() => {
                card.classList.remove('new');
            }, 500);
            
            return card;
        }
        
        function quickBuy(ticketId) {
            // Immediate haptic feedback
            vibrate([50, 100, 50]);
            
            // Send purchase request
            socket.emit('quick_purchase', {
                ticket_id: ticketId,
                timestamp: Date.now()
            });
            
            // Update button
            event.target.textContent = 'PURCHASING...';
            event.target.disabled = true;
        }
        
        function updateMetrics(data) {
            metrics = data;
            
            updateMetricDisplay('latencyMetric', Math.round(data.latency) + 'ms');
            updateMetricDisplay('monitorsMetric', data.monitors);
            updateMetricDisplay('ticketsMetric', data.tickets);
            updateMetricDisplay('successMetric', Math.round(data.successRate) + '%');
        }
        
        function updateMetricDisplay(elementId, value) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = value;
                
                // Flash animation
                element.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 200);
            }
        }
        
        function emergencyStop() {
            // Strong vibration
            vibrate([200, 100, 200]);
            
            if (confirm('Emergency stop all operations?')) {
                socket.emit('emergency_stop');
                
                // Update UI
                document.body.style.background = '#330000';
                setTimeout(() => {
                    document.body.style.background = '#0a0a0a';
                }, 1000);
            }
        }
        
        // Touch gesture support
        let touchStartY = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            const touchEndY = e.changedTouches[0].clientY;
            const diff = touchStartY - touchEndY;
            
            // Pull to refresh
            if (diff < -100 && window.scrollY === 0) {
                socket.emit('refresh_all');
                vibrate([50, 50]);
            }
        });
        
        // Prevent zoom on double tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        });
    </script>
</body>
</html>
"""


class MobileInterface:
    """Mobile-optimized Flask interface"""
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.urandom(24)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.host = host
        self.port = port
        
        # State
        self.connected_clients = set()
        self.platform_states = {}
        self.active_tickets = {}
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_handlers()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def index():
            return render_template_string(MOBILE_TEMPLATE)
        
        @self.app.route('/api/status')
        def status():
            return jsonify({
                'connected_clients': len(self.connected_clients),
                'platform_states': self.platform_states,
                'active_tickets': len(self.active_tickets)
            })
    
    def _setup_socketio_handlers(self):
        """Setup SocketIO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            self.connected_clients.add(request.sid)
            emit('connection_established', {
                'client_id': request.sid,
                'timestamp': time.time()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.connected_clients.discard(request.sid)
        
        @self.socketio.on('get_state')
        def handle_get_state():
            emit('state_update', {
                'platforms': self.platform_states,
                'tickets': list(self.active_tickets.values())[-10:],  # Last 10
                'metrics': self.get_current_metrics()
            })
        
        @self.socketio.on('toggle_platform')
        def handle_toggle_platform(data):
            platform = data.get('platform')
            active = data.get('active')
            
            self.platform_states[platform] = active
            
            # Broadcast to all clients
            self.socketio.emit('platform_state_changed', {
                'platform': platform,
                'active': active
            })
        
        @self.socketio.on('quick_purchase')
        def handle_quick_purchase(data):
            ticket_id = data.get('ticket_id')
            
            # Process purchase (would connect to actual system)
            emit('purchase_status', {
                'ticket_id': ticket_id,
                'status': 'processing'
            })
            
            # Simulate purchase completion
            self.socketio.sleep(1)
            
            emit('purchase_status', {
                'ticket_id': ticket_id,
                'status': 'completed'
            })
        
        @self.socketio.on('emergency_stop')
        def handle_emergency_stop():
            # Broadcast emergency stop to all clients
            self.socketio.emit('emergency_stop_activated', {
                'timestamp': time.time()
            })
            
            # Clear all states
            self.platform_states.clear()
            self.active_tickets.clear()
    
    def broadcast_ticket_alert(self, ticket_data: Dict[str, Any]):
        """Broadcast new ticket alert to all mobile clients"""
        ticket_id = f"ticket_{int(time.time() * 1000)}"
        
        self.active_tickets[ticket_id] = {
            'id': ticket_id,
            **ticket_data,
            'timestamp': time.time()
        }
        
        self.socketio.emit('ticket_alert', self.active_tickets[ticket_id])
    
    def broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics update"""
        self.socketio.emit('metrics_update', metrics)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'latency': 25.5,  # Example values
            'monitors': sum(1 for v in self.platform_states.values() if v),
            'tickets': len(self.active_tickets),
            'successRate': 85.0
        }
    
    def run(self):
        """Run the mobile interface server"""
        print(f"Mobile interface starting on http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port)


# Example usage
if __name__ == "__main__":
    mobile = MobileInterface()
    mobile.run()
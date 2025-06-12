"""
StealthMaster Web Dashboard
Modern, real-time dashboard for monitoring bot performance
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import asyncio
from typing import Dict, List, Any
from collections import defaultdict
import threading
import webbrowser

from ..database.statistics import stats_manager
from ..utils.logging import get_logger

logger = get_logger(__name__)

class StealthMasterDashboard:
    """Web-based dashboard for StealthMaster"""
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.app = Flask(__name__, 
                         template_folder='templates',
                         static_folder='static')
        CORS(self.app)
        self.host = host
        self.port = port
        self.setup_routes()
        
        # Real-time data storage
        self.live_data = {
            'tickets_found': [],
            'blocks_encountered': [],
            'active_monitors': {},
            'success_rate': 0,
            'total_attempts': 0,
            'selections': defaultdict(int)
        }
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/stats/live')
        def live_stats():
            """Get live statistics"""
            try:
                stats = stats_manager.get_summary()
                
                # Calculate hourly stats
                now = datetime.now()
                hour_ago = now - timedelta(hours=1)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'total_found': stats.get('total_found', 0),
                        'total_blocked': len(self.live_data['blocks_encountered']),
                        'success_rate': stats.get('overall_success_rate', 0),
                        'active_monitors': len(self.live_data['active_monitors']),
                        'last_update': now.isoformat(),
                        'hourly_found': self._count_events_since(self.live_data['tickets_found'], hour_ago),
                        'hourly_blocked': self._count_events_since(self.live_data['blocks_encountered'], hour_ago)
                    }
                })
            except Exception as e:
                logger.error(f"Error getting live stats: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/stats/history')
        def history_stats():
            """Get historical statistics"""
            try:
                # Get date range from query params
                days = int(request.args.get('days', 7))
                
                # Get daily stats
                daily_stats = self._get_daily_stats(days)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'daily': daily_stats,
                        'platforms': self._get_platform_stats(),
                        'selections': dict(self.live_data['selections'])
                    }
                })
            except Exception as e:
                logger.error(f"Error getting history stats: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/tickets/recent')
        def recent_tickets():
            """Get recent ticket events"""
            try:
                limit = int(request.args.get('limit', 50))
                selection = request.args.get('selection', None)
                
                tickets = self.live_data['tickets_found'][-limit:]
                
                # Filter by selection if specified
                if selection:
                    tickets = [t for t in tickets if t.get('selection') == selection]
                
                return jsonify({
                    'success': True,
                    'data': tickets
                })
            except Exception as e:
                logger.error(f"Error getting recent tickets: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/blocks/recent')
        def recent_blocks():
            """Get recent block events"""
            try:
                limit = int(request.args.get('limit', 50))
                
                blocks = self.live_data['blocks_encountered'][-limit:]
                
                return jsonify({
                    'success': True,
                    'data': blocks
                })
            except Exception as e:
                logger.error(f"Error getting recent blocks: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/selections')
        def get_selections():
            """Get available ticket selections"""
            return jsonify({
                'success': True,
                'data': {
                    'categories': [
                        {'id': 'seated', 'name': 'Seated', 'icon': '🪑'},
                        {'id': 'prato_a', 'name': 'Prato A', 'icon': '🅰️'},
                        {'id': 'prato_b', 'name': 'Prato B', 'icon': '🅱️'},
                        {'id': 'pit', 'name': 'Pit', 'icon': '🎸'},
                        {'id': 'vip', 'name': 'VIP', 'icon': '👑'}
                    ],
                    'counts': dict(self.live_data['selections'])
                }
            })
    
    def _count_events_since(self, events: List[Dict], since: datetime) -> int:
        """Count events since a given time"""
        count = 0
        for event in events:
            if 'timestamp' in event:
                event_time = datetime.fromisoformat(event['timestamp'])
                if event_time >= since:
                    count += 1
        return count
    
    def _get_daily_stats(self, days: int) -> List[Dict]:
        """Get daily statistics for the past N days"""
        daily_stats = []
        
        for i in range(days):
            date = datetime.now().date() - timedelta(days=i)
            
            # Count events for this day
            tickets_count = 0
            blocks_count = 0
            
            for ticket in self.live_data['tickets_found']:
                if 'timestamp' in ticket:
                    ticket_date = datetime.fromisoformat(ticket['timestamp']).date()
                    if ticket_date == date:
                        tickets_count += 1
            
            for block in self.live_data['blocks_encountered']:
                if 'timestamp' in block:
                    block_date = datetime.fromisoformat(block['timestamp']).date()
                    if block_date == date:
                        blocks_count += 1
            
            daily_stats.append({
                'date': date.isoformat(),
                'tickets_found': tickets_count,
                'blocks': blocks_count,
                'success_rate': (tickets_count / (tickets_count + blocks_count) * 100) if (tickets_count + blocks_count) > 0 else 0
            })
        
        return list(reversed(daily_stats))
    
    def _get_platform_stats(self) -> Dict[str, Dict]:
        """Get statistics by platform"""
        platform_stats = defaultdict(lambda: {'found': 0, 'blocked': 0, 'attempts': 0})
        
        for ticket in self.live_data['tickets_found']:
            platform = ticket.get('platform', 'unknown')
            platform_stats[platform]['found'] += 1
            platform_stats[platform]['attempts'] += 1
        
        for block in self.live_data['blocks_encountered']:
            platform = block.get('platform', 'unknown')
            platform_stats[platform]['blocked'] += 1
            platform_stats[platform]['attempts'] += 1
        
        # Calculate success rates
        for platform, stats in platform_stats.items():
            if stats['attempts'] > 0:
                stats['success_rate'] = (stats['found'] / stats['attempts']) * 100
            else:
                stats['success_rate'] = 0
        
        return dict(platform_stats)
    
    def add_ticket_found(self, platform: str, event: str, selection: str, price: float = None):
        """Add a ticket found event"""
        self.live_data['tickets_found'].append({
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'event': event,
            'selection': selection,
            'price': price
        })
        
        # Update selection count
        self.live_data['selections'][selection] += 1
        
        # Keep only last 1000 events
        if len(self.live_data['tickets_found']) > 1000:
            self.live_data['tickets_found'] = self.live_data['tickets_found'][-1000:]
    
    def add_block_encountered(self, platform: str, reason: str):
        """Add a block encountered event"""
        self.live_data['blocks_encountered'].append({
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'reason': reason
        })
        
        # Keep only last 1000 events
        if len(self.live_data['blocks_encountered']) > 1000:
            self.live_data['blocks_encountered'] = self.live_data['blocks_encountered'][-1000:]
    
    def update_active_monitor(self, monitor_id: str, status: str, details: Dict = None):
        """Update active monitor status"""
        self.live_data['active_monitors'][monitor_id] = {
            'status': status,
            'last_update': datetime.now().isoformat(),
            'details': details or {}
        }
    
    def start(self):
        """Start the dashboard server"""
        def run_server():
            logger.info(f"🚀 Starting dashboard at http://{self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        
        # Start Flask in a separate thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Open browser
        import time
        time.sleep(1)  # Wait for server to start
        webbrowser.open(f'http://{self.host}:{self.port}')
        
        logger.info("✅ Dashboard started successfully")
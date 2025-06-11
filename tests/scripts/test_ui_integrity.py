import pytest
import asyncio
from textual.pilot import Pilot
from unittest.mock import AsyncMock, MagicMock, patch
import time
import json

from src.ui.velocity_dashboard import VelocityDashboard
from src.ui.realtime_engine import RealtimeEngine
from src.orchestration.state import StateManager

class TestUIIntegrity:
    """Tests for UI/TUI responsiveness and data binding."""
    
    @pytest.mark.asyncio
    async def test_ui_update_latency(self):
        """UI-01: Test UI update latency under 50ms requirement."""
        async with Pilot(VelocityDashboard) as pilot:
            app = pilot.app
            
            # Simulate state change
            update_times = []
            
            for _ in range(10):
                start = time.perf_counter()
                
                # Trigger state update
                await app.update_metric('success_rate', 95.5)
                await pilot.pause(0.001)  # Allow UI to process
                
                # Measure update time
                update_time = (time.perf_counter() - start) * 1000
                update_times.append(update_time)
            
            avg_latency = sum(update_times) / len(update_times)
            max_latency = max(update_times)
            
            assert avg_latency < 50, f"Average UI latency too high: {avg_latency}ms"
            assert max_latency < 100, f"Max UI latency too high: {max_latency}ms"
    
    @pytest.mark.asyncio
    async def test_realtime_websocket_updates(self):
        """UI-02: Test WebSocket real-time data flow."""
        engine = RealtimeEngine()
        
        received_updates = []
        
        # Mock WebSocket client
        async def mock_client(websocket, path):
            async for message in websocket:
                received_updates.append(json.loads(message))
        
        # Start engine
        await engine.start(mock_client)
        
        # Send test updates
        test_events = [
            {'type': 'metric', 'data': {'cpu': 45.2}},
            {'type': 'alert', 'data': {'level': 'warning', 'message': 'High latency'}},
            {'type': 'status', 'data': {'browser_pool': 'healthy'}}
        ]
        
        for event in test_events:
            await engine.broadcast(event)
            await asyncio.sleep(0.01)  # Allow propagation
        
        await engine.stop()
        
        assert len(received_updates) == len(test_events), "Not all updates received"
        assert all(update['timestamp'] for update in received_updates), "Missing timestamps"
    
    @pytest.mark.asyncio
    async def test_hotkey_responsiveness(self):
        """UI-03: Test hotkey functionality and response time."""
        async with Pilot(VelocityDashboard) as pilot:
            app = pilot.app
            action_triggered = False
            
            # Mock action handler
            def mock_emergency_stop():
                nonlocal action_triggered
                action_triggered = True
            
            app.emergency_stop = mock_emergency_stop
            
            # Test emergency stop hotkey (Ctrl+X)
            start = time.perf_counter()
            await pilot.press("ctrl+x")
            await pilot.pause(0.01)
            response_time = (time.perf_counter() - start) * 1000
            
            assert action_triggered, "Hotkey action not triggered"
            assert response_time < 100, f"Hotkey response too slow: {response_time}ms"
    
    @pytest.mark.asyncio
    async def test_performance_graph_updates(self):
        """UI-04: Test performance graph real-time updates."""
        async with Pilot(VelocityDashboard) as pilot:
            app = pilot.app
            
            # Get performance graph widget
            graph_widget = app.query_one("#performance_graph")
            initial_data_points = len(graph_widget.data_points)
            
            # Add performance data
            for i in range(10):
                await app.add_performance_metric({
                    'timestamp': time.time(),
                    'cpu': 50 + i,
                    'memory': 60 + i,
                    'success_rate': 95 - i * 0.5
                })
                await pilot.pause(0.05)
            
            final_data_points = len(graph_widget.data_points)
            
            assert final_data_points > initial_data_points, "Graph not updating"
            assert graph_widget.is_updating, "Graph update flag not set"
    
    @pytest.mark.asyncio
    async def test_alert_system(self):
        """UI-05: Test alert system (audio/haptic feedback)."""
        async with Pilot(VelocityDashboard) as pilot:
            app = pilot.app
            alerts_triggered = []
            
            # Mock alert handlers
            app.trigger_audio_alert = lambda level: alerts_triggered.append(('audio', level))
            app.trigger_haptic_alert = lambda pattern: alerts_triggered.append(('haptic', pattern))
            
            # Trigger different alert levels
            await app.show_alert('info', 'Test info')
            await app.show_alert('warning', 'Test warning')
            await app.show_alert('critical', 'Test critical')
            
            await pilot.pause(0.1)
            
            assert len(alerts_triggered) >= 2, "Not enough alerts triggered"
            assert any(a[0] == 'audio' for a in alerts_triggered), "No audio alerts"
            assert any(a[1] == 'critical' for a in alerts_triggered), "No critical alerts"
    
    @pytest.mark.asyncio
    async def test_data_binding_consistency(self):
        """UI-06: Test UI data binding with backend state."""
        state_manager = StateManager()
        
        async with Pilot(VelocityDashboard) as pilot:
            app = pilot.app
            app.bind_state_manager(state_manager)
            
            # Update backend state
            await state_manager.update({
                'active_browsers': 5,
                'success_rate': 92.3,
                'total_purchases': 42
            })
            
            await pilot.pause(0.1)  # Allow UI update
            
            # Check UI reflects state
            stats_widget = app.query_one("#stats_display")
            displayed_text = stats_widget.renderable
            
            assert "5" in str(displayed_text), "Active browsers not displayed"
            assert "92.3" in str(displayed_text), "Success rate not displayed"
            assert "42" in str(displayed_text), "Total purchases not displayed"
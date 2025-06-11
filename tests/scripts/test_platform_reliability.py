import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from datetime import datetime
import time

from src.platforms.ticketmaster import TicketmasterHandler
from src.platforms.vivaticket import VivaTicketHandler
from src.platforms.fansale import FanSaleHandler
from src.profiles.manager import ProfileManager
from src.browser.pool import BrowserPool

class TestPlatformReliability:
    """Tests for platform handler reliability and error recovery."""
    
    @pytest.fixture
    async def mock_browser_pool(self):
        pool = AsyncMock(spec=BrowserPool)
        pool.acquire_context = AsyncMock()
        pool.release_context = AsyncMock()
        return pool
    
    @pytest.fixture
    async def mock_profile_manager(self):
        manager = AsyncMock(spec=ProfileManager)
        manager.get_profile = AsyncMock(return_value={
            'email': 'test@example.com',
            'password': 'testpass',
            'platform_data': {}
        })
        return manager
    
    @pytest.mark.asyncio
    async def test_login_retry_mechanism(self, mock_browser_pool, mock_profile_manager):
        """RELIABILITY-01: Verify login retry logic across platforms."""
        platforms = [
            TicketmasterHandler(mock_browser_pool, mock_profile_manager),
            VivaTicketHandler(mock_browser_pool, mock_profile_manager),
            FanSaleHandler(mock_browser_pool, mock_profile_manager)
        ]
        
        for platform in platforms:
            # Mock failing login attempts
            platform._perform_login = AsyncMock(side_effect=[
                Exception("Network error"),
                Exception("Timeout"),
                True  # Success on third attempt
            ])
            
            result = await platform.login('test_profile')
            
            assert result is True, f"{platform.__class__.__name__} login retry failed"
            assert platform._perform_login.call_count == 3, "Did not retry expected times"
    
    @pytest.mark.asyncio
    async def test_queue_it_handling(self, mock_browser_pool):
        """RELIABILITY-02: Test Ticketmaster Queue-it handling."""
        handler = TicketmasterHandler(mock_browser_pool, None)
        
        # Mock page in queue
        mock_page = AsyncMock()
        mock_page.url = "queue.ticketmaster.it"
        mock_page.wait_for_url = AsyncMock()
        mock_page.locator = AsyncMock()
        
        mock_context = AsyncMock()
        mock_context.pages = [mock_page]
        
        # Test queue detection and waiting
        await handler._handle_queue(mock_context)
        
        assert mock_page.wait_for_url.called
        assert "ticketmaster.it" in str(mock_page.wait_for_url.call_args)
    
    @pytest.mark.asyncio
    async def test_session_recovery(self, mock_browser_pool, mock_profile_manager):
        """RELIABILITY-03: Test session recovery after connection loss."""
        handler = VivaTicketHandler(mock_browser_pool, mock_profile_manager)
        
        # Simulate session loss
        handler._active_sessions = {'test_profile': AsyncMock()}
        handler._active_sessions['test_profile'].pages = AsyncMock(
            side_effect=Exception("Target closed")
        )
        
        # Attempt to use the session
        result = await handler.search_events('test_profile', 'concert')
        
        # Should attempt recovery
        assert mock_browser_pool.acquire_context.called
        assert 'test_profile' in handler._active_sessions
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, mock_browser_pool):
        """RELIABILITY-04: Test concurrent search operations."""
        handler = FanSaleHandler(mock_browser_pool, None)
        
        # Mock search operation
        async def mock_search(profile, query):
            await asyncio.sleep(0.1)  # Simulate work
            return [{'event': query, 'price': 100}]
        
        handler.search_events = mock_search
        
        # Run 10 concurrent searches
        tasks = [
            handler.search_events(f'profile_{i}', f'event_{i}')
            for i in range(10)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        assert len(results) == 10, "Not all searches completed"
        assert duration < 0.5, f"Concurrent execution too slow: {duration}s"
    
    @pytest.mark.asyncio
    async def test_purchase_state_machine(self, mock_browser_pool):
        """RELIABILITY-05: Test purchase workflow state transitions."""
        handler = TicketmasterHandler(mock_browser_pool, None)
        
        states = []
        
        # Mock state tracking
        original_method = handler._update_state
        async def track_state(state):
            states.append(state)
            return await original_method(state)
        
        handler._update_state = track_state
        
        # Execute purchase workflow
        mock_page = AsyncMock()
        await handler._execute_purchase_flow(mock_page, {
            'event_id': '123',
            'tickets': 2
        })
        
        expected_states = [
            'searching', 'selecting_tickets', 'entering_details',
            'confirming', 'completed'
        ]
        
        assert states == expected_states, f"Invalid state progression: {states}"
# tests/test_models.py
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from src.core.models import EnhancedTicketOpportunity, DataUsageTracker
from src.core.enums import PlatformType, PriorityLevel


class TestEnhancedTicketOpportunity:
    """Test suite for EnhancedTicketOpportunity model."""
    
    def test_initialization(self):
        """Test basic initialization of ticket opportunity."""
        opportunity = EnhancedTicketOpportunity(
            id="test_opp_123",
            platform=PlatformType.TICKETMASTER,
            event_name="Test Concert",
            url="https://example.com/tickets",
            offer_url="https://example.com/tickets/offer",
            section="VIP",
            price=100.0,
            quantity=2,
            detected_at=datetime.now(),
            priority=PriorityLevel.HIGH
        )
        
        assert opportunity.id == "test_opp_123"
        assert opportunity.platform == PlatformType.TICKETMASTER
        assert opportunity.event_name == "Test Concert"
        assert opportunity.url == "https://example.com/tickets"
        assert opportunity.offer_url == "https://example.com/tickets/offer"
        assert opportunity.price == 100.0
        assert opportunity.section == "VIP"
        assert opportunity.quantity == 2
        assert opportunity.priority == PriorityLevel.HIGH
        assert isinstance(opportunity.detected_at, datetime)
    
    def test_fingerprint_generation(self):
        """Test that opportunity fingerprints are generated."""
        opp1 = EnhancedTicketOpportunity(
            id="test_1",
            platform=PlatformType.TICKETMASTER,
            event_name="Concert 1",
            url="https://example.com/1",
            offer_url="https://example.com/1/offer",
            section="VIP",
            price=50.0,
            quantity=2,
            detected_at=datetime.now(),
            priority=PriorityLevel.HIGH
        )
        
        opp2 = EnhancedTicketOpportunity(
            id="test_2",
            platform=PlatformType.TICKETMASTER,
            event_name="Concert 2", 
            url="https://example.com/2",
            offer_url="https://example.com/2/offer",
            section="VIP",
            price=75.0,
            quantity=2,
            detected_at=datetime.now(),
            priority=PriorityLevel.HIGH
        )
        
        assert opp1.fingerprint != opp2.fingerprint
        assert len(opp1.fingerprint) > 0
        assert len(opp2.fingerprint) > 0
    
    def test_age_calculation(self):
        """Test age calculation functionality."""
        old_time = datetime.now()
        opportunity = EnhancedTicketOpportunity(
            id="test_age",
            platform=PlatformType.FANSALE,
            event_name="Bruce Springsteen",
            url="https://fansale.com/tickets",
            offer_url="https://fansale.com/tickets/offer",
            section="General Admission",
            price=200.0,
            quantity=1,
            detected_at=old_time,
            priority=PriorityLevel.HIGH
        )
        
        # Age should be very small (just created)
        assert opportunity.age_seconds >= 0
        assert opportunity.is_fresh is True
    
    def test_priority_comparison(self):
        """Test priority comparison."""
        high_priority = EnhancedTicketOpportunity(
            id="high_test",
            platform=PlatformType.TICKETMASTER,
            event_name="High Priority Event",
            url="https://example.com/high",
            offer_url="https://example.com/high/offer",
            section="VIP",
            price=100.0,
            quantity=1,
            detected_at=datetime.now(),
            priority=PriorityLevel.CRITICAL
        )
        
        low_priority = EnhancedTicketOpportunity(
            id="low_test",
            platform=PlatformType.TICKETMASTER,
            event_name="Low Priority Event", 
            url="https://example.com/low",
            offer_url="https://example.com/low/offer",
            section="VIP",
            price=100.0,
            quantity=1,
            detected_at=datetime.now(),
            priority=PriorityLevel.LOW
        )
        
        assert high_priority.priority.numeric_value < low_priority.priority.numeric_value


class TestDataUsageTracker:
    """Test suite for DataUsageTracker model."""
    
    def test_initialization(self):
        """Test DataUsageTracker initialization."""
        tracker = DataUsageTracker()
        
        assert tracker.total_used_mb == 0.0
        assert tracker.session_used_mb == 0.0
        assert len(tracker.platform_usage) == 0
        assert len(tracker.profile_usage) == 0
    
    def test_add_usage(self):
        """Test adding data usage."""
        tracker = DataUsageTracker()
        
        # Add some usage
        tracker.add_usage(1024, platform="ticketmaster")
        tracker.add_usage(2048, platform="fansale", profile_id="profile_123")
        
        assert tracker.total_used_mb > 0
        assert tracker.session_used_mb > 0
        assert "ticketmaster" in tracker.platform_usage
        assert "fansale" in tracker.platform_usage
        assert "profile_123" in tracker.profile_usage
    
    def test_reset_session(self):
        """Test resetting session usage."""
        tracker = DataUsageTracker()
        
        # Add usage
        tracker.add_usage(1024, platform="ticketmaster")
        initial_session = tracker.session_used_mb
        initial_total = tracker.total_used_mb
        
        # Reset session
        tracker.reset_session_usage()
        
        assert tracker.session_used_mb == 0.0
        assert tracker.total_used_mb == initial_total  # Total should remain
    
    def test_approaching_limit(self):
        """Test limit checking."""
        tracker = DataUsageTracker()
        tracker.global_limit_mb = 10.0
        tracker.session_limit_mb = 5.0
        
        # Add small usage - should not be approaching limit
        tracker.add_usage(1024)  # 1KB
        assert not tracker.is_approaching_limit()
        
        # Add large usage to approach global limit
        tracker.add_usage(9 * 1024 * 1024)  # 9MB
        assert tracker.is_approaching_limit()
    
    def test_remaining_mb(self):
        """Test getting remaining MB."""
        tracker = DataUsageTracker()
        tracker.global_limit_mb = 10.0
        tracker.session_limit_mb = 5.0
        
        # Add 1MB
        tracker.add_usage(1024 * 1024)
        
        remaining = tracker.get_remaining_mb()
        assert remaining < 5.0  # Should be less than session limit
        assert remaining > 0
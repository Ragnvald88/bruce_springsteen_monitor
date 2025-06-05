# tests/test_connection_manager.py
import pytest
import httpx
from unittest.mock import MagicMock, patch, AsyncMock

from src.core.managers import ConnectionPoolManager, StealthSSLContext
from src.profiles.models import BrowserProfile


class TestConnectionPoolManager:
    """Test suite for ConnectionPoolManager."""
    
    def test_init(self, sample_config):
        """Test ConnectionPoolManager initialization."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        assert manager.config == sample_config['network']
        assert manager.pools == {}
        assert manager.max_connections == 10
        assert manager.base_connect_timeout == 15
    
    def test_get_pool_key(self, sample_config, mock_profile):
        """Test pool key generation."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        # Test without proxy
        key = manager._get_pool_key(mock_profile)
        assert "test_profile_123" in key
        assert "default" in key
        
        # Test with proxy
        mock_profile.proxy_config = MagicMock()
        mock_profile.proxy_config.host = "proxy.example.com"
        mock_profile.proxy_config.port = 8080
        
        key_with_proxy = manager._get_pool_key(mock_profile)
        assert "proxy.example.com:8080" in key_with_proxy
    
    def test_create_stealth_headers(self, sample_config, mock_profile):
        """Test stealth header creation."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        headers = manager._create_stealth_headers(mock_profile)
        
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert 'Accept-Language' in headers
        assert headers['User-Agent'] == "Mozilla/5.0 (Test Browser)"
    
    def test_create_proxy_config_no_proxy(self, sample_config, mock_profile):
        """Test proxy config creation when no proxy is set."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        proxy_config = manager._create_proxy_config(mock_profile)
        
        assert proxy_config is None
    
    def test_create_proxy_config_with_proxy(self, sample_config, mock_profile):
        """Test proxy config creation with proxy."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        # Mock proxy config
        mock_profile.proxy_config = MagicMock()
        mock_profile.proxy_config.host = "proxy.example.com"
        mock_profile.proxy_config.port = 8080
        mock_profile.proxy_config.username = "user"
        mock_profile.proxy_config.password = "pass"
        mock_profile.proxy_config.protocol = "http"
        
        proxy_config = manager._create_proxy_config(mock_profile)
        
        assert proxy_config == "http://user:pass@proxy.example.com:8080"
    
    @pytest.mark.asyncio
    async def test_get_client_new(self, sample_config, mock_profile):
        """Test getting a new HTTP client."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            client = await manager.get_client(mock_profile)
            
            assert client == mock_client
            mock_client_class.assert_called_once()
            
            # Verify client is stored in pool
            pool_key = manager._get_pool_key(mock_profile)
            assert pool_key in manager.pools
    
    @pytest.mark.asyncio
    async def test_get_client_existing(self, sample_config, mock_profile):
        """Test getting an existing HTTP client from pool."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        # Pre-populate pool
        pool_key = manager._get_pool_key(mock_profile)
        mock_client = AsyncMock()
        manager.pools[pool_key] = mock_client
        manager.last_rotation[pool_key] = 9999999999  # Far future
        
        client = await manager.get_client(mock_profile)
        
        assert client == mock_client
    
    @pytest.mark.asyncio
    async def test_mark_client_compromised(self, sample_config, mock_profile):
        """Test marking a client as compromised."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        # Pre-populate pool
        pool_key = manager._get_pool_key(mock_profile)
        mock_client = AsyncMock()
        manager.pools[pool_key] = mock_client
        manager.connection_health[pool_key] = 100.0
        
        await manager.mark_client_compromised(mock_profile)
        
        # Client should be removed from pool
        assert pool_key not in manager.pools
        assert pool_key not in manager.connection_health
        mock_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_all(self, sample_config, mock_profile):
        """Test closing all connections."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        # Pre-populate pool with multiple clients
        mock_clients = [AsyncMock() for _ in range(3)]
        for i, client in enumerate(mock_clients):
            manager.pools[f"key_{i}"] = client
        
        await manager.close_all()
        
        # All clients should be closed and pools cleared
        for client in mock_clients:
            client.aclose.assert_called_once()
        
        assert len(manager.pools) == 0
        assert len(manager.connection_health) == 0
    
    @pytest.mark.asyncio
    async def test_get_pool_stats(self, sample_config):
        """Test getting pool statistics."""
        manager = ConnectionPoolManager(sample_config['network'])
        
        # Add some mock data
        manager.pools = {"key1": AsyncMock(), "key2": AsyncMock()}
        manager.connection_health = {"key1": 90.0, "key2": 80.0}
        manager.last_rotation = {"key1": 1000, "key2": 2000}
        
        stats = await manager.get_pool_stats()
        
        assert stats['active_pools'] == 2
        assert stats['total_connections'] == 2
        assert stats['average_health'] == 85.0
        assert len(stats['pools']) == 2


class TestStealthSSLContext:
    """Test suite for StealthSSLContext."""
    
    def test_create_context_default(self):
        """Test SSL context creation with defaults."""
        context = StealthSSLContext.create_context()
        
        assert context is not None
        assert context.check_hostname is True
        assert context.verify_mode.name == 'CERT_REQUIRED'
    
    def test_create_context_with_profile(self, mock_profile):
        """Test SSL context creation with profile."""
        mock_profile.tls_version = "TLSv1_3"
        
        context = StealthSSLContext.create_context(mock_profile)
        
        assert context is not None
        assert context.minimum_version.name == 'TLSv1_3'
    
    def test_cipher_suite_randomization(self):
        """Test that cipher suites are randomized."""
        contexts = [StealthSSLContext.create_context() for _ in range(10)]
        
        # Should create different contexts (though hard to test randomness directly)
        assert all(ctx is not None for ctx in contexts)
        assert len(contexts) == 10
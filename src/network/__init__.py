"""
Network functionality for StealthMaster.
Includes proxy management and network utilities.
"""

# Proxy management modules will be imported when available

__all__ = [
    # Core
    'ProxyConfig',
    'ProxyCredentials',
    'ProxyProtocol',
    'ProxyType',
    'ProxyInstance',
    'ProxyStats',
    'RotationStrategy',
    'ProxyProvider',
    'ProxySelector',
    'ProxyHealthChecker',
    'BasicProxyHealthChecker',
    
    # Selectors
    'RoundRobinSelector',
    'RandomSelector',
    'LeastUsedSelector',
    'PerformanceBasedSelector',
    'StickySelector',
    
    # Providers
    'FileProxyProvider',
    'EnvironmentProxyProvider',
    'APIProxyProvider',
    
    # Manager
    'ProxyManager',
    'create_proxy_manager'
]
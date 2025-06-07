# Presentation: CLI Interface
"""
Command-line interface for the ticket monitoring application.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from application.config import ApplicationConfig
from adapters.platform_adapter import PlatformAdapter
from adapters.profile_adapter import ProfileAdapter

logger = logging.getLogger(__name__)


class CLIPresentation:
    """Command-line interface presentation layer"""
    
    def __init__(self, config: ApplicationConfig):
        self.config = config
        self._shutdown_event = asyncio.Event()
        self._tasks = []
        
    async def run(self):
        """Run the CLI application"""
        self._print_banner()
        
        # Validate config
        if self.config.dry_run:
            logger.warning("🔧 Running in DRY RUN mode - no tickets will be purchased")
        
        logger.info(f"🎯 Mode: {self.config.mode.upper()}")
        logger.info(f"📄 Monitoring {len(self.config.targets)} targets")
        logger.info(f"🔌 {len(self.config.proxies)} proxies configured")
        
        # Import here to avoid circular imports
        try:
            # Try to use existing orchestrator with adapters
            from core.orchestrator import UnifiedOrchestrator
            from profiles.manager import ProfileManager
            from profiles.utils import parse_profile_manager_config
            
            # Create profile manager config
            pm_config = {
                'num_target_profiles': self.config.num_profiles,
                'profiles_per_platform': self.config.profiles_per_platform,
                'proxy_configs': self._parse_proxies(),
            }
            
            # Create profile manager
            profile_manager = ProfileManager(config=pm_config)
            await profile_manager.initialize()
            
            # Map config to old format
            old_config = self._create_legacy_config()
            
            # Create orchestrator
            orchestrator = UnifiedOrchestrator(
                config=old_config,
                profile_manager=profile_manager,
                mode=self.config.mode
            )
            
            # Initialize
            await orchestrator.initialize()
            
            # Run
            logger.info("🚀 Starting ticket monitoring...")
            await orchestrator.run()
            
        except ImportError as e:
            logger.error(f"Failed to import legacy components: {e}")
            logger.info("Using simplified monitoring...")
            await self._run_simple_monitoring()
        
    async def shutdown(self):
        """Shutdown the application gracefully"""
        logger.info("🛑 Shutting down...")
        self._shutdown_event.set()
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        logger.info("👋 Shutdown complete")
    
    def _print_banner(self):
        """Print application banner"""
        print("""
================================================================================
🎸 BRUCE SPRINGSTEEN TICKET HUNTER - CLEAN ARCHITECTURE
================================================================================
        """)
    
    def _parse_proxies(self):
        """Parse proxy configurations"""
        from domain.entities import ProxyConfig
        
        proxies = []
        for proxy_data in self.config.proxies:
            proxy = ProxyConfig(
                host=proxy_data.get('host', ''),
                port=proxy_data.get('port', 0),
                username=proxy_data.get('username'),
                password=proxy_data.get('password'),
                proxy_type=proxy_data.get('type', 'http'),
                country_code=proxy_data.get('country_code'),
                proxy_provider=proxy_data.get('provider')
            )
            proxies.append(proxy)
        
        return proxies
    
    def _create_legacy_config(self):
        """Create legacy config format for compatibility"""
        return {
            'settings': {
                'mode': self.config.mode,
                'dry_run': self.config.dry_run,
                'headless': self.config.headless,
                'browser': self.config.browser_type,
            },
            'targets': [
                {
                    'event_name': target.event_name,
                    'url': target.url,
                    'platform': target.platform,
                    'priority': target.priority,
                    'check_interval': target.check_interval,
                    'enabled': target.enabled,
                }
                for target in self.config.targets
            ],
            'strike_settings': {
                'max_parallel': self.config.max_concurrent_strikes,
                'timeout': self.config.request_timeout,
            },
            'data_usage': {
                'global_limit_mb': self.config.data_limit_mb,
            }
        }
    
    async def _run_simple_monitoring(self):
        """Fallback simple monitoring implementation"""
        logger.info("Running simple monitoring...")
        
        while not self._shutdown_event.is_set():
            for target in self.config.targets:
                if not target.enabled:
                    continue
                
                logger.info(f"Checking {target.event_name} on {target.platform}...")
                # Simple check logic here
                
            await asyncio.sleep(30)
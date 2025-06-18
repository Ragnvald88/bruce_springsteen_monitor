"""
StealthMaster V2 Integration Script
===================================
Integrates all upgrades into the existing StealthMaster project
"""

import os
import sys
import shutil
import asyncio
from pathlib import Path
import logging

# Setup paths
project_root = Path(__file__).parent.parent
upgrades_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(upgrades_dir))

# Import upgrade modules
from cloudflare_bypass import cloudflare_bypass
from resource_manager import resource_manager
from fansale_monitor_v2 import FanSaleMonitorV2
from ticket_strike_engine import ParallelStrikeEngine
from italian_proxy_manager import italian_proxy_manager
from human_behavior import AdvancedHumanBehavior

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StealthMasterV2:
    """
    Enhanced StealthMaster with all upgrades integrated
    """
    
    def __init__(self):
        self.config = self._load_config()
        self.monitor = None
        self.strike_engine = None
        self.running = False
        
    def _load_config(self):
        """Load configuration from .env and config.yaml"""
        from dotenv import load_dotenv
        load_dotenv()
        
        config = {
            'email': os.getenv('FANSALE_EMAIL'),
            'password': os.getenv('FANSALE_PASSWORD'),
            'target_url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388',
            'max_price': 800,
            'target_sections': [],  # Any section
            'user_info': {
                'first_name': 'Ronald',
                'last_name': 'Hoogenberg',
                'email': os.getenv('FANSALE_EMAIL'),
                'phone': '+39 123 456 7890',  # Update with your phone
                'address': 'Via Example 123',
                'city': 'Milano',
                'zip_code': '20121'
            },
            'payment_info': {
                'method': 'credit_card',
                # Add payment details securely
            }
        }
        
        return config
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing StealthMaster V2...")
        
        # Start CloudFlare bypass service
        logger.info("Starting CloudFlare bypass service...")
        await cloudflare_bypass.bypass.start_flaresolverr()
        
        # Test Italian proxies
        logger.info("Testing Italian proxies...")
        await italian_proxy_manager.test_all_proxies()
        
        # Initialize monitor
        logger.info("Initializing FanSale monitor...")
        self.monitor = FanSaleMonitorV2(self.config)
        
        # Initialize strike engine
        logger.info("Initializing strike engine...")
        self.strike_engine = ParallelStrikeEngine(self.config)
        
        # Connect monitor to strike engine
        self._connect_components()
        
        logger.info("Initialization complete!")
    
    def _connect_components(self):
        """Connect monitor and strike engine"""
        # Override monitor's ticket handler
        original_handler = self.monitor._handle_new_ticket
        
        async def enhanced_handler(ticket):
            # Call original handler
            await original_handler(ticket)
            
            # Execute strike
            logger.info(f"🎯 Executing strike on ticket {ticket.offer_id}...")
            
            # Get available contexts from monitor
            contexts = [s['context'] for s in self.monitor.sessions.values()]
            
            # Execute parallel strikes
            result = await self.strike_engine.execute_parallel_strikes(
                contexts,
                ticket
            )
            
            if result.success:
                logger.info(
                    f"✅ TICKET SECURED! Confirmation: {result.confirmation_number} "
                    f"(Time: {result.execution_time_ms:.0f}ms)"
                )
                
                # Stop monitoring after success
                await self.stop()
            else:
                logger.warning(
                    f"❌ Strike failed: {result.error_message} "
                    f"(Stage: {result.stage_reached})"
                )
        
        self.monitor._handle_new_ticket = enhanced_handler
    
    async def run(self):
        """Run the enhanced monitoring system"""
        try:
            self.running = True
            
            # Initialize components
            await self.initialize()
            
            # Start monitoring
            logger.info("Starting ticket monitoring...")
            await self.monitor.start()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop all components gracefully"""
        if not self.running:
            return
        
        logger.info("Stopping StealthMaster V2...")
        self.running = False
        
        # Stop monitor
        if self.monitor:
            await self.monitor.stop()
        
        # Cleanup resources
        await resource_manager.cleanup_all()
        
        # Stop CloudFlare service
        cloudflare_bypass.bypass.stop_flaresolverr()
        
        logger.info("StealthMaster V2 stopped")
    
    async def get_status(self):
        """Get system status"""
        status = {
            'running': self.running,
            'monitor': await self.monitor.get_stats() if self.monitor else None,
            'strike_engine': self.strike_engine.get_statistics() if self.strike_engine else None,
            'proxies': italian_proxy_manager.get_statistics(),
            'resources': await resource_manager.get_stats()
        }
        
        return status


def print_banner():
    """Print startup banner"""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                        STEALTHMASTER V2.0                             ║
║                    Advanced Ticket Automation                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Features:                                                           ║
║  ✓ CloudFlare bypass with FlareSolverr                             ║
║  ✓ 8-minute session rotation                                       ║
║  ✓ Italian residential proxies                                     ║
║  ✓ Human behavior simulation                                       ║
║  ✓ Parallel strike execution                                       ║
║  ✓ Resource leak prevention                                        ║
║                                                                       ║
║  Target: Bruce Springsteen - Milano 2025                           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


async def main():
    """Main entry point"""
    print_banner()
    
    # Create and run StealthMaster V2
    stealth_master = StealthMasterV2()
    
    try:
        await stealth_master.run()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        await stealth_master.stop()


if __name__ == "__main__":
    # Use uvloop for better performance
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    # Run the system
    asyncio.run(main())

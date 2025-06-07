#!/usr/bin/env python3
"""
Comprehensive test script for ProfileIntegratedStrikeForce
Tests strike execution, profile coordination, and platform-specific strategies
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.strike_force import ProfileIntegratedStrikeForce
from src.core.enums import OperationMode, PlatformType, PriorityLevel
from src.core.models import EnhancedTicketOpportunity, DataUsageTracker
from src.profiles.manager import ProfileManager
from src.profiles.utils import create_profile_manager_from_config
from src.profiles.consolidated_models import ProfileQuality
from src.core.stealth.stealth_integration import BruceStealthIntegration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_strike_force.log')
    ]
)
logger = logging.getLogger(__name__)

class StrikeForceTest:
    """Test suite for strike force functionality"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.results = {
            'initialization': {},
            'strike_params': {},
            'profile_selection': {},
            'strike_execution': {},
            'platform_strategies': {},
            'errors': []
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            sys.exit(1)
    
    async def test_initialization(self) -> bool:
        """Test StrikeForce initialization"""
        logger.info("\n" + "="*80)
        logger.info("🔧 TESTING STRIKE FORCE INITIALIZATION")
        logger.info("="*80)
        
        try:
            # Initialize components
            self.profile_manager = create_profile_manager_from_config(self.config_path)
            await self.profile_manager.initialize(lazy_load=True)
            
            self.data_tracker = DataUsageTracker(
                global_limit_mb=self.config.get('data_limits', {}).get('global_limit_mb', 5000),
                session_limit_mb=self.config.get('data_limits', {}).get('session_limit_mb', 1000)
            )
            
            # Create mock stealth integration for testing
            self.stealth_integration = Mock(spec=BruceStealthIntegration)
            self.stealth_integration.create_stealth_browser_context = AsyncMock()
            
            # Initialize strike force
            self.strike_force = ProfileIntegratedStrikeForce(
                stealth_integration=self.stealth_integration,
                profile_manager=self.profile_manager,
                data_tracker=self.data_tracker,
                config=self.config
            )
            
            self.results['initialization'] = {
                'success': True,
                'max_parallel': self.strike_force.max_parallel,
                'strike_timeout': self.strike_force.strike_timeout,
                'platform_strategies': list(self.strike_force.platform_strategies.keys())
            }
            
            logger.info(f"✅ StrikeForce initialized")
            logger.info(f"   Max parallel strikes: {self.strike_force.max_parallel}")
            logger.info(f"   Strike timeout: {self.strike_force.strike_timeout}s")
            logger.info(f"   Platform strategies: {len(self.strike_force.platform_strategies)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}", exc_info=True)
            self.results['initialization'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_strike_params(self) -> Dict[str, Any]:
        """Test strike parameter generation for different modes"""
        logger.info("\n" + "="*80)
        logger.info("⚙️ TESTING STRIKE PARAMETERS")
        logger.info("="*80)
        
        if not hasattr(self, 'strike_force'):
            logger.error("❌ StrikeForce not initialized")
            return {}
        
        results = {}
        
        # Create test opportunity
        test_opportunity = EnhancedTicketOpportunity(
            id="test_opp_123",
            platform=PlatformType.FANSALE,
            event_name="Test Event",
            url="https://test.com",
            section="Test Section",
            price=100.0,
            detected_at=datetime.now(),
            priority=PriorityLevel.HIGH
        )
        
        # Test each operation mode
        modes = [
            OperationMode.BEAST,
            OperationMode.STEALTH,
            OperationMode.ULTRA_STEALTH,
            OperationMode.ADAPTIVE,
            OperationMode.HYBRID
        ]
        
        for mode in modes:
            logger.info(f"\n🎯 Testing {mode.value} mode parameters")
            
            try:
                params = self.strike_force._get_strike_params(mode, test_opportunity)
                
                results[mode.value] = {
                    'profile_count': params['profile_count'],
                    'timeout': params['timeout'],
                    'race_mode': params['race_mode'],
                    'retry_on_block': params.get('retry_on_block', False),
                    'min_quality': params.get('min_quality', ProfileQuality.LOW).value,
                    'data_optimization': params.get('data_optimization', 'N/A')
                }
                
                logger.info(f"   Profile count: {params['profile_count']}")
                logger.info(f"   Timeout: {params['timeout']}s")
                logger.info(f"   Race mode: {params['race_mode']}")
                logger.info(f"   Min quality: {params.get('min_quality', 'N/A')}")
                
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
                results[mode.value] = {'error': str(e)}
        
        self.results['strike_params'] = results
        return results
    
    async def test_profile_selection_for_strike(self) -> Dict[str, Any]:
        """Test profile selection for strikes"""
        logger.info("\n" + "="*80)
        logger.info("👥 TESTING PROFILE SELECTION FOR STRIKES")
        logger.info("="*80)
        
        if not hasattr(self, 'strike_force'):
            logger.error("❌ StrikeForce not initialized")
            return {}
        
        results = {}
        
        # Test opportunity
        test_opportunity = EnhancedTicketOpportunity(
            id="test_profile_selection",
            platform=PlatformType.FANSALE,
            event_name="Profile Selection Test",
            url="https://test.com",
            section="Test",
            price=100.0,
            detected_at=datetime.now(),
            priority=PriorityLevel.HIGH
        )
        
        # Test different profile counts
        test_configs = [
            {'profile_count': 1, 'min_quality': ProfileQuality.HIGH},
            {'profile_count': 3, 'min_quality': ProfileQuality.MEDIUM},
            {'profile_count': 5, 'min_quality': ProfileQuality.LOW}
        ]
        
        for config in test_configs:
            logger.info(f"\n📋 Testing selection: {config['profile_count']} profiles, min quality: {config['min_quality'].value}")
            
            try:
                profiles = await self.strike_force._select_profiles_for_strike(
                    test_opportunity, config
                )
                
                results[f"count_{config['profile_count']}"] = {
                    'requested': config['profile_count'],
                    'received': len(profiles),
                    'profile_ids': [p.profile_id for p in profiles] if profiles else [],
                    'success': len(profiles) > 0
                }
                
                logger.info(f"   Requested: {config['profile_count']}")
                logger.info(f"   Received: {len(profiles)}")
                
                if profiles:
                    for i, profile in enumerate(profiles):
                        logger.info(f"   Profile {i+1}: {profile.profile_id}")
                else:
                    logger.warning("   ⚠️ No profiles selected")
                
            except Exception as e:
                logger.error(f"   ❌ Selection error: {e}")
                results[f"count_{config['profile_count']}"] = {
                    'error': str(e),
                    'success': False
                }
        
        self.results['profile_selection'] = results
        return results
    
    async def test_strike_execution(self) -> Dict[str, Any]:
        """Test strike execution with mock opportunities"""
        logger.info("\n" + "="*80)
        logger.info("⚡ TESTING STRIKE EXECUTION")
        logger.info("="*80)
        
        if not hasattr(self, 'strike_force'):
            logger.error("❌ StrikeForce not initialized")
            return {}
        
        results = {}
        
        # Create test opportunities for each platform
        test_opportunities = [
            EnhancedTicketOpportunity(
                id="fansale_test_123",
                platform=PlatformType.FANSALE,
                event_name="FanSale Test Event",
                url="https://fansale.it/test",
                section="Prato Gold",
                price=250.0,
                detected_at=datetime.now(),
                priority=PriorityLevel.HIGH
            ),
            EnhancedTicketOpportunity(
                id="tm_test_456",
                platform=PlatformType.TICKETMASTER,
                event_name="Ticketmaster Test Event",
                url="https://ticketmaster.it/test",
                section="Tribune Est",
                price=180.0,
                detected_at=datetime.now(),
                priority=PriorityLevel.NORMAL
            ),
            EnhancedTicketOpportunity(
                id="viva_test_789",
                platform=PlatformType.VIVATICKET,
                event_name="Vivaticket Test Event",
                url="https://vivaticket.com/test",
                section="Parterre",
                price=300.0,
                detected_at=datetime.now(),
                priority=PriorityLevel.CRITICAL
            )
        ]
        
        # Mock the stealth integration to return a mock context
        mock_context = Mock()
        mock_context.close = AsyncMock()
        self.stealth_integration.create_stealth_browser_context.return_value = mock_context
        
        # Test each opportunity
        for opportunity in test_opportunities:
            logger.info(f"\n🎯 Testing strike for {opportunity.platform.value}: {opportunity.event_name}")
            logger.info(f"   Price: €{opportunity.price}")
            logger.info(f"   Section: {opportunity.section}")
            logger.info(f"   Priority: {opportunity.priority.value}")
            
            try:
                # Mock the platform-specific strike method
                platform_method = self.strike_force.platform_strategies.get(opportunity.platform)
                if platform_method:
                    # Replace with mock that returns success
                    original_method = platform_method
                    self.strike_force.platform_strategies[opportunity.platform] = AsyncMock(return_value=True)
                
                # Execute strike
                mode = OperationMode.ADAPTIVE
                success = await self.strike_force.execute_coordinated_strike(
                    opportunity, mode
                )
                
                results[opportunity.platform.value] = {
                    'opportunity_id': opportunity.id,
                    'success': success,
                    'mode': mode.value,
                    'price': opportunity.price,
                    'section': opportunity.section
                }
                
                if success:
                    logger.info(f"   ✅ Strike successful!")
                else:
                    logger.warning(f"   ⚠️ Strike failed")
                
                # Restore original method
                if platform_method:
                    self.strike_force.platform_strategies[opportunity.platform] = original_method
                
            except Exception as e:
                logger.error(f"   ❌ Strike error: {e}", exc_info=True)
                results[opportunity.platform.value] = {
                    'opportunity_id': opportunity.id,
                    'error': str(e),
                    'success': False
                }
        
        self.results['strike_execution'] = results
        return results
    
    def test_platform_strategies(self) -> Dict[str, Any]:
        """Test platform-specific strategies exist"""
        logger.info("\n" + "="*80)
        logger.info("🎲 TESTING PLATFORM STRATEGIES")
        logger.info("="*80)
        
        if not hasattr(self, 'strike_force'):
            logger.error("❌ StrikeForce not initialized")
            return {}
        
        results = {}
        
        expected_platforms = [
            PlatformType.FANSALE,
            PlatformType.TICKETMASTER,
            PlatformType.VIVATICKET
        ]
        
        for platform in expected_platforms:
            strategy = self.strike_force.platform_strategies.get(platform)
            
            results[platform.value] = {
                'has_strategy': strategy is not None,
                'method_name': strategy.__name__ if strategy else None,
                'is_async': asyncio.iscoroutinefunction(strategy) if strategy else False
            }
            
            if strategy:
                logger.info(f"✅ {platform.value}: {strategy.__name__} (async: {asyncio.iscoroutinefunction(strategy)})")
            else:
                logger.warning(f"⚠️ {platform.value}: No strategy defined")
        
        self.results['platform_strategies'] = results
        return results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("📋 STRIKE FORCE TEST REPORT")
        logger.info("="*80)
        
        # Initialization summary
        init_result = self.results.get('initialization', {})
        if init_result.get('success'):
            logger.info(f"\n✅ Initialization: Success")
            logger.info(f"   Max parallel: {init_result.get('max_parallel', 'N/A')}")
            logger.info(f"   Timeout: {init_result.get('strike_timeout', 'N/A')}s")
        else:
            logger.info(f"\n❌ Initialization: Failed - {init_result.get('error', 'Unknown error')}")
        
        # Strike params summary
        if self.results.get('strike_params'):
            logger.info("\n⚙️ Strike Parameters by Mode:")
            for mode, params in self.results['strike_params'].items():
                if 'error' not in params:
                    logger.info(f"   {mode}: {params.get('profile_count', 0)} profiles, {params.get('timeout', 0)}s timeout")
                else:
                    logger.info(f"   {mode}: ❌ Error - {params['error']}")
        
        # Profile selection summary
        if self.results.get('profile_selection'):
            logger.info("\n👥 Profile Selection:")
            for test, result in self.results['profile_selection'].items():
                if result.get('success'):
                    logger.info(f"   ✅ {test}: {result['received']}/{result['requested']} profiles")
                else:
                    logger.info(f"   ❌ {test}: Failed - {result.get('error', 'No profiles')}")
        
        # Strike execution summary
        if self.results.get('strike_execution'):
            logger.info("\n⚡ Strike Execution:")
            for platform, result in self.results['strike_execution'].items():
                status = "✅" if result.get('success') else "❌"
                logger.info(f"   {status} {platform}")
                if 'error' in result:
                    logger.info(f"      Error: {result['error']}")
        
        # Platform strategies summary
        if self.results.get('platform_strategies'):
            logger.info("\n🎲 Platform Strategies:")
            for platform, result in self.results['platform_strategies'].items():
                status = "✅" if result.get('has_strategy') else "⚠️"
                logger.info(f"   {status} {platform}: {result.get('method_name', 'None')}")
        
        # Errors summary
        if self.results['errors']:
            logger.info("\n❌ Errors encountered:")
            for error in self.results['errors']:
                logger.info(f"   - {error}")
        
        # Save results
        report_path = "test_strike_force_report.yaml"
        with open(report_path, 'w') as f:
            yaml.dump(self.results, f, default_flow_style=False)
        logger.info(f"\n📄 Full report saved to: {report_path}")

async def main():
    """Run all strike force tests"""
    config_path = "config/config.yaml"
    
    if not Path(config_path).exists():
        logger.error(f"❌ Config file not found: {config_path}")
        return
    
    tester = StrikeForceTest(config_path)
    
    try:
        # Run tests in sequence
        if await tester.test_initialization():
            tester.test_strike_params()
            await tester.test_profile_selection_for_strike()
            await tester.test_strike_execution()
            tester.test_platform_strategies()
        
        # Generate report
        tester.generate_report()
        
    except Exception as e:
        logger.error(f"❌ Test suite error: {e}", exc_info=True)
    
    finally:
        # Cleanup
        if hasattr(tester, 'profile_manager'):
            await tester.profile_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
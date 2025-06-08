#!/usr/bin/env python3
"""
Full integration test for the Bruce Springsteen ticket monitoring system
Tests the complete flow from monitoring to strike execution
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, MagicMock

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Try importing playwright
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Playwright not available - will use mocks")

from src.core.enhanced_orchestrator_v3 import UnifiedOrchestrator
from src.core.enums import OperationMode, PlatformType, PriorityLevel
from src.core.models import EnhancedTicketOpportunity

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_full_integration.log')
    ]
)
logger = logging.getLogger(__name__)

class IntegrationTest:
    """Full integration test suite"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.results = {
            'orchestrator_init': {},
            'subsystem_init': {},
            'monitoring_test': {},
            'opportunity_flow': {},
            'strike_flow': {},
            'data_usage': {},
            'performance': {},
            'errors': []
        }
        self.playwright = None
        self.orchestrator = None
    
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
    
    async def setup_playwright(self):
        """Setup playwright instance"""
        if PLAYWRIGHT_AVAILABLE:
            try:
                self.playwright = await async_playwright().start()
                logger.info("✅ Playwright initialized")
                return True
            except Exception as e:
                logger.error(f"❌ Playwright initialization failed: {e}")
                self.playwright = self._create_mock_playwright()
                return False
        else:
            self.playwright = self._create_mock_playwright()
            logger.info("⚠️ Using mock playwright (not installed)")
            return False
    
    def _create_mock_playwright(self):
        """Create mock playwright for testing without actual browser"""
        mock_playwright = Mock()
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()
        
        # Setup mock chain
        mock_playwright.chromium = Mock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()
        mock_browser.close = AsyncMock()
        
        return mock_playwright
    
    async def test_orchestrator_initialization(self) -> bool:
        """Test UnifiedOrchestrator initialization"""
        logger.info("\n" + "="*80)
        logger.info("🚀 TESTING ORCHESTRATOR INITIALIZATION")
        logger.info("="*80)
        
        try:
            start_time = time.time()
            
            # Create orchestrator
            self.orchestrator = UnifiedOrchestrator(
                config=self.config,
                playwright_instance=self.playwright,
                config_file_path=self.config_path,
                gui_queue=None
            )
            
            init_time = time.time() - start_time
            
            self.results['orchestrator_init'] = {
                'success': True,
                'init_time': init_time,
                'mode': self.orchestrator.mode.value,
                'dry_run': self.orchestrator.is_dry_run,
                'max_concurrent_strikes': self.orchestrator.max_concurrent_strikes,
                'max_concurrent_monitors': self.orchestrator.max_concurrent_monitors
            }
            
            logger.info(f"✅ Orchestrator initialized in {init_time:.2f}s")
            logger.info(f"   Mode: {self.orchestrator.mode.value}")
            logger.info(f"   Dry run: {self.orchestrator.is_dry_run}")
            logger.info(f"   Max strikes: {self.orchestrator.max_concurrent_strikes}")
            logger.info(f"   Max monitors: {self.orchestrator.max_concurrent_monitors}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Orchestrator initialization failed: {e}", exc_info=True)
            self.results['orchestrator_init'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def test_subsystem_initialization(self) -> bool:
        """Test subsystem initialization"""
        logger.info("\n" + "="*80)
        logger.info("🔧 TESTING SUBSYSTEM INITIALIZATION")
        logger.info("="*80)
        
        if not self.orchestrator:
            logger.error("❌ Orchestrator not initialized")
            return False
        
        try:
            start_time = time.time()
            success = await self.orchestrator.initialize_subsystems()
            init_time = time.time() - start_time
            
            if success:
                # Check each subsystem
                subsystems = {
                    'profile_manager': self.orchestrator.profile_manager is not None,
                    'connection_pool': self.orchestrator.connection_pool is not None,
                    'response_cache': self.orchestrator.response_cache is not None,
                    'stealth_integration': self.orchestrator.stealth_integration is not None,
                    'monitor': self.orchestrator.monitor is not None,
                    'strike_force': self.orchestrator.strike_force is not None,
                    'ticket_reserver': self.orchestrator.ticket_reserver is not None
                }
                
                self.results['subsystem_init'] = {
                    'success': True,
                    'init_time': init_time,
                    'subsystems': subsystems,
                    'all_initialized': all(subsystems.values())
                }
                
                logger.info(f"✅ Subsystems initialized in {init_time:.2f}s")
                for name, initialized in subsystems.items():
                    status = "✅" if initialized else "❌"
                    logger.info(f"   {status} {name}")
                
                # Profile manager details
                if self.orchestrator.profile_manager:
                    dynamic_count = len(self.orchestrator.profile_manager.dynamic_profiles)
                    static_count = len(self.orchestrator.profile_manager.static_profiles)
                    logger.info(f"\n📊 Profile Manager Stats:")
                    logger.info(f"   Dynamic profiles: {dynamic_count}")
                    logger.info(f"   Static profiles: {static_count}")
                    logger.info(f"   Platform pools: {list(self.orchestrator.profile_manager.platform_pools.keys())}")
                
                return True
            else:
                logger.error("❌ Subsystem initialization failed")
                self.results['subsystem_init'] = {
                    'success': False,
                    'error': 'initialize_subsystems returned False'
                }
                return False
                
        except Exception as e:
            logger.error(f"❌ Subsystem initialization error: {e}", exc_info=True)
            self.results['subsystem_init'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def test_monitoring_flow(self) -> Dict[str, Any]:
        """Test the monitoring flow"""
        logger.info("\n" + "="*80)
        logger.info("🔍 TESTING MONITORING FLOW")
        logger.info("="*80)
        
        if not self.orchestrator or not self.orchestrator.monitor:
            logger.error("❌ Monitor not available")
            return {}
        
        results = {}
        
        # Get enabled targets
        targets = [t for t in self.config.get('targets', []) if t.get('enabled', False)]
        
        for target in targets[:2]:  # Test first 2 targets
            platform_str = target.get('platform', '').lower()
            url = target.get('url', '')
            event_name = target.get('event_name', 'Unknown')
            priority_str = target.get('priority', 'NORMAL')
            
            # Map to enums
            platform_map = {
                'fansale': PlatformType.FANSALE,
                'ticketmaster': PlatformType.TICKETMASTER,
                'vivaticket': PlatformType.VIVATICKET
            }
            platform = platform_map.get(platform_str, PlatformType.FANSALE)
            priority = PriorityLevel[priority_str]
            
            logger.info(f"\n📡 Monitoring {platform_str}: {event_name}")
            
            try:
                start_time = time.time()
                
                # Check for opportunities
                opportunities = await self.orchestrator.monitor.check_ultra_efficient(
                    platform, url, event_name, priority
                )
                
                check_time = time.time() - start_time
                
                results[platform_str] = {
                    'event_name': event_name,
                    'opportunities_found': len(opportunities),
                    'check_time': check_time,
                    'success': True
                }
                
                if opportunities:
                    logger.info(f"   ✅ Found {len(opportunities)} opportunities in {check_time:.2f}s")
                    
                    # Queue opportunities
                    for opp in opportunities[:3]:  # Queue first 3
                        await self.orchestrator._queue_opportunity(opp)
                        logger.info(f"   📥 Queued: {opp.section} - €{opp.price}")
                    
                    results[platform_str]['queued'] = min(3, len(opportunities))
                else:
                    logger.info(f"   ℹ️ No opportunities found ({check_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"   ❌ Monitoring error: {e}")
                results[platform_str] = {
                    'event_name': event_name,
                    'error': str(e),
                    'success': False
                }
        
        # Check queue status
        queue_size = self.orchestrator.opportunity_queue.qsize()
        logger.info(f"\n📊 Opportunity queue size: {queue_size}")
        
        self.results['monitoring_test'] = results
        return results
    
    async def test_opportunity_flow(self) -> Dict[str, Any]:
        """Test opportunity queueing and processing"""
        logger.info("\n" + "="*80)
        logger.info("🎯 TESTING OPPORTUNITY FLOW")
        logger.info("="*80)
        
        if not self.orchestrator:
            logger.error("❌ Orchestrator not available")
            return {}
        
        results = {}
        
        # Create test opportunities
        test_opportunities = [
            EnhancedTicketOpportunity(
                id=f"test_opp_{i}",
                platform=PlatformType.FANSALE,
                event_name=f"Test Event {i}",
                url="https://test.com",
                section=f"Section {i}",
                price=100.0 + (i * 50),
                detected_at=datetime.now(),
                priority=PriorityLevel.HIGH if i == 0 else PriorityLevel.NORMAL
            )
            for i in range(3)
        ]
        
        # Queue opportunities
        logger.info("\n📥 Queueing test opportunities:")
        for opp in test_opportunities:
            await self.orchestrator._queue_opportunity(opp)
            logger.info(f"   Added: {opp.event_name} - €{opp.price}")
        
        # Check queue
        queue_size = self.orchestrator.opportunity_queue.qsize()
        results['queuing'] = {
            'opportunities_added': len(test_opportunities),
            'queue_size': queue_size,
            'success': queue_size > 0
        }
        
        logger.info(f"\n📊 Queue status: {queue_size} opportunities")
        
        # Test opportunity scoring
        logger.info("\n🎲 Testing opportunity scoring:")
        for opp in test_opportunities:
            score = self.orchestrator._calculate_opportunity_score(opp)
            results[f'score_{opp.id}'] = score
            logger.info(f"   {opp.event_name}: Score = {score:.2f}")
        
        self.results['opportunity_flow'] = results
        return results
    
    async def test_strike_flow(self) -> Dict[str, Any]:
        """Test strike execution flow (mock)"""
        logger.info("\n" + "="*80)
        logger.info("⚡ TESTING STRIKE FLOW (MOCK)")
        logger.info("="*80)
        
        if not self.orchestrator or not self.orchestrator.strike_force:
            logger.error("❌ Strike force not available")
            return {}
        
        results = {}
        
        # Create high-priority test opportunity
        test_opportunity = EnhancedTicketOpportunity(
            id="strike_test_123",
            platform=PlatformType.FANSALE,
            event_name="Bruce Springsteen Milano TEST",
            url="https://test.com/ticket",
            section="Prato Gold",
            price=250.0,
            detected_at=datetime.now(),
            priority=PriorityLevel.CRITICAL
        )
        
        logger.info(f"\n🎯 Testing strike for: {test_opportunity.event_name}")
        logger.info(f"   Platform: {test_opportunity.platform.value}")
        logger.info(f"   Section: {test_opportunity.section}")
        logger.info(f"   Price: €{test_opportunity.price}")
        
        try:
            # Mock the stealth integration for testing
            if hasattr(self.orchestrator, 'stealth_integration'):
                mock_context = Mock()
                mock_context.close = AsyncMock()
                self.orchestrator.stealth_integration.create_stealth_browser_context = AsyncMock(return_value=mock_context)
            
            # Mock the platform strategy to simulate success
            original_strategy = self.orchestrator.strike_force.platform_strategies.get(test_opportunity.platform)
            self.orchestrator.strike_force.platform_strategies[test_opportunity.platform] = AsyncMock(return_value=True)
            
            # Execute strike
            start_time = time.time()
            success = await self.orchestrator.strike_force.execute_coordinated_strike(
                test_opportunity,
                self.orchestrator.mode
            )
            strike_time = time.time() - start_time
            
            results['strike_execution'] = {
                'success': success,
                'execution_time': strike_time,
                'mode': self.orchestrator.mode.value,
                'opportunity_id': test_opportunity.id
            }
            
            if success:
                logger.info(f"   ✅ Strike successful! ({strike_time:.2f}s)")
            else:
                logger.warning(f"   ⚠️ Strike failed ({strike_time:.2f}s)")
            
            # Restore original strategy
            if original_strategy:
                self.orchestrator.strike_force.platform_strategies[test_opportunity.platform] = original_strategy
            
        except Exception as e:
            logger.error(f"   ❌ Strike error: {e}", exc_info=True)
            results['strike_execution'] = {
                'success': False,
                'error': str(e)
            }
        
        self.results['strike_flow'] = results
        return results
    
    async def test_data_usage_tracking(self) -> Dict[str, Any]:
        """Test data usage tracking"""
        logger.info("\n" + "="*80)
        logger.info("📊 TESTING DATA USAGE TRACKING")
        logger.info("="*80)
        
        if not self.orchestrator:
            logger.error("❌ Orchestrator not available")
            return {}
        
        tracker = self.orchestrator.data_tracker
        
        results = {
            'total_used_mb': tracker.total_used_mb,
            'blocked_resources_saved_mb': tracker.blocked_resources_saved_mb,
            'remaining_mb': tracker.get_remaining_mb(),
            'global_limit_mb': tracker.global_limit_mb,
            'session_limit_mb': tracker.session_limit_mb,
            'optimization_level': tracker.current_optimization_level.value,
            'is_approaching_80': tracker.is_approaching_limit(0.8),
            'is_approaching_95': tracker.is_approaching_limit(0.95)
        }
        
        logger.info(f"   Total used: {results['total_used_mb']:.2f} MB")
        logger.info(f"   Resources saved: {results['blocked_resources_saved_mb']:.2f} MB")
        logger.info(f"   Remaining: {results['remaining_mb']:.2f} MB")
        logger.info(f"   Optimization: {results['optimization_level']}")
        
        self.results['data_usage'] = results
        return results
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance and health metrics"""
        logger.info("\n" + "="*80)
        logger.info("⚡ TESTING PERFORMANCE METRICS")
        logger.info("="*80)
        
        if not self.orchestrator:
            logger.error("❌ Orchestrator not available")
            return {}
        
        # Get system health
        health = self.orchestrator.system_health
        
        # Get metrics
        metrics = self.orchestrator._get_detailed_metrics()
        
        results = {
            'health': {
                'cpu_percent': health.cpu_percent,
                'memory_percent': health.memory_percent,
                'is_healthy': health.is_healthy,
                'threat_level': health.threat_level,
                'active_tasks': health.active_tasks
            },
            'performance': {
                'total_attempts': metrics['performance']['total_attempts'],
                'total_successes': metrics['performance']['total_successes'],
                'total_detections': metrics['performance']['total_detections'],
                'queue_size': metrics['performance']['queue_size']
            },
            'cache': metrics.get('cache', {})
        }
        
        logger.info(f"\n💊 System Health:")
        logger.info(f"   CPU: {health.cpu_percent:.1f}%")
        logger.info(f"   Memory: {health.memory_percent:.1f}%")
        logger.info(f"   Healthy: {health.is_healthy}")
        logger.info(f"   Threat Level: {health.threat_level}")
        
        logger.info(f"\n📊 Performance:")
        logger.info(f"   Attempts: {results['performance']['total_attempts']}")
        logger.info(f"   Successes: {results['performance']['total_successes']}")
        logger.info(f"   Detections: {results['performance']['total_detections']}")
        
        self.results['performance'] = results
        return results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("📋 INTEGRATION TEST REPORT")
        logger.info("="*80)
        
        # Orchestrator initialization
        orch_init = self.results.get('orchestrator_init', {})
        if orch_init.get('success'):
            logger.info(f"\n✅ Orchestrator Init: Success ({orch_init.get('init_time', 0):.2f}s)")
            logger.info(f"   Mode: {orch_init.get('mode', 'N/A')}")
        else:
            logger.info(f"\n❌ Orchestrator Init: Failed - {orch_init.get('error', 'Unknown')}")
        
        # Subsystem initialization
        sub_init = self.results.get('subsystem_init', {})
        if sub_init.get('success'):
            logger.info(f"\n✅ Subsystems Init: Success ({sub_init.get('init_time', 0):.2f}s)")
            if 'subsystems' in sub_init:
                for name, initialized in sub_init['subsystems'].items():
                    status = "✅" if initialized else "❌"
                    logger.info(f"   {status} {name}")
        else:
            logger.info(f"\n❌ Subsystems Init: Failed - {sub_init.get('error', 'Unknown')}")
        
        # Monitoring test
        if self.results.get('monitoring_test'):
            logger.info("\n🔍 Monitoring Results:")
            for platform, result in self.results['monitoring_test'].items():
                if result.get('success'):
                    opp_count = result.get('opportunities_found', 0)
                    time_taken = result.get('check_time', 0)
                    logger.info(f"   ✅ {platform}: {opp_count} opportunities ({time_taken:.2f}s)")
                else:
                    logger.info(f"   ❌ {platform}: {result.get('error', 'Failed')}")
        
        # Strike flow
        strike_result = self.results.get('strike_flow', {}).get('strike_execution', {})
        if strike_result:
            status = "✅" if strike_result.get('success') else "❌"
            logger.info(f"\n{status} Strike Execution: {strike_result.get('success', False)}")
            if 'execution_time' in strike_result:
                logger.info(f"   Time: {strike_result['execution_time']:.2f}s")
        
        # Data usage
        if self.results.get('data_usage'):
            data = self.results['data_usage']
            logger.info(f"\n📊 Data Usage:")
            logger.info(f"   Used: {data.get('total_used_mb', 0):.2f} MB")
            logger.info(f"   Remaining: {data.get('remaining_mb', 0):.2f} MB")
            logger.info(f"   Optimization: {data.get('optimization_level', 'N/A')}")
        
        # Performance
        if self.results.get('performance'):
            perf = self.results['performance']
            if 'health' in perf:
                health = perf['health']
                logger.info(f"\n💊 System Health:")
                logger.info(f"   CPU: {health.get('cpu_percent', 0):.1f}%")
                logger.info(f"   Memory: {health.get('memory_percent', 0):.1f}%")
                logger.info(f"   Status: {'Healthy' if health.get('is_healthy') else 'Unhealthy'}")
        
        # Errors
        if self.results['errors']:
            logger.info("\n❌ Errors encountered:")
            for error in self.results['errors']:
                logger.info(f"   - {error}")
        
        # Save report
        report_path = "test_full_integration_report.yaml"
        with open(report_path, 'w') as f:
            yaml.dump(self.results, f, default_flow_style=False)
        logger.info(f"\n📄 Full report saved to: {report_path}")

async def main():
    """Run full integration test"""
    config_path = "config/config.yaml"
    
    if not Path(config_path).exists():
        logger.error(f"❌ Config file not found: {config_path}")
        return
    
    tester = IntegrationTest(config_path)
    
    try:
        # Setup
        await tester.setup_playwright()
        
        # Run tests
        if await tester.test_orchestrator_initialization():
            if await tester.test_subsystem_initialization():
                await tester.test_monitoring_flow()
                await tester.test_opportunity_flow()
                await tester.test_strike_flow()
                await tester.test_data_usage_tracking()
                await tester.test_performance_metrics()
        
        # Generate report
        tester.generate_report()
        
    except Exception as e:
        logger.error(f"❌ Integration test error: {e}", exc_info=True)
    
    finally:
        # Cleanup
        if tester.orchestrator:
            await tester.orchestrator.graceful_shutdown()
        if tester.playwright and PLAYWRIGHT_AVAILABLE:
            await tester.playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
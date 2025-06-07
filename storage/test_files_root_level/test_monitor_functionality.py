#!/usr/bin/env python3
"""
Comprehensive test script for ProfileAwareLightweightMonitor
Tests URL monitoring, opportunity detection parsing, and platform functionality
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import yaml
import httpx
from typing import Dict, List, Any

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.components import ProfileAwareLightweightMonitor, MonitoringMetrics
from src.core.enums import PlatformType, PriorityLevel
from src.core.models import DataUsageTracker
from src.core.managers import ConnectionPoolManager, ResponseCache
from src.profiles.manager import ProfileManager
from src.profiles.utils import create_profile_manager_from_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_monitor_functionality.log')
    ]
)
logger = logging.getLogger(__name__)

class MonitorTest:
    """Test suite for monitor functionality"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.results = {
            'url_tests': {},
            'parsing_tests': {},
            'platform_tests': {},
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
    
    async def test_url_accessibility(self) -> Dict[str, Any]:
        """Test if platform URLs are accessible"""
        logger.info("\n" + "="*80)
        logger.info("🌐 TESTING URL ACCESSIBILITY")
        logger.info("="*80)
        
        results = {}
        targets = self.config.get('targets', [])
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        ) as client:
            for target in targets:
                if not target.get('enabled', False):
                    continue
                
                platform = target.get('platform', 'unknown')
                url = target.get('url', '')
                event_name = target.get('event_name', 'Unknown')
                
                logger.info(f"\n📍 Testing {platform}: {event_name}")
                logger.info(f"   URL: {url}")
                
                try:
                    start_time = asyncio.get_event_loop().time()
                    response = await client.get(url)
                    elapsed = asyncio.get_event_loop().time() - start_time
                    
                    results[platform] = {
                        'url': url,
                        'event_name': event_name,
                        'status_code': response.status_code,
                        'response_time': elapsed,
                        'content_length': len(response.content),
                        'headers': dict(response.headers),
                        'success': response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        logger.info(f"   ✅ Success: {response.status_code} ({elapsed:.2f}s, {len(response.content):,} bytes)")
                    else:
                        logger.warning(f"   ⚠️ Non-200 status: {response.status_code}")
                    
                except Exception as e:
                    logger.error(f"   ❌ Error: {str(e)}")
                    results[platform] = {
                        'url': url,
                        'event_name': event_name,
                        'error': str(e),
                        'success': False
                    }
        
        self.results['url_tests'] = results
        return results
    
    async def test_monitor_initialization(self) -> bool:
        """Test ProfileAwareLightweightMonitor initialization"""
        logger.info("\n" + "="*80)
        logger.info("🔧 TESTING MONITOR INITIALIZATION")
        logger.info("="*80)
        
        try:
            # Initialize components
            profile_manager = create_profile_manager_from_config(self.config_path)
            await profile_manager.initialize(lazy_load=True)
            
            data_tracker = DataUsageTracker(
                global_limit_mb=self.config.get('data_limits', {}).get('global_limit_mb', 5000),
                session_limit_mb=self.config.get('data_limits', {}).get('session_limit_mb', 1000)
            )
            
            connection_pool = ConnectionPoolManager(self.config, profile_manager)
            response_cache = ResponseCache(max_size_mb=50)
            
            # Create monitor
            monitor = ProfileAwareLightweightMonitor(
                self.config,
                profile_manager,
                connection_pool,
                response_cache,
                data_tracker
            )
            
            logger.info("✅ Monitor initialized successfully")
            logger.info(f"   Detection patterns: {len(monitor.detection_patterns)} platforms")
            logger.info(f"   Default interval: {monitor.default_check_interval}s")
            logger.info(f"   Cache max age: {monitor.cache_max_age_s}s")
            
            # Store for later tests
            self.monitor = monitor
            self.profile_manager = profile_manager
            self.data_tracker = data_tracker
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Monitor initialization failed: {e}", exc_info=True)
            self.results['errors'].append(f"Monitor init: {str(e)}")
            return False
    
    async def test_opportunity_detection(self) -> Dict[str, Any]:
        """Test opportunity detection for each platform"""
        logger.info("\n" + "="*80)
        logger.info("🎯 TESTING OPPORTUNITY DETECTION")
        logger.info("="*80)
        
        if not hasattr(self, 'monitor'):
            logger.error("❌ Monitor not initialized")
            return {}
        
        results = {}
        targets = [t for t in self.config.get('targets', []) if t.get('enabled', False)]
        
        for target in targets:
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
            
            logger.info(f"\n🔍 Testing detection for {platform_str}: {event_name}")
            
            try:
                # Test detection
                opportunities = await self.monitor.check_ultra_efficient(
                    platform, url, event_name, priority
                )
                
                results[platform_str] = {
                    'event_name': event_name,
                    'opportunities_found': len(opportunities),
                    'opportunities': []
                }
                
                if opportunities:
                    logger.info(f"   ✅ Found {len(opportunities)} opportunities!")
                    for i, opp in enumerate(opportunities[:5]):  # Show first 5
                        logger.info(f"   📋 Opportunity {i+1}:")
                        logger.info(f"      Section: {opp.section}")
                        logger.info(f"      Price: €{opp.price}")
                        logger.info(f"      Quantity: {getattr(opp, 'quantity', 'N/A')}")
                        logger.info(f"      Detection method: {opp.detection_method}")
                        
                        results[platform_str]['opportunities'].append({
                            'id': opp.id,
                            'section': opp.section,
                            'price': opp.price,
                            'quantity': getattr(opp, 'quantity', 1),
                            'detection_method': opp.detection_method
                        })
                else:
                    logger.warning(f"   ⚠️ No opportunities detected")
                
                # Check metrics
                check_key = f"{platform.value}:{url}"
                if check_key in self.monitor.metrics:
                    metrics = self.monitor.metrics[check_key]
                    logger.info(f"   📊 Metrics:")
                    logger.info(f"      Successful checks: {metrics.successful_checks}")
                    logger.info(f"      Failed checks: {metrics.failed_checks}")
                    logger.info(f"      Detections: {metrics.detections}")
                    logger.info(f"      Avg response time: {metrics.avg_response_time:.2f}s")
                
            except Exception as e:
                logger.error(f"   ❌ Detection error: {e}", exc_info=True)
                results[platform_str] = {
                    'event_name': event_name,
                    'error': str(e)
                }
        
        self.results['parsing_tests'] = results
        return results
    
    async def test_detection_patterns(self) -> Dict[str, Any]:
        """Test detection patterns with sample HTML"""
        logger.info("\n" + "="*80)
        logger.info("🔬 TESTING DETECTION PATTERNS")
        logger.info("="*80)
        
        if not hasattr(self, 'monitor'):
            logger.error("❌ Monitor not initialized")
            return {}
        
        # Sample HTML for each platform
        test_samples = {
            PlatformType.FANSALE: """
                <div class="offer-item" data-offer-id="12345">
                    <span class="price">€250.00</span>
                    <div class="section">Prato Gold</div>
                    <div class="quantity">2 tickets</div>
                </div>
            """,
            PlatformType.TICKETMASTER: """
                <div class="listing" id="offer-67890">
                    <div class="price">€180.50</div>
                    <div class="section">Tribune Est</div>
                    <div>Row A</div>
                </div>
            """,
            PlatformType.VIVATICKET: """
                <li class="ticket-card" data-ticket-id="11111">
                    <span>€ 320,00</span>
                    <div class="settore">Parterre</div>
                </li>
            """
        }
        
        results = {}
        
        for platform, sample_html in test_samples.items():
            logger.info(f"\n🧪 Testing {platform.value} patterns")
            
            try:
                # Test parsing
                opportunities = await self.monitor._parse_opportunities(
                    platform=platform,
                    url="https://test.com",
                    event_name="Test Event",
                    priority=PriorityLevel.NORMAL,
                    content_bytes=sample_html.encode('utf-8'),
                    from_cache=False
                )
                
                results[platform.value] = {
                    'pattern_works': len(opportunities) > 0,
                    'opportunities_found': len(opportunities)
                }
                
                if opportunities:
                    logger.info(f"   ✅ Pattern works! Found {len(opportunities)} opportunities")
                    for opp in opportunities:
                        logger.info(f"      - {opp.section}: €{opp.price}")
                else:
                    logger.warning(f"   ⚠️ Pattern did not match sample HTML")
                
            except Exception as e:
                logger.error(f"   ❌ Pattern test error: {e}")
                results[platform.value] = {
                    'pattern_works': False,
                    'error': str(e)
                }
        
        self.results['platform_tests']['pattern_tests'] = results
        return results
    
    async def test_data_tracking(self) -> Dict[str, Any]:
        """Test data usage tracking"""
        logger.info("\n" + "="*80)
        logger.info("📊 TESTING DATA TRACKER")
        logger.info("="*80)
        
        if not hasattr(self, 'data_tracker'):
            logger.error("❌ Data tracker not initialized")
            return {}
        
        tracker = self.data_tracker
        
        # Test adding usage
        initial_usage = tracker.total_used_mb
        test_size_bytes = 1024 * 1024  # 1MB
        
        tracker.add_usage(test_size_bytes, "test_platform", "test_profile")
        
        results = {
            'initial_usage_mb': initial_usage,
            'test_size_mb': test_size_bytes / (1024 * 1024),
            'new_usage_mb': tracker.total_used_mb,
            'remaining_mb': tracker.get_remaining_mb(),
            'global_limit_mb': tracker.global_limit_mb,
            'session_limit_mb': tracker.session_limit_mb,
            'optimization_level': tracker.current_optimization_level.value,
            'is_approaching_limit_80': tracker.is_approaching_limit(0.8),
            'is_approaching_limit_95': tracker.is_approaching_limit(0.95)
        }
        
        logger.info(f"   Initial usage: {results['initial_usage_mb']:.2f} MB")
        logger.info(f"   Added: {results['test_size_mb']:.2f} MB")
        logger.info(f"   New usage: {results['new_usage_mb']:.2f} MB")
        logger.info(f"   Remaining: {results['remaining_mb']:.2f} MB")
        logger.info(f"   Optimization: {results['optimization_level']}")
        logger.info(f"   Approaching 80% limit: {results['is_approaching_limit_80']}")
        logger.info(f"   Approaching 95% limit: {results['is_approaching_limit_95']}")
        
        return results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("📋 TEST REPORT SUMMARY")
        logger.info("="*80)
        
        # URL accessibility summary
        logger.info("\n🌐 URL Accessibility:")
        for platform, result in self.results['url_tests'].items():
            status = "✅" if result.get('success', False) else "❌"
            logger.info(f"   {status} {platform}: {result.get('event_name', 'Unknown')}")
            if 'error' in result:
                logger.info(f"      Error: {result['error']}")
        
        # Parsing summary
        logger.info("\n🎯 Opportunity Detection:")
        for platform, result in self.results['parsing_tests'].items():
            if 'error' in result:
                logger.info(f"   ❌ {platform}: Error - {result['error']}")
            else:
                count = result.get('opportunities_found', 0)
                status = "✅" if count > 0 else "⚠️"
                logger.info(f"   {status} {platform}: {count} opportunities found")
        
        # Pattern tests summary
        if 'pattern_tests' in self.results['platform_tests']:
            logger.info("\n🔬 Pattern Tests:")
            for platform, result in self.results['platform_tests']['pattern_tests'].items():
                status = "✅" if result.get('pattern_works', False) else "❌"
                logger.info(f"   {status} {platform}")
        
        # Errors summary
        if self.results['errors']:
            logger.info("\n❌ Errors encountered:")
            for error in self.results['errors']:
                logger.info(f"   - {error}")
        
        # Save results to file
        report_path = "test_monitor_report.yaml"
        with open(report_path, 'w') as f:
            yaml.dump(self.results, f, default_flow_style=False)
        logger.info(f"\n📄 Full report saved to: {report_path}")

async def main():
    """Run all monitor tests"""
    config_path = "config/config.yaml"
    
    if not Path(config_path).exists():
        logger.error(f"❌ Config file not found: {config_path}")
        return
    
    tester = MonitorTest(config_path)
    
    try:
        # 1. Test URL accessibility
        await tester.test_url_accessibility()
        
        # 2. Initialize monitor
        if await tester.test_monitor_initialization():
            # 3. Test opportunity detection
            await tester.test_opportunity_detection()
            
            # 4. Test detection patterns
            await tester.test_detection_patterns()
            
            # 5. Test data tracking
            await tester.test_data_tracking()
        
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
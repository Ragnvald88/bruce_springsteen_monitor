#!/usr/bin/env python3
"""
Comprehensive test script for ProfileManager
Tests profile creation, selection, scoring, and platform assignment
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import yaml
from typing import Dict, List, Any, Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.profiles.manager import ProfileManager
from src.profiles.utils import create_profile_manager_from_config
from src.profiles.consolidated_models import Platform, ProfileQuality, ProfileState
from src.core.advanced_profile_system import DetectionEvent, DynamicProfile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_profile_manager.log')
    ]
)
logger = logging.getLogger(__name__)

class ProfileManagerTest:
    """Test suite for ProfileManager functionality"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.results = {
            'initialization': {},
            'profile_creation': {},
            'profile_selection': {},
            'scoring_tests': {},
            'platform_assignment': {},
            'session_management': {},
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
        """Test ProfileManager initialization"""
        logger.info("\n" + "="*80)
        logger.info("🔧 TESTING PROFILE MANAGER INITIALIZATION")
        logger.info("="*80)
        
        try:
            # Test fast initialization (lazy load)
            start_time = asyncio.get_event_loop().time()
            self.profile_manager = create_profile_manager_from_config(
                self.config_path,
                config_overrides={'num_target_profiles': 10}
            )
            await self.profile_manager.initialize(lazy_load=True)
            init_time = asyncio.get_event_loop().time() - start_time
            
            self.results['initialization'] = {
                'success': True,
                'init_time': init_time,
                'lazy_load': True
            }
            
            logger.info(f"✅ ProfileManager initialized in {init_time:.2f}s (lazy mode)")
            
            # Wait a bit for background initialization
            await asyncio.sleep(2)
            
            # Check profile counts
            dynamic_count = len(self.profile_manager.dynamic_profiles)
            static_count = len(self.profile_manager.static_profiles)
            
            logger.info(f"   Dynamic profiles: {dynamic_count}")
            logger.info(f"   Static profiles: {static_count}")
            logger.info(f"   Platform pools: {list(self.profile_manager.platform_pools.keys())}")
            
            self.results['initialization']['profile_counts'] = {
                'dynamic': dynamic_count,
                'static': static_count,
                'platforms': list(self.profile_manager.platform_pools.keys())
            }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}", exc_info=True)
            self.results['initialization'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def test_profile_creation(self) -> Dict[str, Any]:
        """Test profile creation capabilities"""
        logger.info("\n" + "="*80)
        logger.info("👤 TESTING PROFILE CREATION")
        logger.info("="*80)
        
        if not hasattr(self, 'profile_manager'):
            logger.error("❌ ProfileManager not initialized")
            return {}
        
        results = {}
        
        try:
            # Test creating profiles for each platform
            platforms = [Platform.FANSALE, Platform.TICKETMASTER, Platform.VIVATICKET]
            
            for platform in platforms:
                logger.info(f"\n🔨 Creating profile for {platform.value}")
                
                try:
                    # Create a new profile
                    if hasattr(self.profile_manager, '_create_platform_optimized_profile'):
                        profile_data = await self.profile_manager._create_platform_optimized_profile(platform)
                        
                        if profile_data and 'dynamic' in profile_data:
                            dynamic_profile = profile_data['dynamic']
                            static_profile = profile_data['static']
                            
                            results[platform.value] = {
                                'success': True,
                                'profile_id': dynamic_profile.id,
                                'browser': static_profile.browser,
                                'os': static_profile.os,
                                'viewport': f"{static_profile.viewport_width}x{static_profile.viewport_height}",
                                'user_agent': static_profile.user_agent[:80] + "...",
                                'languages': static_profile.languages,
                                'timezone': static_profile.timezone
                            }
                            
                            logger.info(f"   ✅ Created profile: {dynamic_profile.id}")
                            logger.info(f"      Browser: {static_profile.browser}")
                            logger.info(f"      OS: {static_profile.os}")
                            logger.info(f"      Viewport: {static_profile.viewport_width}x{static_profile.viewport_height}")
                        else:
                            raise Exception("Profile creation returned invalid data")
                    else:
                        # Fallback: check if profiles already exist
                        existing = self.profile_manager.dynamic_profiles
                        if existing:
                            profile = existing[0]
                            results[platform.value] = {
                                'success': True,
                                'profile_id': profile.id,
                                'note': 'Using existing profile'
                            }
                            logger.info(f"   ℹ️ Using existing profile: {profile.id}")
                        else:
                            raise Exception("No profile creation method available")
                    
                except Exception as e:
                    logger.error(f"   ❌ Failed to create profile: {e}")
                    results[platform.value] = {
                        'success': False,
                        'error': str(e)
                    }
            
        except Exception as e:
            logger.error(f"❌ Profile creation test error: {e}", exc_info=True)
            self.results['errors'].append(f"Profile creation: {str(e)}")
        
        self.results['profile_creation'] = results
        return results
    
    async def test_profile_selection(self) -> Dict[str, Any]:
        """Test profile selection for platforms"""
        logger.info("\n" + "="*80)
        logger.info("🎯 TESTING PROFILE SELECTION")
        logger.info("="*80)
        
        if not hasattr(self, 'profile_manager'):
            logger.error("❌ ProfileManager not initialized")
            return {}
        
        results = {}
        
        try:
            platforms = [Platform.FANSALE, Platform.TICKETMASTER, Platform.VIVATICKET]
            
            for platform in platforms:
                logger.info(f"\n🔍 Testing selection for {platform.value}")
                
                try:
                    # Test multiple selections
                    selections = []
                    for i in range(3):
                        profile = await self.profile_manager.get_profile_for_platform(
                            platform=platform,
                            require_session=False
                        )
                        
                        if profile:
                            selections.append({
                                'attempt': i + 1,
                                'profile_id': profile.profile_id,
                                'quality': profile.quality.value if hasattr(profile, 'quality') else 'N/A',
                                'state': profile.state.value if hasattr(profile, 'state') else 'N/A'
                            })
                            logger.info(f"   ✅ Attempt {i+1}: Got profile {profile.profile_id}")
                        else:
                            logger.warning(f"   ⚠️ Attempt {i+1}: No profile available")
                    
                    results[platform.value] = {
                        'success': len(selections) > 0,
                        'selections': selections,
                        'unique_profiles': len(set(s['profile_id'] for s in selections))
                    }
                    
                except Exception as e:
                    logger.error(f"   ❌ Selection error: {e}")
                    results[platform.value] = {
                        'success': False,
                        'error': str(e)
                    }
            
        except Exception as e:
            logger.error(f"❌ Profile selection test error: {e}", exc_info=True)
            self.results['errors'].append(f"Profile selection: {str(e)}")
        
        self.results['profile_selection'] = results
        return results
    
    async def test_profile_scoring(self) -> Dict[str, Any]:
        """Test profile scoring system"""
        logger.info("\n" + "="*80)
        logger.info("📊 TESTING PROFILE SCORING")
        logger.info("="*80)
        
        if not hasattr(self, 'profile_manager'):
            logger.error("❌ ProfileManager not initialized")
            return {}
        
        results = {}
        
        try:
            # Test scoring after various events
            test_scenarios = [
                ('success', DetectionEvent.SUCCESS, "Should increase score"),
                ('rate_limit', DetectionEvent.RATE_LIMIT, "Should slightly decrease score"),
                ('hard_block', DetectionEvent.HARD_BLOCK, "Should significantly decrease score"),
                ('captcha', DetectionEvent.CAPTCHA_CHALLENGE, "Should decrease score")
            ]
            
            # Get a test profile
            test_profile = None
            if self.profile_manager.dynamic_profiles:
                test_profile = self.profile_manager.dynamic_profiles[0]
            
            if not test_profile:
                logger.error("❌ No profiles available for scoring test")
                return {}
            
            logger.info(f"🧪 Testing with profile: {test_profile.id}")
            initial_score = test_profile.calculate_quality_score()
            logger.info(f"   Initial score: {initial_score:.2f}")
            
            for scenario_name, event, description in test_scenarios:
                logger.info(f"\n📌 Scenario: {scenario_name} - {description}")
                
                # Record feedback
                await self.profile_manager.record_feedback(
                    profile_id=test_profile.id,
                    event=event,
                    platform='test',
                    metadata={'test': True}
                )
                
                # Get new score
                new_score = test_profile.calculate_quality_score()
                score_change = new_score - initial_score
                
                results[scenario_name] = {
                    'event': event.value,
                    'initial_score': initial_score,
                    'new_score': new_score,
                    'change': score_change,
                    'description': description
                }
                
                logger.info(f"   New score: {new_score:.2f} (change: {score_change:+.2f})")
                
                # Reset for next test
                initial_score = new_score
            
        except Exception as e:
            logger.error(f"❌ Scoring test error: {e}", exc_info=True)
            self.results['errors'].append(f"Scoring: {str(e)}")
        
        self.results['scoring_tests'] = results
        return results
    
    async def test_platform_assignment(self) -> Dict[str, Any]:
        """Test platform pool assignment"""
        logger.info("\n" + "="*80)
        logger.info("🎲 TESTING PLATFORM ASSIGNMENT")
        logger.info("="*80)
        
        if not hasattr(self, 'profile_manager'):
            logger.error("❌ ProfileManager not initialized")
            return {}
        
        results = {}
        
        try:
            # Check current platform assignments
            for platform, profile_ids in self.profile_manager.platform_pools.items():
                logger.info(f"\n📍 Platform: {platform}")
                logger.info(f"   Assigned profiles: {len(profile_ids)}")
                
                results[platform] = {
                    'profile_count': len(profile_ids),
                    'profile_ids': profile_ids[:3]  # Show first 3
                }
                
                # Verify profiles exist
                valid_count = 0
                for profile_id in profile_ids:
                    # Check in dynamic profiles
                    if any(p.id == profile_id for p in self.profile_manager.dynamic_profiles):
                        valid_count += 1
                
                results[platform]['valid_profiles'] = valid_count
                results[platform]['all_valid'] = valid_count == len(profile_ids)
                
                logger.info(f"   Valid profiles: {valid_count}/{len(profile_ids)}")
                
                if not results[platform]['all_valid']:
                    logger.warning(f"   ⚠️ Some profile IDs don't match existing profiles")
            
        except Exception as e:
            logger.error(f"❌ Platform assignment test error: {e}", exc_info=True)
            self.results['errors'].append(f"Platform assignment: {str(e)}")
        
        self.results['platform_assignment'] = results
        return results
    
    async def test_session_management(self) -> Dict[str, Any]:
        """Test session backup and restoration"""
        logger.info("\n" + "="*80)
        logger.info("💾 TESTING SESSION MANAGEMENT")
        logger.info("="*80)
        
        if not hasattr(self, 'profile_manager'):
            logger.error("❌ ProfileManager not initialized")
            return {}
        
        results = {}
        
        try:
            session_manager = self.profile_manager.session_manager
            
            # Test session backup
            logger.info("\n📦 Testing session backup...")
            test_session_data = {
                'cookies': [{'name': 'test', 'value': 'cookie'}],
                'localStorage': {'test': 'data'},
                'sessionStorage': {'session': 'data'}
            }
            
            test_profile_id = 'test_profile_123'
            test_platform = 'test_platform'
            
            # Save session
            saved = await session_manager.save_session(
                profile_id=test_profile_id,
                platform=test_platform,
                session_data=test_session_data
            )
            
            results['backup'] = {
                'success': saved,
                'profile_id': test_profile_id,
                'platform': test_platform
            }
            
            if saved:
                logger.info("   ✅ Session backup successful")
                
                # Test session restoration
                logger.info("\n📂 Testing session restoration...")
                restored = await session_manager.restore_session(
                    profile_id=test_profile_id,
                    platform=test_platform
                )
                
                results['restore'] = {
                    'success': restored is not None,
                    'data_matches': restored == test_session_data if restored else False
                }
                
                if restored:
                    logger.info("   ✅ Session restoration successful")
                    logger.info(f"   Data matches: {restored == test_session_data}")
                else:
                    logger.warning("   ⚠️ Session restoration returned None")
            else:
                logger.warning("   ⚠️ Session backup failed")
            
            # Check session directory
            session_dir = Path(session_manager.backup_dir)
            if session_dir.exists():
                session_files = list(session_dir.glob("*.json"))
                results['session_files'] = {
                    'directory': str(session_dir),
                    'file_count': len(session_files),
                    'total_size_kb': sum(f.stat().st_size for f in session_files) / 1024
                }
                logger.info(f"\n📁 Session directory: {session_dir}")
                logger.info(f"   Files: {len(session_files)}")
                logger.info(f"   Total size: {results['session_files']['total_size_kb']:.2f} KB")
            
        except Exception as e:
            logger.error(f"❌ Session management test error: {e}", exc_info=True)
            self.results['errors'].append(f"Session management: {str(e)}")
        
        self.results['session_management'] = results
        return results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("📋 PROFILE MANAGER TEST REPORT")
        logger.info("="*80)
        
        # Initialization summary
        init_result = self.results.get('initialization', {})
        if init_result.get('success'):
            logger.info(f"\n✅ Initialization: Success ({init_result.get('init_time', 0):.2f}s)")
            if 'profile_counts' in init_result:
                counts = init_result['profile_counts']
                logger.info(f"   Dynamic profiles: {counts.get('dynamic', 0)}")
                logger.info(f"   Static profiles: {counts.get('static', 0)}")
        else:
            logger.info(f"\n❌ Initialization: Failed - {init_result.get('error', 'Unknown error')}")
        
        # Profile creation summary
        if self.results.get('profile_creation'):
            logger.info("\n👤 Profile Creation:")
            for platform, result in self.results['profile_creation'].items():
                status = "✅" if result.get('success') else "❌"
                logger.info(f"   {status} {platform}")
                if not result.get('success'):
                    logger.info(f"      Error: {result.get('error', 'Unknown')}")
        
        # Profile selection summary
        if self.results.get('profile_selection'):
            logger.info("\n🎯 Profile Selection:")
            for platform, result in self.results['profile_selection'].items():
                status = "✅" if result.get('success') else "❌"
                unique = result.get('unique_profiles', 0)
                logger.info(f"   {status} {platform}: {unique} unique profiles selected")
        
        # Scoring summary
        if self.results.get('scoring_tests'):
            logger.info("\n📊 Profile Scoring:")
            for scenario, result in self.results['scoring_tests'].items():
                change = result.get('change', 0)
                direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                logger.info(f"   {direction} {scenario}: {change:+.2f} score change")
        
        # Platform assignment summary
        if self.results.get('platform_assignment'):
            logger.info("\n🎲 Platform Assignment:")
            for platform, result in self.results['platform_assignment'].items():
                count = result.get('profile_count', 0)
                valid = result.get('all_valid', False)
                status = "✅" if valid else "⚠️"
                logger.info(f"   {status} {platform}: {count} profiles")
        
        # Session management summary
        if self.results.get('session_management'):
            session = self.results['session_management']
            backup_ok = session.get('backup', {}).get('success', False)
            restore_ok = session.get('restore', {}).get('success', False)
            logger.info("\n💾 Session Management:")
            logger.info(f"   Backup: {'✅' if backup_ok else '❌'}")
            logger.info(f"   Restore: {'✅' if restore_ok else '❌'}")
        
        # Errors summary
        if self.results['errors']:
            logger.info("\n❌ Errors encountered:")
            for error in self.results['errors']:
                logger.info(f"   - {error}")
        
        # Save results
        report_path = "test_profile_manager_report.yaml"
        with open(report_path, 'w') as f:
            yaml.dump(self.results, f, default_flow_style=False)
        logger.info(f"\n📄 Full report saved to: {report_path}")

async def main():
    """Run all profile manager tests"""
    config_path = "config/config.yaml"
    
    if not Path(config_path).exists():
        logger.error(f"❌ Config file not found: {config_path}")
        return
    
    tester = ProfileManagerTest(config_path)
    
    try:
        # Run tests in sequence
        if await tester.test_initialization():
            await tester.test_profile_creation()
            await tester.test_profile_selection()
            await tester.test_profile_scoring()
            await tester.test_platform_assignment()
            await tester.test_session_management()
        
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
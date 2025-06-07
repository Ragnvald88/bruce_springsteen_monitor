#!/usr/bin/env python3
"""
Master test runner for Bruce Springsteen ticket monitoring system
Runs all test suites and generates a comprehensive bug report
"""

import asyncio
import logging
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, List, Any, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('master_test_report.log')
    ]
)
logger = logging.getLogger(__name__)

class MasterTestRunner:
    """Runs all test suites and collects results"""
    
    def __init__(self):
        self.test_suites = [
            {
                'name': 'Monitor Functionality',
                'script': 'test_monitor_functionality.py',
                'description': 'Tests URL monitoring, opportunity detection, and platform patterns'
            },
            {
                'name': 'Profile Manager',
                'script': 'test_profile_manager.py',
                'description': 'Tests profile creation, selection, scoring, and session management'
            },
            {
                'name': 'Strike Force',
                'script': 'test_strike_force.py',
                'description': 'Tests strike execution, profile coordination, and platform strategies'
            },
            {
                'name': 'Full Integration',
                'script': 'test_full_integration.py',
                'description': 'Tests complete monitoring flow from detection to strike'
            }
        ]
        
        self.results = {}
        self.bugs_found = []
        self.warnings = []
        self.recommendations = []
    
    async def run_test_suite(self, suite: Dict[str, str]) -> Tuple[bool, Dict[str, Any]]:
        """Run a single test suite"""
        script_path = Path(suite['script'])
        
        if not script_path.exists():
            logger.error(f"❌ Test script not found: {script_path}")
            return False, {'error': 'Script not found'}
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🧪 Running: {suite['name']}")
        logger.info(f"   Script: {suite['script']}")
        logger.info(f"   Description: {suite['description']}")
        logger.info("="*80)
        
        try:
            # Run the test script
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time
            
            # Check for errors
            success = process.returncode == 0
            
            # Try to load the test report
            report_data = {}
            report_files = {
                'test_monitor_functionality.py': 'test_monitor_report.yaml',
                'test_profile_manager.py': 'test_profile_manager_report.yaml',
                'test_strike_force.py': 'test_strike_force_report.yaml',
                'test_full_integration.py': 'test_full_integration_report.yaml'
            }
            
            report_file = report_files.get(suite['script'])
            if report_file and Path(report_file).exists():
                with open(report_file, 'r') as f:
                    report_data = yaml.safe_load(f) or {}
            
            result = {
                'success': success,
                'execution_time': execution_time,
                'return_code': process.returncode,
                'report_data': report_data,
                'stdout_lines': stdout.decode('utf-8').count('\n') if stdout else 0,
                'stderr_content': stderr.decode('utf-8') if stderr else ''
            }
            
            if success:
                logger.info(f"✅ Test completed successfully ({execution_time:.2f}s)")
            else:
                logger.error(f"❌ Test failed with return code: {process.returncode}")
                if stderr:
                    logger.error(f"   Error output: {stderr.decode('utf-8')[:200]}...")
            
            return success, result
            
        except Exception as e:
            logger.error(f"❌ Failed to run test: {e}")
            return False, {'error': str(e)}
    
    def analyze_results(self):
        """Analyze test results and identify bugs"""
        logger.info("\n" + "="*80)
        logger.info("🔍 ANALYZING TEST RESULTS")
        logger.info("="*80)
        
        # Analyze Monitor Test Results
        monitor_results = self.results.get('Monitor Functionality', {}).get('report_data', {})
        if monitor_results:
            # Check URL accessibility
            url_tests = monitor_results.get('url_tests', {})
            for platform, result in url_tests.items():
                if not result.get('success', False):
                    self.bugs_found.append({
                        'component': 'URL Monitoring',
                        'platform': platform,
                        'issue': f"URL not accessible: {result.get('error', 'Unknown error')}",
                        'severity': 'HIGH',
                        'url': result.get('url', 'N/A')
                    })
            
            # Check parsing
            parsing_tests = monitor_results.get('parsing_tests', {})
            for platform, result in parsing_tests.items():
                if 'error' in result:
                    self.bugs_found.append({
                        'component': 'Opportunity Detection',
                        'platform': platform,
                        'issue': f"Parsing error: {result['error']}",
                        'severity': 'CRITICAL'
                    })
                elif result.get('opportunities_found', 0) == 0:
                    self.warnings.append({
                        'component': 'Opportunity Detection',
                        'platform': platform,
                        'issue': 'No opportunities detected - patterns may need updating',
                        'severity': 'MEDIUM'
                    })
        
        # Analyze Profile Manager Results
        profile_results = self.results.get('Profile Manager', {}).get('report_data', {})
        if profile_results:
            # Check initialization
            init_result = profile_results.get('initialization', {})
            if not init_result.get('success', False):
                self.bugs_found.append({
                    'component': 'Profile Manager',
                    'issue': f"Initialization failed: {init_result.get('error', 'Unknown')}",
                    'severity': 'CRITICAL'
                })
            
            # Check profile counts
            if 'profile_counts' in init_result:
                counts = init_result['profile_counts']
                if counts.get('dynamic', 0) == 0:
                    self.bugs_found.append({
                        'component': 'Profile Manager',
                        'issue': 'No dynamic profiles created',
                        'severity': 'HIGH'
                    })
        
        # Analyze Strike Force Results
        strike_results = self.results.get('Strike Force', {}).get('report_data', {})
        if strike_results:
            # Check platform strategies
            strategies = strike_results.get('platform_strategies', {})
            for platform, result in strategies.items():
                if not result.get('has_strategy', False):
                    self.bugs_found.append({
                        'component': 'Strike Force',
                        'platform': platform,
                        'issue': 'Missing platform strategy implementation',
                        'severity': 'HIGH'
                    })
        
        # Analyze Integration Results
        integration_results = self.results.get('Full Integration', {}).get('report_data', {})
        if integration_results:
            # Check subsystem initialization
            subsystem_init = integration_results.get('subsystem_init', {})
            if subsystem_init.get('subsystems'):
                for name, initialized in subsystem_init['subsystems'].items():
                    if not initialized:
                        self.bugs_found.append({
                            'component': 'Orchestrator',
                            'subsystem': name,
                            'issue': 'Subsystem failed to initialize',
                            'severity': 'CRITICAL'
                        })
        
        # Generate recommendations
        self._generate_recommendations()
    
    def _generate_recommendations(self):
        """Generate recommendations based on findings"""
        # Check for critical bugs
        critical_bugs = [b for b in self.bugs_found if b.get('severity') == 'CRITICAL']
        if critical_bugs:
            self.recommendations.append({
                'priority': 'URGENT',
                'action': 'Fix critical initialization issues before running the system',
                'details': f'{len(critical_bugs)} critical bugs found'
            })
        
        # Check for URL accessibility issues
        url_bugs = [b for b in self.bugs_found if 'URL not accessible' in b.get('issue', '')]
        if url_bugs:
            self.recommendations.append({
                'priority': 'HIGH',
                'action': 'Verify platform URLs are correct and accessible',
                'details': f'{len(url_bugs)} URLs are not accessible'
            })
        
        # Check for pattern issues
        pattern_warnings = [w for w in self.warnings if 'patterns may need updating' in w.get('issue', '')]
        if pattern_warnings:
            self.recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Update detection patterns for platforms with no detections',
                'details': f'{len(pattern_warnings)} platforms need pattern updates'
            })
        
        # Profile recommendations
        if any('dynamic profiles' in str(b.get('issue', '')) for b in self.bugs_found):
            self.recommendations.append({
                'priority': 'HIGH',
                'action': 'Check profile creation logic and ensure profiles are being generated',
                'details': 'Profile pool is empty or not initializing properly'
            })
    
    def generate_master_report(self):
        """Generate comprehensive master report"""
        logger.info("\n" + "="*80)
        logger.info("📋 MASTER TEST REPORT")
        logger.info("="*80)
        
        # Summary
        total_tests = len(self.test_suites)
        successful_tests = sum(1 for name, result in self.results.items() if result.get('success', False))
        
        logger.info(f"\n📊 Test Summary:")
        logger.info(f"   Total test suites: {total_tests}")
        logger.info(f"   Successful: {successful_tests}")
        logger.info(f"   Failed: {total_tests - successful_tests}")
        logger.info(f"   Bugs found: {len(self.bugs_found)}")
        logger.info(f"   Warnings: {len(self.warnings)}")
        
        # Individual test results
        logger.info(f"\n🧪 Test Suite Results:")
        for suite in self.test_suites:
            result = self.results.get(suite['name'], {})
            if result:
                status = "✅" if result.get('success', False) else "❌"
                time_str = f"({result.get('execution_time', 0):.2f}s)" if 'execution_time' in result else ""
                logger.info(f"   {status} {suite['name']} {time_str}")
                if 'error' in result:
                    logger.info(f"      Error: {result['error']}")
        
        # Bugs found
        if self.bugs_found:
            logger.info(f"\n🐛 BUGS FOUND ({len(self.bugs_found)}):")
            
            # Group by severity
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                severity_bugs = [b for b in self.bugs_found if b.get('severity') == severity]
                if severity_bugs:
                    logger.info(f"\n   {severity} ({len(severity_bugs)}):")
                    for bug in severity_bugs:
                        component = bug.get('component', 'Unknown')
                        issue = bug.get('issue', 'Unknown issue')
                        platform = bug.get('platform', '')
                        if platform:
                            logger.info(f"   - [{component}] {platform}: {issue}")
                        else:
                            logger.info(f"   - [{component}] {issue}")
        
        # Warnings
        if self.warnings:
            logger.info(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                component = warning.get('component', 'Unknown')
                issue = warning.get('issue', 'Unknown issue')
                platform = warning.get('platform', '')
                if platform:
                    logger.info(f"   - [{component}] {platform}: {issue}")
                else:
                    logger.info(f"   - [{component}] {issue}")
        
        # Recommendations
        if self.recommendations:
            logger.info(f"\n💡 RECOMMENDATIONS:")
            for rec in sorted(self.recommendations, key=lambda x: ['URGENT', 'HIGH', 'MEDIUM', 'LOW'].index(x.get('priority', 'LOW'))):
                priority = rec.get('priority', 'MEDIUM')
                action = rec.get('action', '')
                details = rec.get('details', '')
                logger.info(f"\n   [{priority}] {action}")
                if details:
                    logger.info(f"   Details: {details}")
        
        # System readiness
        critical_count = len([b for b in self.bugs_found if b.get('severity') == 'CRITICAL'])
        high_count = len([b for b in self.bugs_found if b.get('severity') == 'HIGH'])
        
        logger.info(f"\n🚦 SYSTEM READINESS:")
        if critical_count > 0:
            logger.info("   ❌ NOT READY - Critical issues must be fixed")
        elif high_count > 0:
            logger.info("   ⚠️ PARTIALLY READY - High priority issues should be addressed")
        else:
            logger.info("   ✅ READY - System can be run with current configuration")
        
        # Save comprehensive report
        master_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'successful': successful_tests,
                'failed': total_tests - successful_tests,
                'bugs_found': len(self.bugs_found),
                'warnings': len(self.warnings)
            },
            'test_results': self.results,
            'bugs': self.bugs_found,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'system_ready': critical_count == 0
        }
        
        with open('master_test_report.yaml', 'w') as f:
            yaml.dump(master_report, f, default_flow_style=False)
        
        logger.info(f"\n📄 Detailed report saved to: master_test_report.yaml")
        logger.info(f"📄 Log file: master_test_report.log")

async def main():
    """Run all tests and generate master report"""
    runner = MasterTestRunner()
    
    logger.info("🚀 BRUCE SPRINGSTEEN TICKET MONITOR - COMPREHENSIVE TEST SUITE")
    logger.info(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all test suites
    for suite in runner.test_suites:
        success, result = await runner.run_test_suite(suite)
        runner.results[suite['name']] = result
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    # Analyze results
    runner.analyze_results()
    
    # Generate master report
    runner.generate_master_report()
    
    logger.info(f"\n✨ Test suite completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
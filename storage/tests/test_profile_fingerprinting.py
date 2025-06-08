#!/usr/bin/env python3
"""
Profile Rotation and Fingerprinting Test
Tests uniqueness and effectiveness of profile fingerprints
"""

import asyncio
import os
import sys
import json
import hashlib
from datetime import datetime
from collections import defaultdict

# Add src to path
sys.path.insert(0, 'src')

from playwright.async_api import async_playwright
from stealth.cdp_stealth import CDPStealthEngine
from profiles.manager import ProfileManager

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('FingerprintTest')


async def extract_fingerprint(page) -> dict:
    """Extract comprehensive browser fingerprint"""
    fingerprint = await page.evaluate("""
        () => {
            // Canvas fingerprint
            const getCanvasFingerprint = () => {
                try {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    ctx.textBaseline = 'top';
                    ctx.font = '14px "Arial"';
                    ctx.fillStyle = '#f60';
                    ctx.fillRect(125, 1, 62, 20);
                    ctx.fillStyle = '#069';
                    ctx.fillText('Browser fingerprint test', 2, 15);
                    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
                    ctx.fillText('Browser fingerprint test', 4, 17);
                    return canvas.toDataURL();
                } catch (e) {
                    return 'error';
                }
            };
            
            // WebGL fingerprint
            const getWebGLFingerprint = () => {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return 'not supported';
                    
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    return {
                        vendor: gl.getParameter(debugInfo ? debugInfo.UNMASKED_VENDOR_WEBGL : gl.VENDOR),
                        renderer: gl.getParameter(debugInfo ? debugInfo.UNMASKED_RENDERER_WEBGL : gl.RENDERER)
                    };
                } catch (e) {
                    return 'error';
                }
            };
            
            // Audio fingerprint
            const getAudioFingerprint = () => {
                try {
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (!AudioContext) return 'not supported';
                    
                    const context = new AudioContext();
                    const oscillator = context.createOscillator();
                    const analyser = context.createAnalyser();
                    const gain = context.createGain();
                    const scriptProcessor = context.createScriptProcessor(4096, 1, 1);
                    
                    oscillator.type = 'triangle';
                    oscillator.frequency.value = 10000;
                    gain.gain.value = 0;
                    
                    oscillator.connect(analyser);
                    analyser.connect(scriptProcessor);
                    scriptProcessor.connect(gain);
                    gain.connect(context.destination);
                    
                    oscillator.start(0);
                    
                    let fingerprint = [];
                    scriptProcessor.onaudioprocess = function(event) {
                        const output = event.inputBuffer.getChannelData(0);
                        fingerprint = Array.from(output.slice(0, 100));
                    };
                    
                    return fingerprint.slice(0, 30).join(',');
                } catch (e) {
                    return 'error';
                }
            };
            
            return {
                // Basic properties
                userAgent: navigator.userAgent,
                language: navigator.language,
                languages: navigator.languages,
                platform: navigator.platform,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                
                // Screen properties
                screen: {
                    width: screen.width,
                    height: screen.height,
                    colorDepth: screen.colorDepth,
                    pixelDepth: screen.pixelDepth,
                    availWidth: screen.availWidth,
                    availHeight: screen.availHeight
                },
                
                // Time zone
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                timezoneOffset: new Date().getTimezoneOffset(),
                
                // WebDriver detection
                webdriver: navigator.webdriver,
                
                // Chrome specific
                chrome: !!window.chrome,
                chromeRuntime: !!window.chrome?.runtime,
                
                // Plugins
                plugins: Array.from(navigator.plugins).map(p => ({
                    name: p.name,
                    filename: p.filename,
                    length: p.length
                })),
                
                // Media devices
                mediaDevices: await (async () => {
                    try {
                        const devices = await navigator.mediaDevices.enumerateDevices();
                        return devices.map(d => d.kind);
                    } catch (e) {
                        return 'error';
                    }
                })(),
                
                // Canvas fingerprint
                canvas: getCanvasFingerprint().slice(-50),
                
                // WebGL
                webgl: getWebGLFingerprint(),
                
                // Audio
                audio: getAudioFingerprint(),
                
                // Battery API
                battery: await (async () => {
                    try {
                        const battery = await navigator.getBattery();
                        return {
                            charging: battery.charging,
                            level: battery.level
                        };
                    } catch (e) {
                        return 'not supported';
                    }
                })(),
                
                // Connection
                connection: {
                    effectiveType: navigator.connection?.effectiveType,
                    rtt: navigator.connection?.rtt,
                    downlink: navigator.connection?.downlink
                },
                
                // Permissions
                permissions: {
                    notifications: await (async () => {
                        try {
                            const result = await navigator.permissions.query({name: 'notifications'});
                            return result.state;
                        } catch (e) {
                            return 'error';
                        }
                    })()
                }
            };
        }
    """)
    
    return fingerprint


async def test_profile_uniqueness():
    """Test if profiles have unique fingerprints"""
    logger.info("🔍 Testing profile fingerprint uniqueness...")
    
    profile_manager = ProfileManager()
    all_profile_ids = list(profile_manager.profiles.keys())[:10]  # Test first 10
    
    fingerprints = {}
    fingerprint_hashes = defaultdict(list)
    
    async with async_playwright() as p:
        browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
        
        for profile_id in all_profile_ids:
            profile = profile_manager.get_profile(profile_id)
            if not profile:
                continue
                
            logger.info(f"\nProfile: {profile_id}")
            
            # Create context with profile settings
            context_params = profile.get_context_params()
            if 'proxy' in context_params:
                # Remove proxy for this test
                del context_params['proxy']
                
            context = await browser.new_context(**context_params)
            page = await context.new_page()
            await CDPStealthEngine.apply_page_stealth(page)
            
            # Navigate to fingerprinting page
            await page.goto('data:text/html,<h1>Fingerprint Test</h1>')
            
            # Extract fingerprint
            fingerprint = await extract_fingerprint(page)
            fingerprints[profile_id] = fingerprint
            
            # Create hash for comparison
            fp_string = json.dumps(fingerprint, sort_keys=True)
            fp_hash = hashlib.md5(fp_string.encode()).hexdigest()[:8]
            fingerprint_hashes[fp_hash].append(profile_id)
            
            logger.info(f"  User Agent: {fingerprint['userAgent'][:50]}...")
            logger.info(f"  Screen: {fingerprint['screen']['width']}x{fingerprint['screen']['height']}")
            logger.info(f"  Timezone: {fingerprint['timezone']}")
            logger.info(f"  Canvas hash: {fingerprint['canvas'][:20]}...")
            logger.info(f"  Fingerprint hash: {fp_hash}")
            
            await context.close()
            
        await browser.close()
        
    # Analyze uniqueness
    logger.info("\n📊 Fingerprint Analysis:")
    
    total_profiles = len(fingerprints)
    unique_hashes = len(fingerprint_hashes)
    
    logger.info(f"Total profiles tested: {total_profiles}")
    logger.info(f"Unique fingerprints: {unique_hashes}")
    logger.info(f"Uniqueness rate: {unique_hashes/total_profiles*100:.1f}%")
    
    # Find duplicates
    duplicates = {h: profiles for h, profiles in fingerprint_hashes.items() if len(profiles) > 1}
    if duplicates:
        logger.warning("\n⚠️ Duplicate fingerprints found:")
        for hash_val, profiles in duplicates.items():
            logger.warning(f"  Hash {hash_val}: {', '.join(profiles)}")
    else:
        logger.info("\n✅ All profiles have unique fingerprints!")
        
    return fingerprints, fingerprint_hashes


async def test_rotation_effectiveness():
    """Test profile rotation effectiveness"""
    logger.info("\n🔄 Testing profile rotation effectiveness...")
    
    test_url = "https://www.fansale.it"
    results = []
    
    profile_manager = ProfileManager()
    profiles_to_test = list(profile_manager.profiles.keys())[:5]
    
    async with async_playwright() as p:
        for attempt in range(2):  # Test each profile twice
            logger.info(f"\n--- Rotation {attempt + 1} ---")
            
            for profile_id in profiles_to_test:
                profile = profile_manager.get_profile(profile_id)
                if not profile:
                    continue
                    
                browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
                context = await CDPStealthEngine.create_stealth_context(browser, None)
                page = await context.new_page()
                
                try:
                    response = await page.goto(test_url, timeout=30000)
                    content = await page.content()
                    
                    is_blocked = 'blocked' in content.lower() or response.status == 403
                    
                    result = {
                        'profile': profile_id,
                        'attempt': attempt + 1,
                        'status': response.status,
                        'blocked': is_blocked
                    }
                    results.append(result)
                    
                    logger.info(f"  {profile_id}: {'❌ Blocked' if is_blocked else '✅ Success'} (Status: {response.status})")
                    
                except Exception as e:
                    logger.error(f"  {profile_id}: Error - {str(e)[:50]}")
                    results.append({
                        'profile': profile_id,
                        'attempt': attempt + 1,
                        'error': str(e)
                    })
                    
                finally:
                    await browser.close()
                    await asyncio.sleep(1)  # Brief delay between profiles
                    
    # Analyze rotation results
    logger.info("\n📈 Rotation Analysis:")
    
    success_by_profile = defaultdict(int)
    total_by_profile = defaultdict(int)
    
    for result in results:
        profile = result['profile']
        total_by_profile[profile] += 1
        if not result.get('blocked', True) and not result.get('error'):
            success_by_profile[profile] += 1
            
    for profile in profiles_to_test:
        success_rate = success_by_profile[profile] / total_by_profile[profile] * 100
        logger.info(f"  {profile}: {success_rate:.0f}% success rate")
        
    return results


async def main():
    """Run fingerprinting tests"""
    logger.info("="*60)
    logger.info("🔍 PROFILE FINGERPRINTING & ROTATION TEST")
    logger.info("="*60)
    
    # Test 1: Profile uniqueness
    fingerprints, hashes = await test_profile_uniqueness()
    
    # Test 2: Rotation effectiveness
    rotation_results = await test_rotation_effectiveness()
    
    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'fingerprint_test': {
            'total_profiles': len(fingerprints),
            'unique_fingerprints': len(hashes),
            'uniqueness_rate': len(hashes) / len(fingerprints) * 100 if fingerprints else 0,
            'duplicate_groups': [list(profiles) for profiles in hashes.values() if len(profiles) > 1]
        },
        'rotation_test': {
            'results': rotation_results,
            'success_rate': sum(1 for r in rotation_results if not r.get('blocked', True)) / len(rotation_results) * 100 if rotation_results else 0
        },
        'sample_fingerprints': {k: v for k, v in list(fingerprints.items())[:3]}  # Include 3 samples
    }
    
    # Save report
    with open('fingerprint_report.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info("\n" + "="*60)
    logger.info("📊 FINGERPRINTING TEST SUMMARY")
    logger.info("="*60)
    
    logger.info(f"\n✅ Profile Uniqueness: {report['fingerprint_test']['uniqueness_rate']:.1f}%")
    logger.info(f"✅ Rotation Success Rate: {report['rotation_test']['success_rate']:.1f}%")
    
    if report['fingerprint_test']['duplicate_groups']:
        logger.warning("\n⚠️ Found duplicate fingerprints - profiles may be too similar")
    else:
        logger.info("\n✅ All profiles have unique fingerprints")
        
    logger.info("\n📁 Full report saved to: fingerprint_report.json")


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
🔍 StealthMaster AI - FanSale Access Analysis
Test different approaches to access FanSale
"""

import asyncio
import httpx
import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

async def test_fansale_access():
    print("🔍 FanSale Access Analysis")
    print("=" * 50)
    
    fansale_urls = [
        ("Main Site", "https://www.fansale.it/"),
        ("Target Event", "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"),
        ("Login Page", "https://www.fansale.it/login"),
        ("API Endpoint", "https://www.fansale.it/api/"),
    ]
    
    # Test 1: Basic connectivity
    print("🌐 Testing Basic Connectivity...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        for name, url in fansale_urls:
            try:
                start_time = time.time()
                response = await client.get(url)
                duration = time.time() - start_time
                
                print(f"  {name}: {response.status_code} ({duration*1000:.0f}ms)")
                print(f"    Content-Length: {len(response.content)} bytes")
                
                # Check for blocking indicators
                content_lower = response.text.lower()
                blocking_terms = [
                    'cloudflare', 'access denied', 'blocked', 'captcha', 
                    'bot protection', 'please wait', 'checking your browser'
                ]
                found_blocks = [term for term in blocking_terms if term in content_lower]
                
                if found_blocks:
                    print(f"    🚫 Blocking detected: {found_blocks}")
                else:
                    print(f"    ✅ No obvious blocking")
                
                # Check for login requirements
                login_indicators = ['login', 'sign in', 'accedi', 'registrati']
                found_login = [term for term in login_indicators if term in content_lower]
                
                if found_login:
                    print(f"    🔐 Login indicators: {found_login}")
                
            except asyncio.TimeoutError:
                print(f"  {name}: ⏰ TIMEOUT (likely blocked)")
            except Exception as e:
                print(f"  {name}: ❌ ERROR - {type(e).__name__}: {str(e)[:50]}...")
            
            await asyncio.sleep(1)  # Be respectful
    
    # Test 2: With Italian headers
    print("\n🇮🇹 Testing with Italian Headers...")
    italian_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }
    
    async with httpx.AsyncClient(headers=italian_headers, timeout=15.0) as client:
        try:
            response = await client.get("https://www.fansale.it/")
            print(f"  Main site with IT headers: {response.status_code}")
            print(f"  Content-Length: {len(response.content)} bytes")
            
            # Check if we can access the specific event page
            event_response = await client.get("https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
            print(f"  Event page with IT headers: {event_response.status_code}")
            
        except Exception as e:
            print(f"  ❌ Italian headers test failed: {str(e)[:50]}...")
    
    # Test 3: Check if we can reach login page
    print("\n🔐 Testing Login Page Access...")
    async with httpx.AsyncClient(headers=italian_headers, timeout=15.0) as client:
        try:
            login_response = await client.get("https://www.fansale.it/login")
            print(f"  Login page: {login_response.status_code}")
            
            if login_response.status_code == 200:
                # Look for login form elements
                login_content = login_response.text.lower()
                form_elements = ['email', 'password', 'username', 'form', 'input']
                found_elements = [elem for elem in form_elements if elem in login_content]
                print(f"  🔍 Form elements found: {found_elements}")
                
                # Check for CSRF tokens or other protection
                if 'csrf' in login_content or '_token' in login_content:
                    print(f"  🛡️  CSRF protection detected")
                
        except Exception as e:
            print(f"  ❌ Login page test failed: {str(e)[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_fansale_access())
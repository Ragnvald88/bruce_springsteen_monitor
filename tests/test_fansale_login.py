#!/usr/bin/env python3
"""Test script specifically for Fansale login with enhanced stealth."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.stealth.nodriver_core import nodriver_core
from src.stealth.akamai_bypass import AkamaiBypass
from src.config import load_settings
from rich.console import Console

console = Console()


async def test_fansale_login():
    """Test Fansale login with maximum stealth."""
    console.print("[cyan]🎯 Testing Fansale login with enhanced stealth...[/cyan]")
    
    # Load settings
    settings = load_settings()
    
    # Get proxy if configured
    proxy_config = None
    if settings.proxy_settings.enabled and settings.proxy_settings.primary_pool:
        proxy = settings.proxy_settings.primary_pool[0]
        proxy_url = f"{proxy.type}://{proxy.host}:{proxy.port}"
        proxy_config = {
            'server': proxy_url,
            'username': proxy.username,
            'password': proxy.password
        }
        console.print(f"[cyan]🌐 Using proxy: {proxy.host}:{proxy.port}[/cyan]")
    else:
        console.print("[yellow]⚠️  No proxy configured - using direct connection[/yellow]")
    
    try:
        # Create stealth browser using undetected-chromedriver
        console.print("[cyan]🚀 Launching stealth browser...[/cyan]")
        browser_data = await nodriver_core.create_stealth_browser(
            headless=False,
            proxy=proxy_config
        )
        
        if 'driver' in browser_data:
            driver = browser_data['driver']
            console.print("[green]✅ Browser launched successfully[/green]")
        else:
            console.print("[red]❌ Failed to get driver from browser data[/red]")
            console.print(f"[yellow]Browser data keys: {browser_data.keys()}[/yellow]")
            return
        
        # Navigate to Fansale
        console.print("[cyan]📍 Navigating to Fansale...[/cyan]")
        driver.get("https://www.fansale.de")
        
        # Wait for page to load
        await asyncio.sleep(5)
        
        # Apply additional Akamai bypass using Playwright-style injection
        console.print("[cyan]🛡️ Applying Akamai bypass...[/cyan]")
        try:
            driver.execute_script("""
                // Enhanced Akamai bypass for Fansale
                window._abck = window._abck || {};
                window.bmak = window.bmak || {};
                window.bmak.js_post = false;
                window.bmak.fpcf = { f: () => 0, s: () => {} };
                window.bmak.sensor_data = '-1';
                
                // Fix permissions if not already fixed
                if (navigator.permissions && navigator.permissions.query) {
                    const originalQuery = navigator.permissions.query;
                    if (originalQuery.toString().indexOf('[native code]') !== -1) {
                        navigator.permissions.query = function(params) {
                            if (params.name === 'notifications') {
                                return Promise.resolve({ state: 'prompt', onchange: null });
                            }
                            return originalQuery.apply(this, arguments);
                        };
                    }
                }
                
                // Add mouse movement simulation
                document.addEventListener('mousemove', function(e) {
                    window.lastMouseX = e.clientX;
                    window.lastMouseY = e.clientY;
                });
                
                console.log('Akamai bypass applied');
            """)
            console.print("[green]✓ Akamai bypass applied successfully[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not apply full bypass: {e}[/yellow]")
        
        # Check if we're on the main page
        current_url = driver.current_url
        console.print(f"[cyan]📍 Current URL: {current_url}[/cyan]")
        
        # Try to find and click login button
        console.print("[cyan]🔍 Looking for login button...[/cyan]")
        
        # Common selectors for login buttons on Fansale
        login_selectors = [
            "a[href*='login']",
            "a[href*='Login']",
            "a[href*='anmelden']",
            "[class*='login']",
            "[id*='login']",
            "button[class*='login']",
            "span[class*='login']"
        ]
        
        # Also try with text content
        login_texts = ['Login', 'Anmelden', 'Sign in', 'Log in']
        
        login_found = False
        
        # First try CSS selectors
        for selector in login_selectors:
            try:
                from selenium.webdriver.common.by import By
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    console.print(f"[cyan]Found {len(elements)} element(s) with selector: {selector}[/cyan]")
                    elements[0].click()
                    await asyncio.sleep(2)
                    if 'login' in driver.current_url.lower() or 'anmelden' in driver.current_url.lower():
                        login_found = True
                        console.print(f"[green]✅ Clicked login button successfully[/green]")
                        break
            except Exception as e:
                console.print(f"[dim]Selector {selector} failed: {e}[/dim]")
                continue
        
        # If not found, try finding by text
        if not login_found:
            for text in login_texts:
                try:
                    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                    if elements:
                        console.print(f"[cyan]Found element with text: {text}[/cyan]")
                        elements[0].click()
                        await asyncio.sleep(2)
                        if 'login' in driver.current_url.lower() or 'anmelden' in driver.current_url.lower():
                            login_found = True
                            console.print(f"[green]✅ Clicked login button by text[/green]")
                            break
                except:
                    continue
        
        if not login_found:
            console.print("[yellow]⚠️  Could not find login button automatically[/yellow]")
            console.print("[cyan]Please navigate to login page manually...[/cyan]")
        
        # Keep browser open for manual testing
        console.print("\n[green]✅ Browser is ready for testing[/green]")
        console.print("[yellow]Instructions:[/yellow]")
        console.print("1. Navigate to the login page if not already there")
        console.print("2. Try logging in with your credentials")
        console.print("3. Check if you get blocked or can login successfully")
        console.print("\n[cyan]Press Ctrl+C when done testing...[/cyan]")
        
        # Keep the browser open
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Test interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        if 'driver' in locals():
            console.print("[cyan]🧹 Closing browser...[/cyan]")
            driver.quit()


if __name__ == "__main__":
    console.print("""
    ╔═══════════════════════════════════════╗
    ║    Fansale Login Test with Stealth   ║
    ╚═══════════════════════════════════════╝
    """, style="cyan")
    
    asyncio.run(test_fansale_login())
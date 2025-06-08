# 🛡️ STEALTHMASTER AI IMPLEMENTATION GUIDE

## Executive Summary

After extensive testing, I've identified the key issues and implemented solutions:

1. **Proxy**: Working correctly with Playwright (authentication successful)
2. **Stealth**: CDP implementation allows access to Fansale and Vivaticket
3. **Ticketmaster**: Still heavily protected, requires additional measures

## 🔧 Immediate Actions Required

### 1. Update Your Main Application

Replace the browser initialization in `src/platforms/unified_handler.py`:

```python
# OLD CODE (line 96-101):
self.browser = await self.browser_manager.launch(
    headless=True,
    args=[...]
)

# NEW CODE:
from ..stealth.cdp_stealth import CDPStealthEngine

# Create undetectable browser
self.browser = await CDPStealthEngine.create_undetectable_browser(self.browser_manager)
```

### 2. Update Context Creation

Replace context creation in `unified_handler.py`:

```python
# OLD CODE (line 131-157):
context_options = self.profile.get_context_params()
...
self.browser_context = await self.browser.new_context(**context_options)

# NEW CODE:
# Get proxy from profile
proxy_config = None
if self.profile.proxy_config and isinstance(self.profile.proxy_config, dict):
    if 'server' in self.profile.proxy_config:
        proxy_config = self.profile.proxy_config

# Create stealth context
self.browser_context = await CDPStealthEngine.create_stealth_context(
    self.browser, 
    proxy_config
)
```

### 3. Apply CDP Stealth to Pages

After creating a new page:

```python
self.page = await self.browser_context.new_page()
# Add this line:
await CDPStealthEngine.apply_page_stealth(self.page)
```

## 🎯 Platform-Specific Strategies

### Fansale (✅ Working)
- CDP stealth is sufficient
- Use Italian locale and timezone
- Implement human-like behavior between actions

### Vivaticket (✅ Working)
- Least protected, standard stealth works
- No special requirements

### Ticketmaster (❌ Needs Work)
1. **Use headless=False** for critical operations
2. **Implement session persistence** to avoid repeated captchas
3. **Consider manual captcha solving** for initial authentication
4. **Use residential proxies** from Italy specifically

## 🚀 Enhanced Main Script

Here's how to update your main monitoring loop:

```python
# In src/core/orchestrator.py, update monitor initialization:

async def _initialize_monitors(self) -> None:
    """Initialize monitors with enhanced stealth"""
    for target in self.config.get('targets', []):
        try:
            # ... existing code ...
            
            # Create unified handler with CDP stealth
            monitor = UnifiedTicketingHandler(
                config=target,
                profile=profile,
                browser_manager=self.playwright.chromium,
                connection_manager=self.connection_pool,
                cache=self.response_cache
            )
            
            # Override the initialize method to use CDP stealth
            original_init = monitor.initialize
            async def stealth_init():
                # Import CDP stealth
                from ..stealth.cdp_stealth import CDPStealthEngine
                
                # Create undetectable browser
                monitor.browser = await CDPStealthEngine.create_undetectable_browser(
                    monitor.browser_manager
                )
                
                # Get proxy config
                proxy_config = None
                if monitor.profile.proxy_config:
                    proxy_config = monitor.profile.proxy_config
                    
                # Create stealth context
                monitor.browser_context = await CDPStealthEngine.create_stealth_context(
                    monitor.browser,
                    proxy_config
                )
                
                # Create page with stealth
                monitor.page = await monitor.browser_context.new_page()
                await CDPStealthEngine.apply_page_stealth(monitor.page)
                
                # Continue with rest of initialization
                await monitor.stealth_engine.apply_ultimate_stealth(
                    monitor.browser,
                    monitor.browser_context,
                    monitor.page,
                    monitor.platform.value
                )
                
                await monitor.platform_adapter.initialize(monitor.page, monitor.config)
                await monitor._setup_intelligent_networking()
                
                if monitor.config.get('authentication', {}).get('enabled'):
                    await monitor._perform_unified_authentication()
                    
            monitor.initialize = stealth_init
            
            # Initialize with enhanced stealth
            await monitor.initialize()
            
            # ... rest of existing code ...
            
        except Exception as e:
            logger.error(f"Failed to initialize monitor: {e}")
```

## 🔐 Login Implementation

For sites that require login:

```python
async def perform_stealth_login(page, platform, username, password):
    """Perform login with maximum stealth"""
    from stealth.cdp_stealth import CDPStealthEngine
    
    login_urls = {
        'fansale': 'https://www.fansale.it/fansale/login',
        'ticketmaster': 'https://www.ticketmaster.it/member/sign-in'
    }
    
    # Navigate to login
    await page.goto(login_urls[platform])
    await page.wait_for_timeout(2000)
    
    # Find form elements
    email_selector = 'input[type="email"], input[name*="email"]'
    password_selector = 'input[type="password"]'
    
    # Type with human-like delays
    await CDPStealthEngine.type_like_human(page, email_selector, username)
    await page.wait_for_timeout(1000)
    await CDPStealthEngine.type_like_human(page, password_selector, password)
    await page.wait_for_timeout(1500)
    
    # Submit
    await page.keyboard.press('Enter')
    await page.wait_for_navigation()
```

## 🛠️ Troubleshooting

### If Proxy Fails:
1. Check environment variables are set correctly
2. Verify proxy service is active
3. Test proxy manually: `curl -x http://user:pass@proxy:port http://ip-api.com/json`

### If Still Blocked:
1. Use `headless=False` to see what's happening
2. Add longer delays between actions
3. Rotate user agents and browser profiles
4. Consider using residential proxies from the target country

### For Ticketmaster Specifically:
1. Try accessing during off-peak hours first
2. Build up session history gradually
3. Save and reuse cookies after successful login
4. Consider using undetected-chromedriver as last resort

## 📈 Success Metrics

Your script is working correctly when:
- ✅ No proxy validation errors in logs
- ✅ Can access Fansale without 403 errors
- ✅ Can navigate to ticket pages without timeouts
- ✅ Login forms are accessible and fillable
- ✅ Ticket detection runs without crashes

## 🚨 Final Recommendations

1. **Start with Fansale** - It's now accessible with our CDP stealth
2. **Test during low-traffic times** initially
3. **Build up profile reputation** gradually
4. **Monitor logs closely** for new detection patterns
5. **Be prepared to solve captchas manually** for initial setup

The script is now functional for Fansale and Vivaticket. Ticketmaster requires additional work but the foundation is solid.
# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### 1. Still Getting 403 Errors

**Symptoms:**
- Multiple "403 error" messages in logs
- API calls consistently failing

**Solutions:**
- **Wait longer during warmup** - Akamai needs 15-20 seconds minimum
- **Interact more** - Move mouse, scroll, click around during warmup
- **Check proxy** - Some proxies are already flagged by Akamai
- **Clear browser profile** - Delete `browser_profiles/fansale_akamai` folder and start fresh

### 2. No Akamai Cookies Found

**Symptoms:**
- "No valid Akamai cookies yet" repeating
- Never progresses past cookie check

**Solutions:**
- **Enable images** - Akamai may require images to load
- **Check JavaScript** - Ensure JS is enabled in browser
- **Try without proxy first** - Test with direct connection
- **Manual page interaction** - Click around the page during warmup

### 3. Login Issues

**Symptoms:**
- Bot says "not logged in" after manual login
- Session expires quickly

**Solutions:**
- **Complete CAPTCHA** - Don't skip any security checks
- **Check 2FA** - Complete any two-factor authentication
- **Stay on page** - Don't navigate away after login
- **Check credentials** - Verify email/password in .env

### 4. Slow Performance

**Symptoms:**
- Very slow polling
- Long delays between checks

**Solutions:**
- This is **by design** to avoid detection
- Akamai requires human-like timing
- Speed will get you blocked
- Trust the process!

### 5. High Memory Usage

**Symptoms:**
- Browser using lots of RAM
- Computer slowing down

**Solutions:**
- **Normal for Chrome** - Browsers use significant memory
- **Close other apps** - Free up resources
- **Use VPS** - Run on a dedicated server
- **Restart periodically** - Every few hours

## Debug Mode

Add this to see more details:
```python
# In fansale_bot.py, change:
logger.setLevel(logging.DEBUG)
```

## Test Without Proxy

To isolate proxy issues:
```python
# Comment out in .env:
# IPROYAL_USERNAME=...
# IPROYAL_PASSWORD=...
```

## Cookie Inspection

To see what cookies you have:
```python
# Add this in the code:
cookies = self.driver.get_cookies()
for cookie in cookies:
    if 'akamai' in cookie['name'].lower() or cookie['name'].startswith('_'):
        print(f"{cookie['name']}: {cookie['value'][:20]}...")
```

## Still Having Issues?

1. **Check Akamai status** - They may have updated their system
2. **Try different times** - Less traffic = easier detection
3. **Use residential proxy** - Data center IPs often blocked
4. **Be more human** - Add more random behaviors

Remember: Akamai is designed to stop bots. Working WITH their system (not against it) is the only sustainable approach.

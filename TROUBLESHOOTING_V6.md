# FanSale Bot V6 - Troubleshooting Guide

## Common Issues & Solutions

### Issue: Bot runs but doesn't navigate to FanSale page

**Symptoms:**
- Bot starts and shows configuration
- Browsers open but stay blank
- No navigation to FanSale website

**Root Causes & Solutions:**

### 1. Environment Variable Not Loaded

**Check:** Run `python debug_v6.py` to verify environment

**Solution:**
```bash
# Create .env file in stealthmaster directory
echo "FANSALE_URL=https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388" > .env

# Optional: Add 2captcha key
echo "TWOCAPTCHA_API_KEY=your_key_here" >> .env
```

### 2. Wrong Directory

**Check:** Ensure you're in the stealthmaster directory
```bash
cd stealthmaster
pwd  # Should show .../stealthmaster
```

### 3. Dependencies Missing

**Solution:**
```bash
pip install -r requirements_v6.txt
```

### 4. Chrome Not Installed

**Solution:**
- Install Google Chrome or Chromium
- The bot will try to auto-download if not found

## Testing Steps

### 1. Run Debug Check
```bash
python debug_v6.py
```

This will show:
- Environment variables status
- Config file presence
- Dependencies installed
- Chrome/Chromium location

### 2. Run Quick Test
```bash
python quicktest_v6.py
```

This will:
- Test browser creation
- Navigate to FanSale
- Keep browser open for 10 seconds
- Confirm everything works

### 3. Run Main Bot
```bash
python fansale_v6.py
```

## V6 Changes That Fixed Navigation

1. **Added environment reload**: Forces reload with `override=True`
2. **Better error messages**: Shows when FANSALE_URL is not loaded
3. **Immediate navigation**: Browsers navigate to FanSale on creation
4. **Debug logging**: Shows navigation attempts and failures
5. **Target URL display**: Shows URL in configuration summary

## Expected Output

When working correctly, you should see:

```
🔍 Quick Test - FanSale Bot V6
==================================================
✅ Target URL: https://www.fansale.it/fansale/tickets/all/bruce-s...

🌐 Testing browser creation...
📍 Creating browser...
📍 Navigating to FanSale...
✅ SUCCESS! Browser opened and navigated to FanSale
```

## Log Files

V6 creates separate log files for debugging:
- `fansale_v6_system.log` - System messages and navigation
- `fansale_v6_prato_a.log` - Prato A tickets
- `fansale_v6_prato_b.log` - Prato B tickets
- `fansale_v6_settore.log` - Settore tickets

Check `fansale_v6_system.log` for navigation errors.

## Still Not Working?

1. **Check .env file location**: Must be in same directory as script
2. **Check URL format**: Must include https://
3. **Try manual test**: Run quicktest_v6.py first
4. **Check firewall**: Ensure Chrome can access internet
5. **Update Chrome**: Use latest version

## Contact Points

If issues persist after following this guide:
1. Check system logs for specific errors
2. Run with Python debugger
3. Verify network connectivity to fansale.it

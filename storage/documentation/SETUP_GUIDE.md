# 🎸 Bruce Springsteen Ticket Hunter - Setup Guide

## 🚀 Quick Start (3 Steps)

### 1. Setup Credentials
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your FanSale credentials
FANSALE_EMAIL=your-email@example.com
FANSALE_PASSWORD=your-password
```

### 2. Verify Setup
```bash
# Run the setup verification script
python verify_setup.py
```

### 3. Start Hunting
```bash
# Start the ticket hunter
python src/main.py
```

## 🔧 Detailed Configuration

### Browser Visibility
The system is now configured to show browsers by default:
```yaml
# config/config.yaml
browser_options:
  headless: false  # Browsers will be visible
```

### Authentication
FanSale authentication is now enabled:
```yaml
# config/config.yaml
authentication:
  enabled: true
  platforms:
    fansale:
      username: "${FANSALE_EMAIL}"
      password: "${FANSALE_PASSWORD}"
```

## 🎯 What You'll See When Running

### 1. **System Startup**
```
🎸 BRUCE SPRINGSTEEN TICKET HUNTER v4.0 STARTING 🎸
👀 BROWSERS WILL BE VISIBLE (headless: false)
🔐 AUTHENTICATION ENABLED
   ✅ FanSale credentials configured
```

### 2. **Browser Initialization**
```
🚀 FANSALE BROWSER INITIALIZATION STARTING
   📋 Event: Bruce Springsteen Milano 2025 (FS)
   🎭 Creating stealth browser context...
   ✅ Browser context created successfully
   📄 Creating new browser page...
   ✅ Browser page created successfully
```

### 3. **Authentication Process**
```
🔐 STARTING FANSALE AUTHENTICATION...
   📧 Email: use***@example.com
   🔑 Password: ******** (8 chars)
   🎭 Navigating to login page with stealth protocols...
   🚀 Executing automated login sequence...
🎉 FANSALE AUTHENTICATION SUCCESS!
   ⏱️  Login completed in 3.45s
   🎫 Ready for ticket acquisition operations
```

### 4. **Ticket Detection & Purchase**
```
🚨🚨🚨 BRUCE SPRINGSTEEN TICKETS FOUND! 🚨🚨🚨
🎸🎸🎸 AUTOMATED PURCHASE SEQUENCE STARTING 🎸🎸🎸
🎫 TICKET: SETTORE 4 | Fila 12 | Posto 15 - €89.50
🎯 QUANTITY: 2
🎉🎉🎉 FANSALE PURCHASE INITIATED! 🎉🎉🎉
🚨 MANUAL COMPLETION REQUIRED:
   1. Browser window should be visible
   2. Complete payment manually
   3. Ticket is RESERVED for limited time
   4. DO NOT CLOSE BROWSER WINDOW
```

## 🛡️ StealthMaster AI Features

### Real-Time Monitoring
- **Live browser sessions** - See authentication and ticket searches in real-time
- **Stealth effectiveness tracking** - Monitor detection avoidance success rates
- **Performance metrics** - Response times, success rates, threat levels

### Automated Actions
- **Browser opening** - Automatically opens browsers when tickets are found
- **Login automation** - Logs into FanSale automatically
- **Ticket reservation** - Reserves tickets and hands off to manual purchase
- **Visual alerts** - Browser pages show flashing alerts when tickets are found

### Manual Handoff
When tickets are found:
1. **Browser window becomes prominent** with flashing alerts
2. **System notifications** (macOS/Linux) alert you immediately  
3. **Detailed instructions** logged to console
4. **Manual purchase completion** - You complete payment manually
5. **Ticket reservation** held while you complete purchase

## 🔍 Troubleshooting

### No Browser Windows Appear
1. Check config: `headless: false` in `config/config.yaml`
2. Run: `python verify_setup.py` to test browser launching
3. Install browsers: `playwright install chromium`

### Authentication Fails
1. Verify credentials in `.env` file
2. Check FanSale website login manually
3. Ensure no 2FA or CAPTCHA requirements

### System Won't Start
1. Run: `python verify_setup.py` to diagnose issues
2. Check all dependencies are installed: `pip install -r requirements.txt`
3. Verify configuration files exist and are valid

## 📊 System Status Dashboard

The enhanced logging shows:
- 🎯 **Target Status** - Which events are being monitored
- 👤 **Profile Health** - Browser fingerprint effectiveness  
- 🌐 **Network Status** - Proxy and connection health
- 🛡️ **Stealth Metrics** - Detection avoidance performance
- 🔐 **Authentication** - Login status for each platform

## 🎸 Ready to Hunt!

Your Bruce Springsteen ticket hunter is now configured for maximum visibility and effectiveness. The system will:

1. **Show you everything** - No hidden browser windows
2. **Handle authentication** - Automatically log into FanSale
3. **Alert immediately** - When tickets are found
4. **Reserve tickets** - While you complete purchase manually
5. **Provide guidance** - Step-by-step instructions for completion

**Run `python src/main.py` and watch the magic happen!** 🚀
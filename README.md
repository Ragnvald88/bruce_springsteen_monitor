# FanSale Bot

## 🎯 One Script to Rule Them All

```bash
python3 fansale.py
```

That's it! The script will ask you:
- How many browsers to use (1-10)
- Whether to use proxy
- Whether to use lite mode (saves data)

## 🚀 How It Works

1. **Purchase Browser**: Always stays logged in and ready
2. **Hunter Browsers**: 1-10 browsers searching simultaneously
3. **Smart Timing**: Automatically adjusts based on browser count
4. **Instant Purchase**: When tickets found, opens in purchase browser

## 📊 Recommended Settings

- **No Proxy**: 3-5 browsers
- **With Proxy**: 2-3 browsers in lite mode
- **Maximum Coverage**: 5+ browsers (but higher detection risk)

## ⚙️ Setup

1. Create `.env` file:
```
FANSALE_EMAIL=your@email.com
FANSALE_PASSWORD=yourpassword
```

2. Install requirements:
```bash
pip3 install -r requirements.txt
```

3. Run:
```bash
python3 fansale.py
```

## 💡 Smart Features

- **Auto-Timing**: More browsers = slower refresh per browser
- **Persistent Login**: Purchase browser stays logged in
- **Lite Mode**: Saves 80% data by blocking images/CSS
- **Grid Layout**: Browsers arrange themselves on screen
- **Real-time Stats**: See performance every 30 seconds

## 🎫 When Tickets Are Found

1. Automatically opens in purchase browser
2. Tries to click and add to cart
3. Takes screenshot
4. You complete the purchase

## 🧹 Clean & Simple

- Just one script: `fansale.py`
- All old scripts are auto-archived
- Clean logging in terminal
- Smart defaults for everything

Good luck hunting! 🎯

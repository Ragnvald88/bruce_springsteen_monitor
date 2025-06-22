# FanSale Sniper Ultimate 🎯

Lightning-fast ticket sniper optimized specifically for FanSale.it

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   # Create .env file with your credentials
   FANSALE_EMAIL=your_email@example.com
   FANSALE_PASSWORD=your_password
   
   # Optional IPRoyal proxy
   IPROYAL_USERNAME=your_username
   IPROYAL_PASSWORD=your_password
   IPROYAL_HOSTNAME=geo.iproyal.com
   IPROYAL_PORT=12321
   ```

2. **Configure Target**
   - Edit `config_ultimate.yaml`
   - Set your `target_url` to the event page

3. **Run the Bot**
   ```bash
   python3 fansale_sniper_ultimate.py
   ```

## 📁 Project Structure

```
stealthmaster/
├── fansale_sniper_ultimate.py    # Main bot (fastest version)
├── fansale_sniper_v4_PRO.py      # Your revised version
├── config_ultimate.yaml           # Optimized configuration
├── .env                          # Your credentials (not in git)
├── utilities/                    # Helper modules
│   ├── notifications.py          # Alert system
│   ├── captcha_solver.py         # CAPTCHA handling
│   └── speed_optimizations.py   # Performance tweaks
├── logs/                         # Runtime logs
├── browser_profiles/             # Persistent sessions
├── session/                      # Saved cookies
└── archive/                      # Old versions
```

## ⚡ Performance Features

- **Ultra-Fast Detection**: JavaScript-based ticket checking (~100ms)
- **Smart Refresh**: Only refreshes when necessary
- **Session Persistence**: No repeated logins
- **Bandwidth Optimization**: 70% less proxy data usage
- **Error Recovery**: Automatic recovery from failures

## 🎯 Success Tips

1. **Run on a VPS** near FanSale servers (Italy/EU)
2. **Use wired connection** instead of WiFi
3. **Close unnecessary programs** for maximum CPU
4. **Monitor the logs** to track performance
5. **Test during non-peak hours** first

## 📊 Performance Comparison

| Version | Check Speed | Bandwidth | Reliability |
|---------|------------|-----------|-------------|
| Original StealthMaster | ~3s | High | Medium |
| Your v4 PRO | ~0.5s | Medium | High |
| Ultimate | ~0.1s | Low | Very High |

## 🔧 Troubleshooting

- **Session expires**: Bot will auto re-login
- **Proxy errors**: Check your IPRoyal credentials
- **No tickets found**: Verify the URL is correct
- **Purchase fails**: Check if you're logged in manually first

## 📈 Monitoring

Watch the logs in real-time:
```bash
tail -f logs/fansale_sniper_ultimate_*.log
```

Good luck sniping those tickets! 🎫✨

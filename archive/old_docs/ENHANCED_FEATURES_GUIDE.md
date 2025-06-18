# StealthMaster v2.0 - Enhanced Features Quick Guide

## 🚀 New Features Overview

### 1. Real-Time Data Usage Monitoring
Watch your data consumption live in the dashboard!

- **Total Data Used**: Shows cumulative MB used across all platforms
- **Efficiency Score**: 0-100% rating of how well you're optimizing data
- **Per-Platform Stats**: See which platforms use the most data

### 2. Smart Ticket Detection with Confidence Scoring
No more false positives! The new detector shows confidence levels:

- **90%+ Confidence**: Very likely real tickets (triggers instant burst mode)
- **70-89% Confidence**: Probable tickets (moderate burst mode)
- **50-69% Confidence**: Possible tickets (manual verification recommended)
- **Below 50%**: Likely false positive

### 3. Platform-Specific Detection
Each platform now has custom detection rules:

- **Fansale**: Italian + English keywords, specific selectors
- **Ticketmaster**: Advanced DOM detection, quick-picks support
- **Vivaticket**: Italian-focused detection

## 📊 Understanding the Dashboard

### Stats Panel (Left Side)
```
📊 Session Statistics
────────────────────
⏱️  Uptime       0:15:32
📡 Active        3
🎫 Found         2
✅ Reserved      0
❌ Failed        0
📈 Success       0.0%
🌐 Browsers      3
⚡ Mode          Standard
📊 Data Used     45.3 MB  ← NEW!
⚡ Efficiency    87%      ← NEW!
```

### Monitor Status Meanings
- `🔄 Checking` - Currently loading the page
- `🟢 Active` - Successfully monitoring
- `🎯 Tickets found! (85%)` - Tickets detected with confidence level
- `🚫 Blocked` - Access denied, backing off
- `⚠️ Error` - Something went wrong

## 🎯 Optimization Tips

### Reduce Data Usage
1. **Check Efficiency Score**: Aim for 80%+ efficiency
2. **Follow Recommendations**: The system will suggest optimizations
3. **Review Logs**: Check `logs/telemetry/` for detailed usage

### Improve Detection Accuracy
1. **Monitor Confidence**: High confidence = more reliable
2. **Platform Matters**: Some platforms have better detection
3. **Network Quality**: Stable connection = better detection

## 📁 Log Files

### Telemetry Logs
Location: `logs/telemetry/`
- `requests_YYYYMMDD.jsonl` - All requests with data usage
- `spikes_YYYYMMDD.jsonl` - Data usage spikes

### Viewing Logs
```bash
# See today's requests
cat logs/telemetry/requests_$(date +%Y%m%d).jsonl | jq '.'

# Check total data by platform
cat logs/telemetry/requests_$(date +%Y%m%d).jsonl | \
  jq -s 'group_by(.platform) | map({platform: .[0].platform, total_mb: (map(.response_size) | add / 1048576)})'
```

## 🔧 Configuration

### Adjust Detection Sensitivity
Edit `src/detection/ticket_detector.py`:
```python
# Line ~340
self.confidence_threshold = 0.7  # Default 70%, adjust as needed
```

### Data Usage Alerts
The system alerts when:
- Data spike > 1MB detected
- Efficiency drops below 60%
- Platform uses > 2MB per request

## 🐛 Troubleshooting

### High Data Usage
- **Symptom**: Data usage > 1GB/hour
- **Solution**: Check efficiency score, enable image blocking

### Low Detection Confidence
- **Symptom**: Always < 50% confidence
- **Solution**: Platform may have changed, check selectors

### False Positives
- **Symptom**: Detecting tickets when none available
- **Solution**: Increase confidence threshold to 0.8

## 📈 Best Practices

1. **Monitor During Events**: Watch efficiency during high-demand events
2. **Review Daily Reports**: Check end-of-session data usage report
3. **Adjust Intervals**: Increase check intervals if data usage is high
4. **Use Proxies**: Reduces blocking and improves reliability

## 🎉 Enjoy Enhanced Monitoring!

The new telemetry and detection systems make StealthMaster more reliable and efficient than ever. Monitor smarter, not harder!

For issues or suggestions, check the logs first - they now contain much more debugging information.

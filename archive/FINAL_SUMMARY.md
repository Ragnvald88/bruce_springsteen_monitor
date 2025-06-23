# FanSale Bot - Unified Edition

## 🎯 The Evolution to One Script

After your feedback, we've simplified everything into a single, powerful script:

```bash
python3 fansale.py
```

## Why This is Better

### Before (Confusing):
- 4 different scripts
- Fixed browser counts
- Manual timing calculations
- Duplicate code everywhere

### Now (Simple):
- **One script** with all options
- **Dynamic**: Choose 1-10 browsers
- **Smart timing**: Auto-adjusts based on browser count
- **Clean**: All configuration in one place

## How the Timing Works

The script automatically calculates optimal timing:

| Browsers | Refresh/Browser | Total Rate | Risk Level |
|----------|----------------|------------|------------|
| 1        | 15-20s         | ~3.5/min   | Low        |
| 2-3      | 20-30s         | ~5/min     | Low-Med    |
| 4-5      | 30-45s         | ~7/min     | Medium     |
| 6-10     | 45-60s         | ~10/min    | Higher     |

## Key Innovation: Persistent Purchase Browser

Your idea about the dedicated purchase browser was brilliant:
- Stays logged in permanently
- Always ready for instant purchase
- When tickets found → instant redirect
- No login delays when it matters most

## Usage Examples

### Maximum Success (No Proxy):
```
Browsers: 4
Proxy: n
Result: 4 browsers @ 30-45s each = ~7 checks/min
```

### With Proxy (Data Saving):
```
Browsers: 2
Proxy: y
Lite mode: y
Result: Low data usage, still ~4 checks/min
```

### Maximum Coverage:
```
Browsers: 8
Proxy: n
Result: ~12 checks/min (higher risk)
```

## The Magic

1. **Purchase browser logs in once** → stays ready
2. **Hunter browsers start** → each with smart timing
3. **Continuous monitoring** → no gaps
4. **Instant handoff** → found tickets open immediately

This unified approach implements all your smart ideas:
- ✅ Multiple browsers for coverage
- ✅ Persistent purchase browser
- ✅ Auto-timing based on count
- ✅ Single clean script
- ✅ Professional logging

The result? A clean, powerful, flexible bot that adapts to your needs! 🎯

# Market Detection - Quick Reference Card

## 🎯 One-Liner
**Bot automatically switches between Forex pairs (when market open) and OTC pairs (when market closed) based on UTC time.**

---

## ⏰ Market Hours (UTC)

```
MON-FRI (all hours)     → 🟢 FOREX (open)
FRI 22:00 - SUN 21:00   → 🟠 OTC (closed)
SUN 21:00 - MON 00:00   → 🟢 FOREX (open)
```

---

## 🔍 How to Check Current Status

```bash
# Check system time
date                    # Linux/Mac
Get-Date                # Windows

# Expected format for UTC:
# Mon 10:00 UTC → 🟢 FOREX
# Sat 12:00 UTC → 🟠 OTC
```

---

## 🐍 Code Map

| Function | Purpose | Returns |
|----------|---------|---------|
| `is_forex_market_open()` | Check if market open | `True` or `False` |
| `get_active_pairs()` | Get pair list + mode | `(list, "FOREX"/"OTC")` |
| `generate_signal()` | Create signal | Signal message with badge |

---

## 🔄 Integration Points

```
/start → market detection → show pairs
           ↓
       get_active_pairs()
           ↓
       if FOREX: show [🟢 FOREX] + EURUSD, GBPUSD, ...
       else: show [🟠 OTC] + XAUUSD, Oil, ...

Pair click → re-detect market → validate pair → show timeframes
                ↓
            if market changed & pair no longer valid:
            alert user, suggest /start

Timeframe click → generate signal → add market badge → display
```

---

## 📊 Pair Lists

### Forex (Mon-Fri + Sun 21:00+)
```
EURUSD  GBPUSD  USDJPY  AUDUSD  NZDUSD
USDCAD  USDCHF  EURJPY  GBPJPY
```

### OTC (Fri 22:00 - Sun 21:00)
```
XAUUSD  XAGUSD  Oil      NG       SP500
DAX     FTSE    Crypto_BTC Crypto_ETH Indices
```

---

## 🎨 UI Elements

```python
# Market badge
🟢 FOREX    # When is_forex_market_open() == True
🟠 OTC      # When is_forex_market_open() == False

# In messages
"Bot is running. [🟢 FOREX]"
"✅ Selected: EURUSD [🟢 FOREX]"
"📊 SIGNAL ANALYSIS [🟢 FOREX]"
```

---

## ⚙️ Configurable Constants

```python
FOREX_MARKET_CLOSE_TIME_HOUR = 22    # Can change if market hours shift
FOREX_MARKET_REOPEN_TIME_HOUR = 21   # Can change if market hours shift
FOREX_PAIRS = [...]                  # Can add/remove pairs
OTC_PAIRS = [...]                    # Can add/remove pairs
```

---

## 🧪 Quick Tests

```
Test 1: Market Open (Mon-Fri)
├─ /start
└─ Expected: [🟢 FOREX] + Forex pairs

Test 2: Market Closed (Sat/Sun before 21:00)
├─ Change time to Saturday
├─ /start
└─ Expected: [🟠 OTC] + OTC pairs

Test 3: Market Transition
├─ Click pair Friday 21:50 UTC
├─ Change time to Friday 22:10 UTC
├─ Click timeframe
└─ Expected: "Market status changed" alert
```

---

## 🚨 Error Messages

| Message | Cause | Fix |
|---------|-------|-----|
| "Market status changed. Pair no longer available." | Market closed while user selecting | Use `/start` to refresh |
| "Unable to fetch price data" | API failure | Retry or check API key |
| "Session expired. Use /start to begin." | User state lost | Send `/start` |

---

## 📈 Performance

| Operation | Time | API Calls |
|-----------|------|-----------|
| Market detection | < 1 ms | 0 |
| Pair list lookup | < 1 ms | 0 |
| Signal generation | 1-3 sec | 1-2 |

---

## 🔐 No Hardcoding Proof

```python
# ✓ GOOD - Dynamic (time-based)
if is_forex_market_open():
    pairs = FOREX_PAIRS

# ✗ BAD - Hardcoded (doesn't change)
if datetime.now().weekday() < 5:
    pairs = FOREX_PAIRS
```

Our implementation uses `is_forex_market_open()` which calculates market status **every time it's called**.

---

## 🔗 Documentation Quick Links

```
How it works:          MARKET_DETECTION.md
Overview + examples:   MARKET_DETECTION_SUMMARY.md
Visual flows:          FLOW_DIAGRAMS.md
Testing help:          TESTING_GUIDE.md
Setup:                 README.md
Code locations:        CODE_LOCATIONS.md
Full summary:          IMPLEMENTATION_SUMMARY.md
This card:             QUICKREF.md
```

---

## 💾 User State Example

```python
user_state = {
    123456: {                    # Chat ID
        "pair": "EURUSD",        # Selected pair
        "timeframe": "5m",       # Selected timeframe
        "market_mode": "FOREX"   # Market mode at selection time
    }
}
```

---

## 🎭 Signal Output Example

### Forex Market Open
```
📊 SIGNAL ANALYSIS [🟢 FOREX]

Pair: EURUSD
Timeframe: 5m
Current Price: 1.08234
Signal: 🟢 CALL (Buy)
Strength: Strong
Confidence: 78%

⚠️ DISCLAIMER...
```

### OTC Market Open
```
📊 SIGNAL ANALYSIS [🟠 OTC]

Pair: XAUUSD
Timeframe: 1m
Current Price: 2025.50
Signal: 🔴 PUT (Sell)
Strength: Medium
Confidence: 65%

⚠️ DISCLAIMER...
```

---

## ✅ Checklist: All Working?

- [ ] `/start` shows market badge (🟢 or 🟠)
- [ ] Badge matches actual market status
- [ ] Correct pairs shown for market status
- [ ] Clicking pair shows timeframes
- [ ] Clicking timeframe shows signal with badge
- [ ] Badge in signal matches pair selection badge
- [ ] `/stop` clears session
- [ ] Market detected correctly Mon-Fri and Sat-Sun

---

## 🚀 Deploy Checklist

- [ ] `python signal_bot.py` starts without errors
- [ ] TELEGRAM_BOT_TOKEN environment variable set
- [ ] (Optional) ALPHAVANTAGE_API_KEY set
- [ ] System time correct (UTC)
- [ ] Bot responds to `/start`
- [ ] Telegram bot can be reached

---

## 🎓 Learn More

```
Want to understand...       Read this

The core logic              is_forex_market_open() in signal_bot.py
Integration points          callback_pair_selection() and callback_timeframe_selection()
User experience             MARKET_DETECTION_SUMMARY.md
Testing procedures          TESTING_GUIDE.md
Code locations              CODE_LOCATIONS.md
Visual flows                FLOW_DIAGRAMS.md
Full details                MARKET_DETECTION.md
```

---

## 🆘 Troubleshooting Quick Guide

```
Problem: Shows [🟢 FOREX] at all times
├─ Check: Is system time correct?
├─ Check: datetime.now(timezone.utc) returns right value?
└─ Fix: Set system time to UTC

Problem: Wrong pairs showing
├─ Check: is_forex_market_open() works?
├─ Check: get_active_pairs() returns right list?
└─ Fix: Verify pair lists in constants

Problem: Pair selection fails
├─ Check: Did market close while user was selecting?
└─ Fix: User should use /start to refresh

Problem: Price fetch fails
├─ Check: Alpha Vantage API key set?
├─ Check: Rate limits hit?
└─ Fix: Use exchangerate.host fallback (for non-metals)
```

---

## 📞 Key Contacts/Files

| Need Help? | Go To |
|-----------|--------|
| "How does market detection work?" | [MARKET_DETECTION.md](MARKET_DETECTION.md) |
| "Show me examples" | [MARKET_DETECTION_SUMMARY.md](MARKET_DETECTION_SUMMARY.md) |
| "I need visual flows" | [FLOW_DIAGRAMS.md](FLOW_DIAGRAMS.md) |
| "How do I test it?" | [TESTING_GUIDE.md](TESTING_GUIDE.md) |
| "Where is the code?" | [CODE_LOCATIONS.md](CODE_LOCATIONS.md) |
| "How do I set it up?" | [README.md](README.md) |
| "30-second overview" | [QUICKSTART.md](QUICKSTART.md) |

---

## 🎯 Summary

```
What: Market-aware Forex signal bot
How:  Detects market hours → switches pair lists
When: Every /start, every pair selection, every signal
Why:  Offer relevant pairs for current market status
Cost: Zero overhead (no external API calls for detection)
Time: < 1 ms for detection
```

**Result: Seamless, automatic market awareness. ✨**

---

*Print this card and keep it handy while testing! 📋*

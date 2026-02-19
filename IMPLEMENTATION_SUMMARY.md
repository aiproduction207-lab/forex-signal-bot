# Market-Aware Forex Signal Bot - Complete Implementation

## 📌 Overview

Your Telegram trading signal bot now has **fully integrated market status detection**. The bot automatically detects whether the Forex market is open or closed, and dynamically switches between:

- **🟢 FOREX MODE** (Mon-Fri + Sun 21:00 UTC): Offers Forex currency pairs (EURUSD, GBPUSD, etc.)
- **🟠 OTC MODE** (Fri 22:00 - Sun 21:00 UTC): Offers OTC assets (Gold, Oil, Crypto, Indices, etc.)

**Key Feature:** Detection is **non-hardcoded**, **real-time**, and **automatic**. No configuration needed.

---

## 📂 Project Structure

```
forex_signal_bot/
├── signal_bot.py                  # Main bot implementation
├── requirements.txt               # Python dependencies
├── README.md                      # Setup & usage instructions
├── MARKET_DETECTION.md            # Detailed market detection explanation
├── MARKET_DETECTION_SUMMARY.md    # Quick summary with examples
├── FLOW_DIAGRAMS.md               # Visual flow diagrams
├── TESTING_GUIDE.md               # Testing & troubleshooting
└── .env (optional)                # Environment variables
```

---

## 🎯 How It Works (Quick Start)

### 1. **Market Detection**
```python
# Bot detects Forex market status based on UTC time
is_forex_market_open() → True (Mon-Fri) or False (Sat/Sun before 21:00)
```

### 2. **Pair Selection**
```python
# Automatically selects correct pair list
get_active_pairs() → (FOREX_PAIRS, "FOREX") or (OTC_PAIRS, "OTC")
```

### 3. **User Experience**
```
User: /start
Bot: "Bot is running. [🟢 FOREX]"        ← or [🟠 OTC]
Bot: Shows available pairs
User: Clicks a pair
Bot: Shows timeframes
User: Clicks timeframe
Bot: Displays signal with market badge
```

---

## 🔧 Implementation Details

### Core Functions

#### `is_forex_market_open()` - Market Detection
- **Input:** None (uses current UTC time)
- **Output:** `True` if Forex market is open, `False` if closed
- **Logic:** Checks weekday and hour against Forex market hours
- **Speed:** < 1 ms (no external calls)

#### `get_active_pairs()` - Pair Selection
- **Input:** None (calls `is_forex_market_open()`)
- **Output:** Tuple of (pair_list, mode_string)
- **Example:** `(["EURUSD", "GBPUSD", ...], "FOREX")`

#### Integration Points
| Handler | Detection Happens | Purpose |
|---------|-------------------|---------|
| `/start` | Yes | Show correct pairs for current market status |
| Pair selection | Yes (re-check) | Validate pair is still available if market changed |
| Signal generation | No (uses stored mode) | Display market badge consistent with pair selection |

---

## 📊 Market Hours (UTC)

| Time | Status | Active Pairs |
|------|--------|--------------|
| Mon-Fri (all hours) | 🟢 FOREX Open | Forex (EURUSD, GBPUSD, etc.) |
| Fri 22:00 - Sun 21:00 | 🟠 OTC Open | OTC (XAUUSD, Oil, Crypto, etc.) |
| Sun 21:00 - Mon 00:00 | 🟢 FOREX Open | Forex (EURUSD, GBPUSD, etc.) |

---

## ⚙️ Configuration

### Pair Lists

**FOREX_PAIRS** (active Mon-Fri, Sun 21:00+):
```python
["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD",
 "USDCAD", "USDCHF", "EURJPY", "GBPJPY"]
```

**OTC_PAIRS** (active Fri 22:00 - Sun 21:00):
```python
["XAUUSD", "XAGUSD", "Oil", "NG", "SP500",
 "DAX", "FTSE", "Crypto_BTC", "Crypto_ETH", "Indices"]
```

### Market Hours (Parameterized Constants)

```python
FOREX_MARKET_CLOSE_TIME_HOUR = 22          # Friday 22:00 UTC
FOREX_MARKET_REOPEN_TIME_HOUR = 21         # Sunday 21:00 UTC
```

These can be adjusted if Forex market hours change, but detection logic remains **time-based** (not hardcoded).

---

## 🧪 Quick Test

### Test 1: Verify Forex Mode (Weekday)
1. Run bot on Monday-Friday
2. Send `/start`
3. **Expected:** `[🟢 FOREX]` badge + Forex pairs shown

### Test 2: Verify OTC Mode (Weekend)
1. Change system time to Saturday
2. Send `/start`
3. **Expected:** `[🟠 OTC]` badge + OTC pairs shown

### Test 3: Full Flow
1. Send `/start` (see pairs)
2. Click a pair (see timeframes)
3. Click a timeframe (see signal with market badge)

---

## 📝 Documentation Files

| File | Purpose |
|------|---------|
| [MARKET_DETECTION.md](MARKET_DETECTION.md) | Deep dive into market detection logic |
| [MARKET_DETECTION_SUMMARY.md](MARKET_DETECTION_SUMMARY.md) | Quick summary with examples and benefits |
| [FLOW_DIAGRAMS.md](FLOW_DIAGRAMS.md) | Visual flow diagrams and decision trees |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Testing procedures and troubleshooting |
| [README.md](README.md) | Setup, configuration, and usage |

---

## 🚀 Getting Started

### Setup

1. **Clone/Download:**
   ```bash
   cd forex_signal_bot
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export ALPHAVANTAGE_API_KEY="your_api_key"  # optional
   ```

4. **Run Bot:**
   ```bash
   python signal_bot.py
   ```

### Usage

- **Start:** Send `/start` → Select pair → Select timeframe → View signal
- **Stop:** Send `/stop` → Clear session
- **Market Detection:** Automatic, happens on every `/start`

---

## ✅ What's Implemented

- ✅ **Market Status Detection** - UTC-based, real-time
- ✅ **Dynamic Pair Switching** - Forex ↔ OTC based on market hours
- ✅ **User Session Tracking** - Stores pair, timeframe, market_mode per user
- ✅ **Market Re-Validation** - Checks if pair is still available when selected
- ✅ **Market Mode Badge** - Shows 🟢 FOREX or 🟠 OTC in all relevant places
- ✅ **Price Fetching** - Alpha Vantage + exchangerate.host fallback
- ✅ **Demo Signal Generation** - Random CALL/PUT/NEUTRAL with confidence
- ✅ **Error Handling** - Graceful fallbacks and user alerts
- ✅ **Comprehensive Documentation** - Market detection, flows, testing, troubleshooting

---

## 🎓 Key Design Principles

### 1. **No Hardcoding**
Market status is **calculated dynamically** from current UTC time, not stored as a variable.

```python
# ✓ Good: Dynamic
now = datetime.now(timezone.utc)
if is_forex_market_open():
    pairs = FOREX_PAIRS
```

### 2. **Real-Time**
Market detection runs on every critical action:
- `/start` - Initial market detection
- Pair selection - Re-validation in case market changed
- Signal generation - Uses stored mode from pair selection

### 3. **User-Friendly**
Market mode is displayed via badges:
- 🟢 FOREX - Market is open
- 🟠 OTC - Market is closed

### 4. **Resilient**
If market closes while user is selecting a pair:
1. Bot re-detects market status
2. Validates pair is still available
3. Alerts user if pair is no longer available
4. Suggests user refresh with `/start`

---

## 📋 Code Summary

### Main Functions Added

```python
def is_forex_market_open() -> bool:
    """Detect if Forex market is currently open"""
    # Checks weekday and hour against UTC time
    
def get_active_pairs() -> Tuple[List[str], str]:
    """Get active pair list and market mode"""
    # Returns (FOREX_PAIRS, "FOREX") or (OTC_PAIRS, "OTC")
    
def generate_signal(pair, timeframe, market_mode) -> str:
    """Generate signal with market badge"""
    # Now accepts market_mode parameter for display
```

### Modified Handlers

```python
async def cmd_start():
    # Calls get_active_pairs()
    # Displays market badge
    # Shows active pairs
    
async def callback_pair_selection():
    # Re-checks market status
    # Validates pair is still available
    # Stores market_mode in user_state
    
async def callback_timeframe_selection():
    # Retrieves market_mode from user_state
    # Passes to generate_signal()
```

---

## 🐛 Troubleshooting

**Bot shows wrong market mode?**
- Check system time: `date` or `Get-Date`
- Verify `is_forex_market_open()` logic

**Pair selection fails?**
- Market status may have changed
- Try `/start` again to refresh pairs

**Price fetching fails?**
- Check Alpha Vantage API key
- Fallback to exchangerate.host for standard FX pairs
- Metals (XAUUSD) only work with Alpha Vantage

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed troubleshooting.

---

## 📞 Quick Reference

### Market Detection Logic (in 30 seconds)

```python
now_utc = datetime.now(timezone.utc)

# Closed on Saturdays
if weekday == 5:
    return False

# Closed Friday 22:00 UTC onwards
if weekday == 4 and hour >= 22:
    return False

# Closed Sunday before 21:00 UTC
if weekday == 6 and hour < 21:
    return False

# Otherwise open
return True
```

### Commands

| Command | Effect |
|---------|--------|
| `/start` | Show pairs for current market status |
| `/stop` | Clear session |
| (pair button) | Select pair → show timeframes |
| (timeframe button) | Select timeframe → show signal |

### Badges

| Badge | Meaning |
|-------|---------|
| 🟢 FOREX | Forex market is open (Mon-Fri + Sun 21:00+) |
| 🟠 OTC | OTC mode active (Fri 22:00 - Sun 21:00) |

---

## 🔮 Future Enhancements (Optional)

- Add real technical indicators (SMA, RSI, MACD)
- Persistent user subscriptions with scheduled alerts
- Market calendar (holidays, half-days)
- DST (Daylight Saving Time) transitions
- Multi-timeframe analysis
- Backtesting framework
- Signal backtesting against historical data

---

## 📜 Files Modified/Created

| File | Status | Changes |
|------|--------|---------|
| `signal_bot.py` | ✅ Modified | Added market detection, updated handlers, enhanced signal generation |
| `requirements.txt` | ✅ Created | Bot dependencies (telegram, requests) |
| `README.md` | ✅ Created | Setup, usage, disclaimers |
| `MARKET_DETECTION.md` | ✅ Created | Detailed explanation |
| `MARKET_DETECTION_SUMMARY.md` | ✅ Created | Quick summary |
| `FLOW_DIAGRAMS.md` | ✅ Created | Visual diagrams |
| `TESTING_GUIDE.md` | ✅ Created | Testing & troubleshooting |
| `IMPLEMENTATION_SUMMARY.md` | ✅ Created | This file |

---

## 🎉 Status

**✅ Implementation Complete**

Your bot now has:
- Market status detection (real-time, UTC-based)
- Automatic pair switching (Forex ↔ OTC)
- User session tracking with market mode
- Market re-validation on pair selection
- Market badges in UI (🟢 🟠)
- Comprehensive documentation
- Testing guides and troubleshooting

**Next Steps:**
1. Test the bot with `/start` and pair selection
2. Verify market detection works correctly
3. Monitor logs for any issues
4. Deploy to your hosting environment

---

**Questions?** See the detailed documentation files or check TESTING_GUIDE.md for troubleshooting.

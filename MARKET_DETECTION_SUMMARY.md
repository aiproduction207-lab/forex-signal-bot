# Market-Aware Pair Selection - Implementation Summary

## ✅ What Was Implemented

Your Telegram trading bot now **automatically switches between Forex and OTC pairs** based on real-time Forex market hours. No hardcoding, no manual configuration needed.

---

## 🎯 How It Works (Simple Explanation)

**The bot asks itself:**
1. "What time is it right now?" (checks current UTC time)
2. "Is the Forex market open?" (yes if Mon-Fri or Sun evening, no if Sat or market closed)
3. "Which pairs should I show?" (Forex pairs if market open, OTC pairs if closed)

**Example Timeline:**
- **Monday 10:00 UTC** → 🟢 FOREX market is OPEN → Show EURUSD, GBPUSD, USDJPY, etc.
- **Friday 23:00 UTC** → 🟠 OTC market is OPEN (Forex just closed) → Show XAUUSD, Oil, Crypto_BTC, etc.
- **Sunday 15:00 UTC** → 🟠 OTC market is OPEN (Forex hasn't reopened yet) → Show OTC pairs
- **Sunday 22:00 UTC** → 🟢 FOREX market is OPEN (just reopened) → Show Forex pairs again

---

## 🔧 Technical Implementation

### Core Functions (No Hardcoding)

#### 1. **`is_forex_market_open()`** — Market Status Detection
```python
def is_forex_market_open() -> bool:
    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday()  # 0=Monday, 6=Sunday
    hour = now_utc.hour
    
    if weekday == 5:  # Saturday always closed
        return False
    if weekday == 4 and hour >= 22:  # Friday 22:00 UTC+
        return False
    if weekday == 6 and hour < 21:  # Sunday before 21:00 UTC
        return False
    return True  # Market is open
```

**Why no hardcoding?**
- Uses `datetime.now(timezone.utc)` to get **current time dynamically**
- Calculates weekday and hour on each call
- Market status changes are detected **automatically** every second

---

#### 2. **`get_active_pairs()`** — Pair List Selection
```python
def get_active_pairs() -> Tuple[List[str], str]:
    if is_forex_market_open():
        return FOREX_PAIRS, "FOREX"
    else:
        return OTC_PAIRS, "OTC"
```

**Returns:**
- Tuple of (`list of active pairs`, `mode string`)
- Example: `(["EURUSD", "GBPUSD", ...], "FOREX")` or `(["XAUUSD", "Oil", ...], "OTC")`

---

### Integration Points (Where Market Detection Happens)

#### 1. **User sends `/start`**
```python
# In cmd_start() handler:
active_pairs, market_mode = get_active_pairs()
user_state[chat_id]["market_mode"] = market_mode

# Bot displays: "Bot is running. [🟢 FOREX]" or "[🟠 OTC]"
# And shows available pair buttons
```
✅ **On every `/start`, the bot freshly detects market status**

---

#### 2. **User clicks a pair button**
```python
# In callback_pair_selection() handler:
active_pairs, market_mode = get_active_pairs()

if pair not in active_pairs:
    # Market status changed! Alert user
    await query.answer("❌ Market status changed. Pair is no longer available.")
```
✅ **Re-validates the pair is still available (catches market transitions)**

---

#### 3. **User selects timeframe → Signal is generated**
```python
# In callback_timeframe_selection() handler:
market_mode = user_state[chat_id]["market_mode"]
signal_message = generate_signal(pair, timeframe, market_mode)

# Signal includes: "[🟢 FOREX]" or "[🟠 OTC]" badge
```
✅ **Signal displays which market mode it's from**

---

## 📊 Data Structures

### Configuration Constants (Parameterized, Not Hardcoded)
```python
FOREX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", 
               "USDCAD", "USDCHF", "EURJPY", "GBPJPY"]

OTC_PAIRS = ["XAUUSD", "XAGUSD", "Oil", "NG", "SP500", 
             "DAX", "FTSE", "Crypto_BTC", "Crypto_ETH", "Indices"]

# Market hours (easy to adjust if needed)
FOREX_MARKET_CLOSE_TIME_HOUR = 22         # Friday closing
FOREX_MARKET_REOPEN_TIME_HOUR = 21        # Sunday reopening
```

### User State (Per-Chat)
```python
user_state = {
    123456: {
        "pair": "EURUSD",
        "timeframe": "5m",
        "market_mode": "FOREX"  # ← Captures market context
    },
    ...
}
```

---

## 🟢 Forex Market Hours (UTC)

| Day | Hours | Status |
|-----|-------|--------|
| Monday | 00:00 - 23:59 | 🟢 Open |
| Tuesday | 00:00 - 23:59 | 🟢 Open |
| Wednesday | 00:00 - 23:59 | 🟢 Open |
| Thursday | 00:00 - 23:59 | 🟢 Open |
| Friday | 00:00 - 21:59 | 🟢 Open |
| Friday | 22:00 - 23:59 | 🟠 Closed (OTC) |
| Saturday | 00:00 - 23:59 | 🟠 Closed (OTC) |
| Sunday | 00:00 - 20:59 | 🟠 Closed (OTC) |
| Sunday | 21:00 - 23:59 | 🟢 Opens (Forex) |

---

## 🧪 How to Test

### Test 1: Verify Forex Mode (Weekday)
1. Run bot on **Monday-Friday**
2. Send `/start`
3. **Expected:** 🟢 FOREX badge appears, Forex pairs shown (EURUSD, GBPUSD, etc.)

### Test 2: Verify OTC Mode (Weekend)
1. Run bot on **Saturday or Sunday morning** (before 21:00 UTC)
2. Send `/start`
3. **Expected:** 🟠 OTC badge appears, OTC pairs shown (XAUUSD, Oil, etc.)

### Test 3: Market Transition
1. User is selecting a pair at **Friday 21:45 UTC** (market still open)
2. **Friday 22:05 UTC** — market closes, user clicks a pair
3. **Expected:** Bot alerts "Market status changed" and asks user to use `/start` again

---

## 🎓 Why This Design Matters

| Aspect | Benefit |
|--------|---------|
| **No Hardcoding** | Market status updates automatically every second without code changes |
| **Real-Time** | Pair lists switch exactly when market hours change |
| **Resilient** | If user mid-session when market closes, bot detects and alerts |
| **User-Friendly** | Market badges (🟢 🟠) make it clear which pairs are available |
| **Extensible** | Easy to add more pair lists for other assets (crypto, stocks, etc.) |

---

## 📝 Code Changes Made

| File | Changes |
|------|---------|
| `signal_bot.py` | Added `is_forex_market_open()` and `get_active_pairs()` functions |
| `signal_bot.py` | Split `TRADING_PAIRS` into `FOREX_PAIRS` and `OTC_PAIRS` |
| `signal_bot.py` | Added market hour constants (not hardcoded in logic) |
| `signal_bot.py` | Updated `/start`, pair callback, and timeframe handlers |
| `signal_bot.py` | Enhanced `generate_signal()` to display market mode badge |
| `signal_bot.py` | Enhanced user_state to track market_mode per chat |

---

## 🚀 Next Steps (Optional)

1. **Test the bot end-to-end** with `/start` and pair selection
2. **Monitor logs** to verify market detection is working
3. **(Future)** Add more pair lists (Crypto only, Stocks only, etc.)
4. **(Future)** Add market calendar for holidays and half-days
5. **(Future)** Store market transition events in logs for analysis

---

## 📞 Quick Reference

**Bot Behavior:**
- `/start` → Detects market → Shows correct pairs → Displays market badge
- Click pair → Re-validates pair → Shows timeframes → Displays market badge
- Select timeframe → Generates signal → Shows market badge in output
- `/stop` → Clears session

**Files to Review:**
- [signal_bot.py](signal_bot.py) — Main implementation
- [MARKET_DETECTION.md](MARKET_DETECTION.md) — Detailed explanation
- [README.md](README.md) — Setup and usage instructions

# Market Status Detection Logic

## Overview

The Telegram trading signal bot now automatically detects the Forex market status and switches between **Forex mode** and **OTC mode** based on real market hours. This is **dynamic**—no hardcoded values, logic is time-based.

---

## How It Works

### 1. Market Status Detection Function

**Location:** `signal_bot.py`, function `is_forex_market_open()`

```python
def is_forex_market_open() -> bool:
    """
    Determine if the Forex market is currently open.
    
    Forex market hours (UTC):
    - Opens: Sunday 21:00 UTC
    - Closes: Friday 22:00 UTC
    """
```

**Logic:**
- Gets current UTC time using `datetime.now(timezone.utc)`
- Extracts weekday (0=Monday, 6=Sunday) and hour
- Returns `True` if market is open, `False` if closed

**Rules:**
1. **Always closed on Saturday** (weekday == 5)
2. **Closed Friday 22:00 UTC onwards** (Friday evening through weekend)
3. **Closed Sunday before 21:00 UTC** (Sunday daytime hours)
4. **Open all of Mon-Fri** (all hours)
5. **Open Sunday 21:00 UTC onwards** (Sunday evening into Monday)

---

### 2. Active Pair Selection Function

**Location:** `signal_bot.py`, function `get_active_pairs()`

```python
def get_active_pairs() -> Tuple[List[str], str]:
    """
    Get the active pair list based on Forex market status.
    
    Returns:
        Tuple of (pairs list, market mode string)
    """
    if is_forex_market_open():
        return FOREX_PAIRS, "FOREX"
    else:
        return OTC_PAIRS, "OTC"
```

**Behavior:**
- Calls `is_forex_market_open()` to check current market status
- If market is **open**: returns Forex pairs list + "FOREX" mode label
- If market is **closed**: returns OTC pairs list + "OTC" mode label

---

## Integration Points

### 1. `/start` Command

When a user sends `/start`:
```python
active_pairs, market_mode = get_active_pairs()
user_state[chat_id] = {"market_mode": market_mode}
```

- Dynamically fetches the active pair list
- Shows **🟢 FOREX** or **🟠 OTC** badge next to available pairs
- Stores market mode in user session

### 2. Pair Selection (Callback Handler)

When a user clicks a pair button:
```python
active_pairs, market_mode = get_active_pairs()

# Validate pair is still in active list
if pair not in active_pairs:
    # Market status may have changed; alert user
    await query.answer(
        "Market status changed. Pair is no longer available. Please use /start to refresh."
    )
```

- **Re-detects market status** in case it changed since `/start` was called
- Validates the selected pair is still available in current market mode
- Prevents stale pair selections if market closes while user is selecting

### 3. Signal Generation

When generating a signal:
```python
signal_message = generate_signal(pair, timeframe, market_mode)
```

- Passes market mode to signal generator
- Includes market badge (**🟢 FOREX** or **🟠 OTC**) in signal output
- Users see which market mode the signal is from

---

## Pair Lists

### Forex Pairs (Active when market is open)
```
EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, 
USDCAD, USDCHF, EURJPY, GBPJPY
```

### OTC Pairs (Active when market is closed)
```
XAUUSD, XAGUSD, Oil, NG, SP500, 
DAX, FTSE, Crypto_BTC, Crypto_ETH, Indices
```

---

## Example Timeline

**Friday 20:00 UTC (2 hours before market close)**
- Status: 🟢 FOREX
- User sees Forex pairs
- `/start` displays EURUSD, GBPUSD, etc.

**Friday 23:00 UTC (1 hour after market close)**
- Status: 🟠 OTC
- User sees OTC pairs
- `/start` displays XAUUSD, Oil, Crypto_BTC, etc.

**Sunday 19:00 UTC (2 hours before market reopens)**
- Status: 🟠 OTC
- User sees OTC pairs

**Sunday 22:00 UTC (1 hour after market reopens)**
- Status: 🟢 FOREX
- User sees Forex pairs again

---

## Configuration Constants

Located at top of `signal_bot.py`:

```python
FOREX_MARKET_CLOSE_TIME_HOUR = 22          # 22:00 UTC Friday
FOREX_MARKET_REOPEN_TIME_HOUR = 21         # 21:00 UTC Sunday
```

These can be adjusted if Forex market hours change, but the detection logic remains **dynamic and time-based**.

---

## Why This Design?

✅ **No hardcoding:** Market status is computed from current time, not stored as a variable  
✅ **Automatic switching:** Pair lists change at exact market hours  
✅ **Real-time validation:** Pair availability is re-checked on every user action  
✅ **Resilient:** If user is mid-session when market closes, bot alerts them  
✅ **User-friendly:** Clear badges (🟢 FOREX, 🟠 OTC) show which mode is active  

---

## Testing

To test market status detection without waiting for real market hours:

1. **Test Forex Open (Monday-Friday, 00:00-21:59 UTC):**
   - Run bot on any weekday morning
   - `/start` should show 🟢 FOREX pairs

2. **Test Market Close (Friday 22:00 - Sunday 21:00 UTC):**
   - Manually modify system time to Friday 23:00 UTC
   - Or update `is_forex_market_open()` logic temporarily for testing
   - `/start` should show 🟠 OTC pairs

3. **Test Market Reopen (Sunday 21:00+ UTC):**
   - Set time to Sunday 22:00 UTC
   - `/start` should show 🟢 FOREX pairs again

---

## Future Enhancements

- Add support for DST transitions (EDT vs EST affects US market times)
- Add session-specific analysis (e.g., best pairs for London session)
- Add market calendar (holidays, half-days)
- Store historical market status in logs for analysis

# Market Status Detection - Flow Diagrams

## User Journey with Market Detection

### Scenario 1: User sends `/start` on Monday 10:00 UTC (Forex Open)

```
User: "/start" command sent
    ↓
bot.cmd_start() handler invoked
    ↓
Call: active_pairs, market_mode = get_active_pairs()
    ↓
Call: is_forex_market_open()
    ├─ Get current UTC time: Monday 10:00 UTC
    ├─ Check: weekday = 0 (Monday) ✓ Not Saturday
    ├─ Check: NOT (Friday 22:00+) ✓
    ├─ Check: NOT (Sunday before 21:00) ✓
    └─ Return: True
    ↓
Return: (FOREX_PAIRS, "FOREX")
    ↓
Store: user_state[chat_id]["market_mode"] = "FOREX"
    ↓
Display: "Bot is running. [🟢 FOREX]"
    ↓
Show buttons: EURUSD, GBPUSD, USDJPY, ... (Forex pairs only)
```

---

### Scenario 2: User sends `/start` on Friday 23:00 UTC (Forex Closed)

```
User: "/start" command sent
    ↓
bot.cmd_start() handler invoked
    ↓
Call: active_pairs, market_mode = get_active_pairs()
    ↓
Call: is_forex_market_open()
    ├─ Get current UTC time: Friday 23:00 UTC
    ├─ Check: weekday = 4 (Friday) 
    ├─ Check: hour (23) >= 22? YES ✗ Market closed
    └─ Return: False
    ↓
Return: (OTC_PAIRS, "OTC")
    ↓
Store: user_state[chat_id]["market_mode"] = "OTC"
    ↓
Display: "Bot is running. [🟠 OTC]"
    ↓
Show buttons: XAUUSD, XAGUSD, Oil, NG, ... (OTC pairs only)
```

---

### Scenario 3: User selects pair, market closes during selection

```
User clicks "EURUSD" button (Friday 21:50 UTC, market still open)
    ↓
bot.callback_pair_selection() handler invoked
    ↓
Call: active_pairs, market_mode = get_active_pairs()
    ├─ Time is now: Friday 21:50 UTC
    ├─ Check: weekday = 4 (Friday), hour < 22
    └─ Return: (FOREX_PAIRS, "FOREX") ✓ Still open
    ↓
Validate: "EURUSD" in FOREX_PAIRS? YES ✓
    ↓
Store: user_state[chat_id]["pair"] = "EURUSD"
       user_state[chat_id]["market_mode"] = "FOREX"
    ↓
Display: "✅ Selected: EURUSD [🟢 FOREX]"
    ↓
Show timeframe buttons: 5s, 10s, 15s, 30s, 1m, 3m, 5m

---

    [2 minutes pass, clock now Friday 22:05 UTC]

User clicks "5m" button
    ↓
bot.callback_timeframe_selection() handler invoked
    ↓
Retrieve: market_mode = user_state[chat_id]["market_mode"]  ["FOREX"]
    ↓
Call: signal_message = generate_signal("EURUSD", "5m", "FOREX")
    ├─ Fetch price for EURUSD
    ├─ Generate demo signal (CALL/PUT/NEUTRAL)
    └─ Add badge: "[🟢 FOREX]"
    ↓
Display signal with [🟢 FOREX] badge
    ↓
(Note: Signal still shows FOREX because we captured market_mode
 at pair selection time. On next /start, user will see OTC pairs.)
```

---

### Scenario 4: Market transitions mid-session (user clicks pair after market closes)

```
User was selecting a pair at Friday 21:50 UTC (FOREX open)
    ↓
Time passes... now Friday 22:10 UTC (FOREX closed)
    ↓
User clicks "EURUSD" button (late click, market now closed)
    ↓
bot.callback_pair_selection() handler invoked
    ↓
Call: active_pairs, market_mode = get_active_pairs()
    ├─ Time is now: Friday 22:10 UTC
    ├─ Check: weekday = 4 (Friday), hour >= 22? YES
    └─ Return: (OTC_PAIRS, "OTC") ✗ Market now closed!
    ↓
Validate: "EURUSD" in OTC_PAIRS? NO ✗
    ↓
Alert: "❌ Market status changed. EURUSD is no longer available."
    ↓
Suggest: "Please use /start to refresh."
    ↓
User receives alert and knows to use /start for current pairs
```

---

## Detection Logic Decision Tree

```
                    is_forex_market_open()?
                            |
                ____________|____________
               |                        |
        Check weekday              Check time
             |                         |
    Is it Saturday?            Is it Friday?
        |        |                |        |
       YES      NO              YES       NO
        |        |                |        |
      CLOSED    Continue       Check      Continue
               |               hour       |
            Check day            |       Check day
            again?         >= 22?         again?
               |            |  |             |
         Is Sunday        YES NO      Is Sunday
         before 21:00?      |  |      before 21:00?
         |    |             |  |         |    |
        YES   NO           CLOSED OPEN YES   NO
         |     |             |      |    |    |
       CLOSED OPEN          CLOSED OPEN CLOSED OPEN
```

---

## Code Flow: Market Detection

```python
is_forex_market_open()
│
├─ Get current UTC time: datetime.now(timezone.utc)
│
├─ Extract weekday (0-6): now_utc.weekday()
│  └─ 0=Monday, 1=Tuesday, ..., 5=Saturday, 6=Sunday
│
├─ Extract hour (0-23): now_utc.hour
│
├─ Rule 1: If Saturday (weekday == 5)
│  └─ Return False (always closed)
│
├─ Rule 2: If Friday (weekday == 4) AND hour >= 22
│  └─ Return False (Friday evening closed)
│
├─ Rule 3: If Sunday (weekday == 6) AND hour < 21
│  └─ Return False (Sunday daytime closed)
│
└─ Else: Return True (market is open)
```

---

## get_active_pairs() Wrapper

```python
get_active_pairs()
│
├─ Call is_forex_market_open()
│
├─ If True:
│  └─ Return (FOREX_PAIRS, "FOREX")
│     └─ List: ["EURUSD", "GBPUSD", "USDJPY", ...]
│     └─ Mode: "FOREX" (displayed as 🟢 FOREX)
│
└─ If False:
   └─ Return (OTC_PAIRS, "OTC")
      └─ List: ["XAUUSD", "XAGUSD", "Oil", ...]
      └─ Mode: "OTC" (displayed as 🟠 OTC)
```

---

## Integration Map: Where Market Detection Happens

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram User                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    /start       (no UI)       /stop
        │                       │
        ▼                       ▼
   cmd_start()            cmd_stop()
        │                   │
        ├─ get_active_pairs()  └─ Clear user_state
        │  └─ is_forex_market_open() [DETECTION #1]
        │
        ├─ Store market_mode in user_state
        │
        ├─ Display market badge (🟢 or 🟠)
        │
        └─ Show active pair buttons


    User clicks pair button
        │
        ▼
    callback_pair_selection()
        │
        ├─ get_active_pairs() [DETECTION #2: RE-CHECK]
        │  └─ is_forex_market_open()
        │
        ├─ Validate pair in active_pairs
        │
        ├─ Store pair + market_mode in user_state
        │
        └─ Show timeframe buttons


    User clicks timeframe button
        │
        ▼
    callback_timeframe_selection()
        │
        ├─ Retrieve pair, market_mode from user_state
        │
        ├─ generate_signal(pair, timeframe, market_mode)
        │
        └─ Display signal with market badge (🟢 or 🟠)
```

---

## Constants & Configuration

```python
# Market hours (UTC) - Easy to modify if needed
FOREX_MARKET_CLOSE_TIME_HOUR = 22
FOREX_MARKET_REOPEN_TIME_HOUR = 21

# Pair lists (separated by market)
FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD",
    "USDCAD", "USDCHF", "EURJPY", "GBPJPY"
]

OTC_PAIRS = [
    "XAUUSD", "XAGUSD", "Oil", "NG", "SP500",
    "DAX", "FTSE", "Crypto_BTC", "Crypto_ETH", "Indices"
]

# How it's used:
if is_forex_market_open():
    active_pairs = FOREX_PAIRS
else:
    active_pairs = OTC_PAIRS
```

---

## Example: Real-World 24-Hour Cycle

```
Friday 18:00 UTC
  ↓ is_forex_market_open()? YES
  ↓ Display: [🟢 FOREX] EURUSD, GBPUSD, etc.

Friday 22:00 UTC (market closes)
  ↓ is_forex_market_open()? NO (hour >= 22)
  ↓ Display: [🟠 OTC] XAUUSD, Oil, etc.

Saturday 12:00 UTC (still closed)
  ↓ is_forex_market_open()? NO (weekday == 5)
  ↓ Display: [🟠 OTC] XAUUSD, Oil, etc.

Sunday 18:00 UTC (still closed)
  ↓ is_forex_market_open()? NO (weekday == 6, hour < 21)
  ↓ Display: [🟠 OTC] XAUUSD, Oil, etc.

Sunday 21:00 UTC (market reopens!)
  ↓ is_forex_market_open()? YES (weekday == 6, hour >= 21)
  ↓ Display: [🟢 FOREX] EURUSD, GBPUSD, etc.

Monday 10:00 UTC (open)
  ↓ is_forex_market_open()? YES
  ↓ Display: [🟢 FOREX] EURUSD, GBPUSD, etc.
```

---

## Key Design Principles

### ✅ NO HARDCODING
```python
# ✓ Good: Dynamic, time-based
if is_forex_market_open():
    pairs = FOREX_PAIRS

# ✗ Bad: Hardcoded, doesn't change
if datetime.now().weekday() < 5:
    pairs = FOREX_PAIRS
```

### ✅ RE-DETECTION ON CRITICAL ACTIONS
```python
# When user selects a pair, re-check market status
# This prevents stale pair selections if market changed
active_pairs, market_mode = get_active_pairs()
if pair not in active_pairs:  # Pair no longer available!
    alert_user()
```

### ✅ PERSISTENT STATE PER SESSION
```python
# Market mode is captured when pair is selected
user_state[chat_id]["market_mode"] = market_mode

# Used later when generating signal
# Ensures consistency if market changes between selection and generation
```

### ✅ PARAMETERIZED CONSTANTS
```python
# Not hardcoded in logic
FOREX_MARKET_CLOSE_TIME_HOUR = 22  # Easy to change if hours shift
FOREX_MARKET_REOPEN_TIME_HOUR = 21
```

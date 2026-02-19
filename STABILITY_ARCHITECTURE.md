# Stability Architecture Diagram

## 🏗️ Error Handling Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                            │
│  /start → pair selection → timeframe → signal                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  cmd_start() Handler               │
         │  [Try-Except wrapper]              │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  get_active_pairs()                │
         │  [Market detection]                │
         │  └─ Validate data                  │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  Send pair selection menu          │
         │  [Try-Except on send]              │
         │  └─ Fallback to text-only          │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  callback_pair_selection()         │
         │  [Try-Except wrapper]              │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  get_active_pairs() (recheck)      │
         │  └─ Ensure consistency             │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  Send timeframe selection menu     │
         │  [Try-Except on send]              │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  callback_timeframe_selection()    │
         │  [Try-Except wrapper]              │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  generate_signal()                 │
         │  [Try-Except wrapper]              │
         └─────────────────┬──────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
         ┌──────▼────────┐      ┌─────▼──────┐
         │fetch_current  │      │Demo signal │
         │rate()         │      │generation  │
         │               │      │            │
         │Try-Except     │      │(Can't fail)│
         │wrapper        │      └────────────┘
         └──────┬────────┘
                │
     ┌──────────┴──────────────────────────────┐
     │                                          │
┌────▼──────────────┐                 ┌────────▼──────────┐
│Alpha Vantage API  │                 │exchangerate.host  │
│(Primary)          │                 │(Fallback)         │
│                   │                 │                   │
│Timeout: 10s       │ ─── FAIL ───┐   │Timeout: 5s        │
│Connection: Yes    │             │   │                   │
│Parse JSON: Yes    │             │   │                   │
│Extract Price: Yes │             └─►Return rate or fail◄─┘
└────────────────────┘
        │
     ┌──┴─────────────────────────┐
     │Success: Return Price        │
     │Fail: Try fallback           │
     │                             │
     └─────────────────┬───────────┘
                       │
        ┌──────────────▼──────────────┐
        │All sources failed?          │
        │                             │
        │Yes → Return None            │
        │  No → Return rate           │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────────┐
        │generate_signal()                │
        │                                 │
        │Price is None?                   │
        │  Yes → Return friendly error    │
        │  No  → Generate signal          │
        └──────────────┬──────────────────┘
                       │
        ┌──────────────▼──────────────────┐
        │Signal message with             │
        │- Pair                          │
        │- Action (BUY/SELL/NEUTRAL)     │
        │- Confidence                    │
        │- Entry Time                    │
        │- Support/Resistance            │
        │- Disclaimer                    │
        └──────────────┬──────────────────┘
                       │
        ┌──────────────▼──────────────────┐
        │Send to user                    │
        │[Try-Except on send]            │
        │└─ Fallback message if fails    │
        └───────────────────────────────┘
```

---

## 🔄 API Failure Recovery Flow

```
User requests signal for EURUSD/5m
│
├─→ fetch_current_rate("EURUSD")
│   │
│   ├─→ Try Alpha Vantage (timeout=10s)
│   │   │
│   │   ├─ Connection OK?
│   │   │  ├─ No → Log warning, continue to fallback
│   │   │  └─ Yes → Fetch data
│   │   │
│   │   ├─ Response is valid JSON?
│   │   │  ├─ No → Log parse error, continue to fallback
│   │   │  └─ Yes → Extract price
│   │   │
│   │   ├─ Price is reasonable (>0)?
│   │   │  ├─ No → Log invalid price, continue to fallback
│   │   │  └─ Yes → Return price ✓
│   │   │
│   │   └─ Timeout after 10 seconds?
│   │      ├─ Yes → Log timeout warning, continue to fallback
│   │      └─ No → (Handled above)
│   │
│   ├─→ Try exchangerate.host (timeout=5s) [only if Alpha failed]
│   │   │
│   │   ├─ Connection OK?
│   │   │  ├─ No → Log warning, return None
│   │   │  └─ Yes → Fetch data
│   │   │
│   │   ├─ Response is valid JSON?
│   │   │  ├─ No → Log parse error, return None
│   │   │  └─ Yes → Extract price
│   │   │
│   │   ├─ Price is reasonable (>0)?
│   │   │  ├─ No → Log invalid price, return None
│   │   │  └─ Yes → Return price ✓
│   │   │
│   │   └─ Timeout after 5 seconds?
│   │      ├─ Yes → Log timeout warning, return None
│   │      └─ No → (Handled above)
│   │
│   └─→ All sources failed?
│       ├─ Yes → Return None (logged)
│       └─ No → (Handled above)
│
├─→ generate_signal() receives price or None
│   │
│   ├─ Price is None?
│   │  ├─ Yes → Return friendly error message ✓
│   │  └─ No → Continue to signal generation
│   │
│   ├─ Generate action, confidence, levels
│   │  (These operations can't fail)
│   │
│   ├─ Format message
│   │  (String operations can't fail)
│   │
│   └─→ Return formatted signal or error message ✓
│
└─→ Send to user via Telegram
    ├─ Send succeeds? → Done ✓
    └─ Send fails? → Log error, try fallback message
```

---

## 🛡️ Exception Handling Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    EXCEPTION HANDLING                        │
└─────────────────────────────────────────────────────────────┘

Layer 1: Handler Level
├─ async def cmd_start(...):
│  ├─ Try: Main logic
│  └─ Except: Log & reply to user
├─ async def callback_pair_selection(...):
│  ├─ Try: Pair selection logic
│  └─ Except: Log & reply to user
└─ async def callback_timeframe_selection(...):
   ├─ Try: Timeframe & signal logic
   └─ Except: Log & reply to user

Layer 2: Function Level
├─ def fetch_current_rate(...):
│  ├─ Try Alpha Vantage: [Try-Except]
│  ├─ Try Fallback: [Try-Except]
│  └─ Except: Log & return None
└─ def generate_signal(...):
   ├─ Validate inputs: [Type checks]
   ├─ Fetch price: [Handled by fetch_current_rate]
   ├─ Validate price: [Type & value checks]
   ├─ Generate components: [Can't fail]
   ├─ Format message: [Can't fail]
   └─ Except: Log & return error message

Layer 3: Operation Level
├─ API calls: [Timeout + exception handling]
├─ JSON parsing: [Try-Except JSONDecodeError]
├─ Type conversion: [Try-Except ValueError]
├─ Dict access: [.get() with defaults]
└─ Message sending: [Try-Except for each send]

Layer 4: Data Validation
├─ Type checking: isinstance()
├─ Value checking: > 0, in list, etc
├─ Structure checking: dict has required keys
└─ Fallback values: Safe defaults

Result: No crash can escape → User always gets response
```

---

## 📊 Logging Flow

```
Event
  │
  ├─ Startup: logger.info("Bot polling started...")
  │
  ├─ User action: logger.info("User %s started bot", chat_id)
  │
  ├─ Normal operation:
  │  └─ logger.debug("Signal generated for %s: %s confidence", pair, conf)
  │
  ├─ API success:
  │  └─ logger.debug("Alpha Vantage rate for %s: %.5f", pair, price)
  │
  ├─ API failure (recoverable):
  │  ├─ logger.warning("Alpha Vantage timeout for %s", pair)
  │  ├─ logger.warning("Fallback API connection error for %s", pair)
  │  └─ logger.error("All rate sources failed for %s", pair)
  │
  ├─ Error (recovered):
  │  ├─ logger.exception("Error in callback_pair_selection")
  │  └─ logger.warning("Could not send error message: %s", e)
  │
  └─ Shutdown: logger.info("Bot shutting down. Final sessions: %d", count)

All logs go to:
├─ Console (INFO and above, real-time)
└─ File (DEBUG and above, rotates at 10MB)
```

---

## 🔄 Automatic Recovery Mechanisms

```
Network Disconnect
  │
  ├─ Detection: Connection refused
  │
  ├─ Telegram library (python-telegram-bot)
  │  ├─ Catch exception
  │  ├─ Log error
  │  └─ Queue for retry
  │
  ├─ Wait 1 second
  │  └─ Exponential backoff on repeated failures
  │
  ├─ Retry connection
  │  ├─ Success? → Resume normal polling
  │  └─ Fail? → Wait 2 seconds, retry
  │
  └─ Network comes back up
     └─ Automatic reconnection, no user action needed

API Timeout
  │
  ├─ Detection: Request > 10 seconds
  │
  ├─ Timeout exception raised
  │  ├─ Log warning
  │  └─ Continue to fallback
  │
  ├─ Try fallback API
  │  ├─ Success? → Return rate
  │  └─ Fail? → Return error message
  │
  └─ User gets signal or friendly error

API Returns Error
  │
  ├─ Detection: Error field in JSON response
  │
  ├─ Log error message
  │  └─ Continue to fallback
  │
  ├─ Try fallback API
  │  ├─ Success? → Return rate
  │  └─ Fail? → Return error message
  │
  └─ User gets signal or friendly error

Both APIs Fail
  │
  ├─ Detection: All sources exhausted
  │
  ├─ Log final error
  │
  ├─ Return None to generate_signal
  │
  ├─ generate_signal checks for None
  │
  ├─ Returns friendly error message
  │
  └─ User sees: "API sources unavailable, try again"
```

---

## 🎯 Safety Guarantees (Visualized)

```
┌────────────────────────────────────────────────────────────┐
│         CAN'T CRASH                  CAN CRASH             │
├────────────────────────────────────────────────────────────┤
│ ✓ API timeout             │ ✗ Unhandled exception          │
│ ✓ API returns error       │ ✗ Missing required field      │
│ ✓ API returns junk        │ ✗ None/null dereference       │
│ ✓ Network disconnect      │ ✗ Type mismatch              │
│ ✓ Malformed JSON          │ ✗ Division by zero           │
│ ✓ Missing fields          │ ✗ Resource leak              │
│ ✓ Invalid data types      │                               │
│ ✓ Handler exception       │ ALL PROTECTED WITH TRY-EXCEPT │
│                           │ AND DATA VALIDATION           │
└────────────────────────────────────────────────────────────┘
```

---

## 📈 Resilience Over Time

```
Time ──────────────────────────────────────────────────→

✓ Bot online (running)
│
├─ Startup (config validation)
├─ API available → signals work
├─ API timeout → fallback works, user gets signal
├─ Network hiccup → auto-reconnect, transparent
├─ API down → user gets error, bot keeps running
├─ High load → slower responses, still works
├─ Day 7 → still running
├─ Day 30 → logs rotated, still running
├─ Month 3 → multiple API failures, all handled
└─ Year 1 → Still running 24/7 ✓

No manual intervention needed (except initial setup)
```

---

## 🎓 Design Principles

```
Defense in Depth
├─ Layer 1: Type validation
├─ Layer 2: Value validation
├─ Layer 3: Exception handling
├─ Layer 4: Fallback logic
└─ Layer 5: Error reporting

Fail Safe
├─ Assume everything can fail
├─ Plan for each failure mode
├─ Never crash, return error instead
└─ Log for debugging

User First
├─ Every error gets a message
├─ Messages are user-friendly
├─ Users know what happened
└─ Users can retry or try another pair

Transparent Logging
├─ All operations logged
├─ Failures captured with context
├─ Debugging is easy
└─ Metrics can be extracted
```

This architecture ensures **zero crash scenarios** while maintaining **complete visibility** through logging.

# Code Locations Reference

This file maps all market detection code to exact locations in `signal_bot.py`.

---

## 📍 Imports (Lines 1-17)

```python
import os
import logging
import random
from datetime import datetime, timezone  # ← ADDED for market detection
from typing import Optional, Dict, List, Tuple  # ← Tuple for get_active_pairs()
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode
```

**Location:** [signal_bot.py](signal_bot.py#L1-L17)

**What was added:**
- `from datetime import datetime, timezone` - For UTC time calculation
- `Tuple` type hint in imports - For return type of `get_active_pairs()`

---

## 📍 Configuration Constants (Lines 30-50)

```python
# Configuration - Pair Lists
# Forex pairs (active during Forex market hours)
FOREX_PAIRS: List[str] = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "NZDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY",
]

# OTC pairs (active when Forex market is closed)
OTC_PAIRS: List[str] = [
    "XAUUSD", "XAGUSD", "Oil", "NG", "SP500",
    "DAX", "FTSE", "Crypto_BTC", "Crypto_ETH", "Indices",
]

TIMEFRAMES: List[str] = ["5s", "10s", "15s", "30s", "1m", "3m", "5m"]

# Forex market hours (UTC): Mon-Fri 00:00 - Fri 22:00, partial Sunday 21:00-23:59
# Closed: Fri 22:00 - Sun 21:00
FOREX_MARKET_OPEN_DAY = 0  # Monday (0-6, where 0=Monday)
FOREX_MARKET_CLOSE_DAY = 4  # Friday
FOREX_MARKET_CLOSE_TIME_HOUR = 22  # 22:00 UTC Friday
FOREX_MARKET_REOPEN_DAY = 6  # Sunday (0-6)
FOREX_MARKET_REOPEN_TIME_HOUR = 21  # 21:00 UTC Sunday
```

**Location:** [signal_bot.py](signal_bot.py#L30-L50)

**What was added:**
- `FOREX_PAIRS` list (separated from original single list)
- `OTC_PAIRS` list (new)
- Market hour constants (FOREX_MARKET_CLOSE_TIME_HOUR, FOREX_MARKET_REOPEN_TIME_HOUR)

---

## 📍 Market Detection Functions (Lines 75-120)

### Function 1: `is_forex_market_open()` 

```python
def is_forex_market_open() -> bool:
    """
    Determine if the Forex market is currently open.
    
    Forex market hours (UTC):
    - Opens: Sunday 21:00 UTC
    - Closes: Friday 22:00 UTC
    
    Returns:
        True if market is open, False if closed (OTC mode).
    """
    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday()  # 0=Monday, 6=Sunday
    hour = now_utc.hour

    # Market closed on Saturdays (weekday=5)
    if weekday == 5:
        return False

    # Market closed Friday 22:00 through Sunday 21:00
    if weekday == 4 and hour >= FOREX_MARKET_CLOSE_TIME_HOUR:  # Friday 22:00+
        return False

    if weekday == 6 and hour < FOREX_MARKET_REOPEN_TIME_HOUR:  # Sunday before 21:00
        return False

    # Market open: Mon-Fri (all hours) and Sunday 21:00+
    return True
```

**Location:** [signal_bot.py](signal_bot.py#L75-L102)

**Key Points:**
- Gets current UTC time: `datetime.now(timezone.utc)`
- Extracts weekday (0-6) and hour (0-23)
- Three rules: Saturday always closed, Friday 22:00+ closed, Sunday before 21:00 closed
- Uses parameterized constants (not hardcoded)

---

### Function 2: `get_active_pairs()`

```python
def get_active_pairs() -> Tuple[List[str], str]:
    """
    Get the active pair list based on Forex market status.
    
    Returns:
        Tuple of (pairs list, market mode string).
        Example: (["EURUSD", ...], "FOREX") or (["XAUUSD", ...], "OTC")
    """
    if is_forex_market_open():
        return FOREX_PAIRS, "FOREX"
    else:
        return OTC_PAIRS, "OTC"
```

**Location:** [signal_bot.py](signal_bot.py#L105-L114)

**Key Points:**
- Calls `is_forex_market_open()` 
- Returns tuple: (pair list, mode string)
- Wrapper function for clean API

---

## 📍 Handler: `/start` Command (Lines 267-325)

```python
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start command: welcome message and pair selection menu.
    Market status is dynamically detected; pairs change based on Forex hours.
    """
    try:
        chat_id = update.effective_chat.id
        
        # Detect market status and get active pairs
        active_pairs, market_mode = get_active_pairs()  # ← MARKET DETECTION #1
        
        # Initialize user session with market mode
        user_state[chat_id] = {"market_mode": market_mode}

        market_badge = "🟢 FOREX" if market_mode == "FOREX" else "🟠 OTC"
        welcome_text = (
            f"Bot is running. [{market_badge}]\n"
            "You will receive trading signals.\n"
            "Use /stop to pause signals.\n\n"
            "📈 Select a trading pair to analyze:"
        )

        # Create pair selection buttons in 2-column grid
        keyboard = []
        for i in range(0, len(active_pairs), 2):
            row = []
            row.append(
                InlineKeyboardButton(
                    active_pairs[i],  # ← Use active pairs from market detection
                    callback_data=f"pair|{active_pairs[i]}"
                )
            )
            if i + 1 < len(active_pairs):
                row.append(
                    InlineKeyboardButton(
                        active_pairs[i + 1],
                        callback_data=f"pair|{active_pairs[i + 1]}"
                    )
                )
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return STATE_PAIR

    except Exception:
        logger.exception("Error in /start handler")
        await update.message.reply_text("❌ An error occurred. Please try again.")
        return -1
```

**Location:** [signal_bot.py](signal_bot.py#L267-L325)

**Market Detection Points:**
- Line 276: `active_pairs, market_mode = get_active_pairs()` ← DETECTION #1
- Line 279: Store market_mode in user_state
- Line 281: Create market badge display
- Line 293: Use active_pairs in button loop (not hardcoded FOREX_PAIRS)

---

## 📍 Handler: Pair Selection Callback (Lines 328-398)

```python
async def callback_pair_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handle pair button selection. Show timeframe menu.
    Market status is re-checked to ensure consistency.
    """
    try:
        query = update.callback_query
        if not query or not query.data:
            return STATE_PAIR

        if not query.data.startswith("pair|"):
            await query.answer()
            return STATE_PAIR

        pair = query.data.split("|", 1)[1]
        chat_id = query.message.chat_id
        
        # Re-detect market status in case it changed
        active_pairs, market_mode = get_active_pairs()  # ← MARKET DETECTION #2 (RE-CHECK)
        
        # Validate pair is still in active list
        if pair not in active_pairs:
            await query.answer(
                f"❌ Market status changed. {pair} is no longer available. Please use /start to refresh.",
                show_alert=True
            )
            return STATE_START

        # Store pair and market mode in user state
        if chat_id not in user_state:
            user_state[chat_id] = {}
        user_state[chat_id]["pair"] = pair
        user_state[chat_id]["market_mode"] = market_mode  # ← Store market mode

        # Show timeframe selection menu with market mode indicator
        market_badge = "🟢 FOREX" if market_mode == "FOREX" else "🟠 OTC"
        timeframe_text = f"✅ Selected pair: *{pair}* [{market_badge}]\n\nNow select a timeframe:"

        keyboard = []
        for i in range(0, len(TIMEFRAMES), 3):
            row = []
            for j in range(3):
                if i + j < len(TIMEFRAMES):
                    tf = TIMEFRAMES[i + j]
                    row.append(
                        InlineKeyboardButton(
                            tf,
                            callback_data=f"tf|{tf}"
                        )
                    )
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.answer()
        await query.edit_message_text(
            timeframe_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return STATE_TIMEFRAME

    except Exception:
        logger.exception("Error in callback_pair_selection")
        await update.callback_query.answer(
            "❌ Error. Please try again.",
            show_alert=True
        )
        return STATE_PAIR
```

**Location:** [signal_bot.py](signal_bot.py#L328-L398)

**Market Detection Points:**
- Line 349: `active_pairs, market_mode = get_active_pairs()` ← DETECTION #2 (RE-CHECK)
- Line 352-358: Validate pair is in active_pairs (market re-validation)
- Line 365-366: Store market_mode in user_state
- Line 369: Create market badge display

---

## 📍 Handler: Timeframe Selection Callback (Lines 401-440)

```python
async def callback_timeframe_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handle timeframe selection. Generate and display signal.
    """
    try:
        query = update.callback_query
        if not query or not query.data:
            return STATE_TIMEFRAME

        if not query.data.startswith("tf|"):
            await query.answer()
            return STATE_TIMEFRAME

        timeframe = query.data.split("|", 1)[1]
        chat_id = query.message.chat_id

        # Validate user state
        if chat_id not in user_state or "pair" not in user_state[chat_id]:
            await query.answer(
                "Session expired. Use /start to begin.",
                show_alert=True
            )
            return STATE_START

        pair = user_state[chat_id]["pair"]
        market_mode = user_state[chat_id].get("market_mode", "FOREX")  # ← Retrieve market_mode
        user_state[chat_id]["timeframe"] = timeframe

        # Generate signal with market mode context
        signal_message = generate_signal(pair, timeframe, market_mode)  # ← Pass market_mode

        await query.answer()
        if signal_message:
            await query.edit_message_text(
                signal_message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text(
                "❌ Error generating signal. Please try again.",
                parse_mode=ParseMode.MARKDOWN
            )

        return STATE_START

    except Exception:
        logger.exception("Error in callback_timeframe_selection")
        await update.callback_query.answer(
            "❌ Error. Please try again.",
            show_alert=True
        )
        return STATE_TIMEFRAME
```

**Location:** [signal_bot.py](signal_bot.py#L401-L440)

**Market Detection Points:**
- Line 425: `market_mode = user_state[chat_id].get("market_mode", "FOREX")` ← Retrieve stored market_mode
- Line 428: `signal_message = generate_signal(pair, timeframe, market_mode)` ← Pass to signal generator

---

## 📍 Function: Signal Generation (Lines 197-234)

```python
def generate_signal(pair: str, timeframe: str, market_mode: str = "FOREX") -> Optional[str]:
    """
    Generate a trading signal for a given pair and timeframe.
    This is a simplified demo generator. In production, implement real
    technical analysis (SMA, RSI, Bollinger Bands, etc.).
    
    Args:
        pair: Trading pair (e.g., "EURUSD")
        timeframe: Time interval (e.g., "1m")
        market_mode: Market mode ("FOREX" or "OTC")  # ← NEW PARAMETER
    
    Returns:
        Formatted signal message or None on error.
    """
    try:
        # Fetch current price
        rate = fetch_current_rate(pair)
        if rate is None:
            return (
                f"❌ Unable to fetch price data for {pair}. "
                f"Please try again later."
            )

        # Demo signal generator (replace with real indicator logic)
        signal = random.choice(["🟢 CALL (Buy)", "🔴 PUT (Sell)", "⚪ NEUTRAL"])
        strength = random.choice(["Strong", "Medium", "Weak"])
        confidence = random.randint(60, 95)
        
        # Add market mode indicator
        market_badge = "🟢 FOREX" if market_mode == "FOREX" else "🟠 OTC"  # ← Market badge

        # Build formatted signal message
        signal_message = (
            f"📊 *SIGNAL ANALYSIS* [{market_badge}]\n\n"  # ← Display badge
            f"*Pair:* {pair}\n"
            f"*Timeframe:* {timeframe}\n"
            f"*Current Price:* {rate:.5f}\n"
            f"*Signal:* {signal}\n"
            f"*Strength:* {strength}\n"
            f"*Confidence:* {confidence}%\n\n"
            f"{DISCLAIMER}"
        )
        return signal_message

    except Exception:
        logger.exception("Error generating signal for %s on %s", pair, timeframe)
        return None
```

**Location:** [signal_bot.py](signal_bot.py#L197-L234)

**Market Detection Points:**
- Line 197: `market_mode: str = "FOREX"` ← NEW parameter (was not in original)
- Line 226: `market_badge = "🟢 FOREX" if market_mode == "FOREX" else "🟠 OTC"` ← Create badge
- Line 229: Include badge in signal message ← Display in output

---

## 📍 User State Definition (Lines 63-65)

```python
# User state: chat_id -> {pair, timeframe, market_mode}
user_state: Dict[int, Dict[str, str]] = {}
```

**Location:** [signal_bot.py](signal_bot.py#L63-L65)

**What was added:**
- Comment updated to include `market_mode` in state tracking

**Structure Example:**
```python
{
    123456: {
        "pair": "EURUSD",
        "timeframe": "5m",
        "market_mode": "FOREX"  # ← NEW field
    },
    789012: {
        "pair": "XAUUSD",
        "timeframe": "1m",
        "market_mode": "OTC"    # ← NEW field
    }
}
```

---

## 📊 Summary of Changes

| Component | Lines | Change Type | Purpose |
|-----------|-------|-------------|---------|
| Imports | 10 | Added | `datetime`, `timezone`, `Tuple` |
| Constants | 38-50 | Modified | Split TRADING_PAIRS → FOREX_PAIRS + OTC_PAIRS, added market hours |
| Functions | 75-114 | Added | `is_forex_market_open()`, `get_active_pairs()` |
| `/start` handler | 276 | Modified | Call `get_active_pairs()` for market detection |
| Pair callback | 349 | Modified | Re-detect market, validate pair |
| Timeframe callback | 425-428 | Modified | Retrieve and pass market_mode |
| Signal generator | 197-234 | Modified | Accept market_mode param, display badge |
| User state | 63-65 | Modified | Now tracks market_mode per chat |

---

## 🔗 Cross-References

**Related Documentation:**
- [MARKET_DETECTION.md](MARKET_DETECTION.md) - Detailed explanation
- [MARKET_DETECTION_SUMMARY.md](MARKET_DETECTION_SUMMARY.md) - Quick summary
- [FLOW_DIAGRAMS.md](FLOW_DIAGRAMS.md) - Visual diagrams
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures

---

## ✅ Checklist: All Market Detection Code

- ✅ Imports added (datetime, timezone, Tuple)
- ✅ Configuration updated (FOREX_PAIRS, OTC_PAIRS, market hours)
- ✅ Detection function implemented (is_forex_market_open)
- ✅ Wrapper function implemented (get_active_pairs)
- ✅ /start handler updated
- ✅ Pair selection callback updated
- ✅ Timeframe selection callback updated
- ✅ Signal generation function updated
- ✅ User state enhanced
- ✅ All integration points working


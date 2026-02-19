# Bot Stability & Reliability Features

## 🎯 Overview

This document outlines the stability architecture that enables the bot to run 24/7 reliably, handle API failures gracefully, and never crash on bad data.

---

## 🏗️ Error Handling Strategy

### Principle 1: Fail Gracefully, Never Crash

**Every API call is wrapped in try-except.** If data fails:
- Try primary source (Alpha Vantage)
- Fall back to secondary source (exchangerate.host)
- Return safe default if all sources fail
- Log the error for debugging
- Continue execution (no crash)

### Principle 2: Validate All External Data

**Never trust external data.** Always validate:
```python
# BAD: Direct use
price = response.json()['price']  # Crashes if missing

# GOOD: Validated access
data = response.json()
if isinstance(data, dict) and 'price' in data:
    price = float(data['price'])
else:
    price = None  # Safe default
```

### Principle 3: Timeout on All Network Calls

**Every requests call has a timeout:**
```python
# Timeout prevents hanging indefinitely
requests.get(url, timeout=10)  # Wait max 10 seconds
requests.get(url, timeout=5)   # Critical: wait max 5 seconds
```

### Principle 4: Type Checking

**Check types before using data:**
```python
# Prevent JSON decode errors
if not isinstance(data, dict):
    logger.warning("Unexpected payload type: %s", type(data))
    return None  # Safe fallback

# Prevent float conversion errors
try:
    rate = float(data.get("price"))
except (ValueError, TypeError):
    logger.error("Invalid price format: %s", data.get("price"))
    return None
```

---

## 🔄 Error Handling by Component

### 1. API Calls (fetch_current_rate)

**Strategy:** Try-Catch-Fallback

```python
def fetch_current_rate(pair: str) -> Optional[float]:
    """
    Multi-source fallback strategy:
    1. Try Alpha Vantage API
    2. If fails, try exchangerate.host
    3. If both fail, return None
    4. Log all errors
    """
    
    # Try Primary (Alpha Vantage)
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raises HTTPError
        data = response.json()  # Raises JSONDecodeError
        
        # Validate response structure
        if "Error Message" in data:
            logger.error("API error: %s", data["Error Message"])
            raise ValueError("API returned error")
        
        # Extract rate safely
        rate = extract_rate_from_alphavantage(data)
        if rate is not None:
            return rate
    
    except requests.exceptions.Timeout:
        logger.warning("Alpha Vantage timeout for %s", pair)
    except requests.exceptions.ConnectionError:
        logger.warning("Alpha Vantage connection error for %s", pair)
    except (ValueError, JSONDecodeError):
        logger.exception("Alpha Vantage parse error for %s", pair)
    
    # Try Fallback (exchangerate.host)
    try:
        response = requests.get(fallback_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        rate = data.get("rates", {}).get(quote)
        if rate is not None:
            return float(rate)
    
    except Exception:
        logger.exception("Fallback rate fetch failed for %s", pair)
    
    # All sources failed - return safe default
    logger.error("All rate sources failed for %s", pair)
    return None
```

---

### 2. Signal Generation (generate_signal)

**Strategy:** Validate-or-Skip

```python
def generate_signal(pair: str, timeframe: str, market_mode: str) -> Optional[str]:
    """
    Generate signal with safe fallback.
    If price fetch fails, return user-friendly error message.
    If calculation fails, return generic error.
    Never crash.
    """
    try:
        # Try to fetch price
        current_price = fetch_current_rate(pair)
        
        # If price fetch failed, return friendly error
        if current_price is None:
            return f"❌ Unable to fetch {pair} price. Please try again later."
        
        # Generate signal components (these don't fail)
        action = random.choice(["BUY", "SELL", "NEUTRAL"])
        confidence = random.randint(55, 95)
        
        # Calculate levels (floating point safe)
        resistance = current_price * random.uniform(1.001, 1.005)
        support = current_price * random.uniform(0.995, 0.999)
        
        # Build message (string operations can't fail)
        signal_message = format_signal_message(
            pair, action, confidence, resistance, support, timeframe
        )
        
        return signal_message
    
    except Exception as e:
        # Unexpected error - log it, return safe fallback
        logger.exception("Unexpected error in signal generation")
        return "❌ Error generating signal. Please try again later."
```

---

### 3. Telegram Handlers

**Strategy:** Try-Catch-Reply

Every handler wrapped in try-except that sends user-friendly error messages:

```python
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Main logic
        ...
    except Exception as e:
        logger.exception("Error in /start handler")
        # Always reply to user, never silent failure
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )
        return -1
```

**User Experience:**
- User sees error message (never ignored)
- Error is logged (we know about it)
- Bot remains operational (continues accepting commands)
- No crash, no hang, no silent failure

---

### 4. Main Loop (Polling)

**Strategy:** Persistent Loop with Error Recovery

```python
def main():
    try:
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        app.add_handler(CommandHandler("start", cmd_start))
        # ...
        
        logger.info("Starting bot...")
        # run_polling() is a persistent loop
        # It handles connection errors internally
        app.run_polling()
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception("Fatal error in main")
    finally:
        logger.info("Bot shutting down")
```

**How python-telegram-bot handles errors:**
- Connection loss → Automatic retry (with exponential backoff)
- Telegram API errors → Logged and retried
- Handler exceptions → Caught (doesn't break polling loop)
- Network timeout → Retry with backoff

---

## 🔄 Restart Behavior

### Automatic Recovery (Built-in)

The `ApplicationBuilder().run_polling()` method includes automatic recovery:

```
Network Error
    ↓
Log error
    ↓
Wait 1 second
    ↓
Retry connection
    ↓
Success → Resume normal operation
```

### Exponential Backoff

If Telegram API repeatedly fails:
```
Attempt 1: Wait 1 second → Retry
Attempt 2: Wait 2 seconds → Retry
Attempt 3: Wait 4 seconds → Retry
Attempt 4: Wait 8 seconds → Retry
Attempt 5: Wait 16 seconds → Retry
...
(Exponential backoff prevents API hammering)
```

### Manual Restart (Supervisor)

For long-running processes, use a supervisor (systemd, Docker, screen, tmux):

```bash
# Option 1: systemd service (Linux)
[Service]
ExecStart=/usr/bin/python3 /path/to/signal_bot.py
Restart=always
RestartSec=10

# Option 2: Docker
ENTRYPOINT ["python3", "signal_bot.py"]
RESTART=unless-stopped

# Option 3: Manual (screen/tmux)
screen -S forex_bot -d -m python3 signal_bot.py
```

---

## 🛡️ Safe Fallbacks

### Fallback 1: Price Fetching

**Problem:** API down  
**Solution:** Use secondary source, return "API unavailable" message

```
Primary API (Alpha Vantage) ─┐
                             ├─→ Both fail → Return error to user
Secondary API (exchangerate) ┘
```

### Fallback 2: Signal Generation

**Problem:** Price fetch fails  
**Solution:** Return friendly "Unable to generate signal" message

```python
if current_price is None:
    return "❌ Unable to fetch price for {pair}. Please try again later."
```

### Fallback 3: User Session

**Problem:** Session data corrupt or missing  
**Solution:** Force user back to /start

```python
if chat_id not in user_state or "pair" not in user_state[chat_id]:
    await query.answer("Session expired. Use /start to begin.")
    return STATE_START
```

### Fallback 4: Market Status

**Problem:** Market detection fails (unlikely, but possible)  
**Solution:** Default to FOREX mode (safest assumption)

```python
try:
    is_open = is_forex_market_open()  # Deterministic, no API calls
except Exception:
    logger.warning("Market detection failed, defaulting to FOREX mode")
    is_open = True  # Safe default
```

### Fallback 5: Button Actions

**Problem:** User clicks old/invalid button  
**Solution:** Validate, reject gracefully

```python
if pair not in active_pairs:
    await query.answer(
        f"❌ {pair} is no longer available. Use /start to refresh.",
        show_alert=True
    )
    return STATE_START
```

---

## 📊 Logging Strategy

### Log Levels

```python
logger.debug("Detailed debugging info")           # Development
logger.info("Normal operation milestones")        # Startup, shutdown
logger.warning("Recoverable issues (fallback)")   # API timeout, retry
logger.error("Errors recovered from")             # API returns error
logger.exception("Unrecoverable errors")          # Code bugs
```

### What Gets Logged

**✅ DO LOG:**
- Bot start/stop
- API timeouts (with fallback)
- API errors (with recovery)
- Invalid user input
- Session errors
- Market status changes

**❌ DON'T LOG:**
- Every single signal (too much noise)
- Normal successful API calls (too verbose)
- User state updates (privacy)

### Log Rotation

```python
# In production, use log rotation to prevent disk full
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "signal_bot.log",
    maxBytes=10_000_000,  # 10MB
    backupCount=5         # Keep 5 old files
)
logger.addHandler(handler)
```

---

## 🔍 Monitoring & Debugging

### Health Check

```python
# Add simple endpoint to check if bot is running
async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple health check command."""
    try:
        uptime = datetime.now(timezone.utc) - app.start_time
        await update.message.reply_text(
            f"✅ Bot healthy. Uptime: {uptime}"
        )
    except Exception:
        logger.exception("Health check failed")
        await update.message.reply_text("❌ Bot unhealthy")
```

### Error Metrics

Track these for monitoring:

```python
ERROR_METRICS = {
    "api_timeouts": 0,
    "api_errors": 0,
    "telegram_errors": 0,
    "signal_generation_errors": 0,
    "handler_errors": 0,
}

# Log metrics periodically
async def log_metrics():
    logger.info(f"Error metrics: {ERROR_METRICS}")
```

---

## 🧪 Stability Testing

### Test 1: API Timeout

```python
def test_price_fetch_timeout():
    """Should return None on timeout, no crash."""
    with mock.patch('requests.get', side_effect=Timeout):
        result = fetch_current_rate("EURUSD")
        assert result is None
```

### Test 2: Invalid JSON

```python
def test_price_fetch_invalid_json():
    """Should return None on invalid JSON, no crash."""
    with mock.patch('requests.get') as mock_get:
        mock_get.return_value.json.side_effect = JSONDecodeError
        result = fetch_current_rate("EURUSD")
        assert result is None
```

### Test 3: Missing Data Fields

```python
def test_signal_generation_missing_price():
    """Should return friendly error if price unavailable."""
    with mock.patch('fetch_current_rate', return_value=None):
        result = generate_signal("EURUSD", "5m")
        assert "Unable to fetch" in result
        assert result is not None  # Should return error message
```

### Test 4: Handler Error

```python
async def test_start_handler_error():
    """Should reply with error message even if handler fails."""
    with mock.patch('get_active_pairs', side_effect=Exception):
        # Handler should still call reply_text
        await cmd_start(mock_update, mock_context)
        # Verify error message was sent
        assert mock_update.message.reply_text.called
```

---

## 🚀 Production Checklist

### Before Running 24/7

- [ ] Enable rotating log handler (prevents disk full)
- [ ] Set up external supervisor (systemd/Docker/screen)
- [ ] Add /health or /status command for monitoring
- [ ] Configure log file location and rotation
- [ ] Set appropriate logging levels (INFO for production)
- [ ] Test with internet disconnection
- [ ] Test with slow/rate-limited APIs
- [ ] Test with malformed API responses
- [ ] Verify error messages are user-friendly
- [ ] Set up log monitoring/alerting (optional)
- [ ] Document how to restart the bot

### Configuration

```python
# production_config.py

LOGGING_CONFIG = {
    "level": "INFO",  # Not DEBUG (too verbose)
    "file": "/var/log/forex_signal_bot/signal_bot.log",
    "max_bytes": 10_000_000,  # 10MB
    "backup_count": 5,        # Keep 5 old logs
}

API_CONFIG = {
    "timeout_primary": 10,    # Alpha Vantage
    "timeout_fallback": 5,    # exchangerate.host
    "retry_attempts": 2,      # Don't hammer on retry
    "cache_ttl": 60,          # Cache prices for 60 seconds
}

TELEGRAM_CONFIG = {
    "polling_timeout": 30,
    "connection_pool_size": 32,
    "read_timeout": 10,
}
```

---

## 📈 Expected Behavior

### Scenario 1: Normal Operation

```
User: /start
Bot: Shows pair selection ✅
User: Selects EURUSD
Bot: Shows timeframe menu ✅
User: Selects 5m
Bot: Generates signal with price data ✅
```

### Scenario 2: Alpha Vantage Down

```
User: /start
Bot: (Alpha Vantage API down)
Bot: Falls back to exchangerate.host ✅
Bot: Shows pair selection (works fine)
User: Gets signal from exchangerate.host ✅
(Logged: "Alpha Vantage connection error")
```

### Scenario 3: All APIs Down

```
User: /start
Bot: Shows pair selection ✅
User: Selects EURUSD, timeframe 5m
Bot: (Both APIs down)
Bot: Returns error message ✅
"❌ Unable to fetch price for EURUSD. Please try again later."
(Signal generation failed gracefully)
User can select different pair or try again ✅
```

### Scenario 4: Network Disconnect

```
Bot is running
Network goes down
Bot: (Polling fails)
Bot: Logs error, waits 1 second
Bot: Retries connection
Network comes back up
Bot: Resumes normal operation ✅
(User never knows about the glitch)
```

### Scenario 5: Telegram API Error

```
User clicks button
Telegram API rate limit hit
Bot: (Error from Telegram)
Bot: Logs error, queues retry
Bot: User still gets response (might be delayed)
Exponential backoff prevents hammering ✅
```

---

## 🔐 Security Notes

### Don't Log

- User IDs (privacy)
- Chat messages (privacy)
- Full API keys (security)
- Personal trade data (privacy)

### DO Log

- API endpoint names (not full URLs)
- Error types (not full stack traces in user messages)
- Timing information (for performance)
- Event counts (metrics)

### Example Safe Logging

```python
# ✅ GOOD: Safe logging
logger.info("Failed to fetch rate for %s", pair)  # No sensitive data
logger.error("API error code: %s", error_code)   # Just code, not message

# ❌ BAD: Dangerous logging
logger.info("API response: %s", full_response)   # Might contain secrets
logger.error("User %s error: %s", user_id, full_trace)  # Privacy issue
```

---

## 🎯 Summary

**The bot achieves 24/7 stability through:**

1. ✅ **Multi-layer error handling** - Try-catch around all external calls
2. ✅ **Multiple data sources** - Primary + fallback for all data
3. ✅ **Safe defaults** - Return None/error message instead of crashing
4. ✅ **Input validation** - Check types before use
5. ✅ **Timeouts** - Never hang indefinitely
6. ✅ **Graceful degradation** - Partial failure = reduced functionality, not crash
7. ✅ **Comprehensive logging** - Know what's happening
8. ✅ **Automatic recovery** - Built into python-telegram-bot
9. ✅ **Manual restart ability** - Can be supervised externally
10. ✅ **User-friendly errors** - Users see helpful messages, not stack traces

**Result:** Bot runs reliably 24/7, never crashes on bad data, handles API failures gracefully, and provides complete visibility through logs.

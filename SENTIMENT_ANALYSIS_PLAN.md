# Optional Sentiment/News Analysis Module - Design Plan

## 📋 Executive Summary

Optional module that pulls **general market sentiment** (risk-on/risk-off) from free public sources and adjusts signal confidence accordingly. Can be disabled if sources unavailable.

---

## 🎯 Core Concept

**Sentiment = Market-wide mood, not signal-specific**

```
Sentiment Analysis:
├─ Risk-On (Bullish) → Increase confidence on BUY signals
├─ Risk-Off (Bearish) → Increase confidence on SELL signals
└─ Neutral → No adjustment (baseline confidence)

Signal Flow:
1. Generate base signal (BUY/SELL/NEUTRAL) → 55-95% confidence
2. Check market sentiment
3. Adjust confidence based on alignment
4. Display final signal

Example:
BUY signal at 70% confidence
+ Risk-on sentiment detected
= Confidence boosted to 78%
```

---

## 📊 Data Sources (Free & Public)

### 1. **Fear & Greed Index** ⭐ (Easiest)

**Source:** Alternative.me (free, no API key needed)

**What it provides:**
- Single score: 0-100
- 0-25 = Extreme Fear (Risk-off)
- 25-45 = Fear
- 45-55 = Neutral
- 55-75 = Greed (Risk-on)
- 75-100 = Extreme Greed

**Endpoint:** `https://api.alternative.me/fng/`

**Sample Response:**
```json
{
  "name": "Fear and Greed Index",
  "data": [
    {
      "value": "72",
      "classification": "Greed",
      "timestamp": "1704639600"
    }
  ],
  "metadata": {
    "error": null
  }
}
```

**Pros:**
- ✅ No authentication needed
- ✅ Free tier unlimited
- ✅ Single reliable metric
- ✅ Works globally

**Cons:**
- ❌ Crypto-focused (but useful for general sentiment)
- ❌ Updated daily (not real-time)

---

### 2. **Market Data Feed** (CoinGecko)

**Source:** CoinGecko free API

**What it provides:**
- Global market cap trends
- Bitcoin dominance
- Altcoin movement
- Market trends

**Endpoint:** `https://api.coingecko.com/api/v3/global`

**Use Case:**
- Detect money flow directions
- Risk-on = crypto rallying
- Risk-off = flight to safety

**Pros:**
- ✅ No API key needed
- ✅ Free tier 10-50 calls/min
- ✅ Real-time data

**Cons:**
- ❌ Crypto-focused (proxy for risk sentiment)

---

### 3. **VIX Proxy** (Crypto Volatility)

**Source:** Alternative.me or CoinGecko

**Concept:**
- High volatility (VIX proxy) = Fear = Risk-off
- Low volatility = Confidence = Risk-on

**How to derive:**
```python
# From price data, calculate volatility
# High volatility (>50) = Risk-off
# Low volatility (<30) = Risk-on
```

---

### 4. **Twitter/X Sentiment** (Optional, Advanced)

**Source:** Free Twitter API v2 (with academic access)

**What it provides:**
- Real-time tweets about forex/trading
- Sentiment through keyword analysis
- Community mood

**Pros:**
- ✅ Real-time
- ✅ Community validated

**Cons:**
- ❌ Requires Twitter API access (free but restricted)
- ❌ NLP analysis needed
- ❌ Noisy data

**Status:** Optional Phase 2

---

### 5. **Reddit Sentiment** (Advanced, Optional)

**Source:** r/forex, r/trading subreddits

**What it provides:**
- Community discussion sentiment
- Real-time trader mood
- Specific pair discussions

**Cons:**
- ❌ Requires API setup
- ❌ Manual scraping complex
- ❌ Limited data per currency pair

**Status:** Optional Phase 2

---

### 6. **Economic Calendar** (Optional)

**Source:** investing.com public data

**What it provides:**
- Upcoming economic events
- Expected vs actual data
- Impact ratings (High/Medium/Low)

**Use Case:**
- Reduce confidence during high-impact events
- Risk-off before major announcements

**Cons:**
- ❌ Requires scraping (complex)
- ❌ Changing HTML breaks code

---

## 🏗️ Architecture Design

### High-Level Flow

```
┌─────────────────────────────────────┐
│  User selects pair + timeframe      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Generate base signal               │
│  (BUY/SELL/NEUTRAL) + confidence    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Fetch market sentiment (optional)  │
│  ├─ Fear & Greed Index              │
│  ├─ Market trends                   │
│  └─ Handle failures gracefully      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Adjust confidence based on         │
│  signal alignment with sentiment    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Display final signal with badge    │
│  📊 TRADING SIGNAL [🟢 Risk-On]     │
└─────────────────────────────────────┘
```

---

### Module Structure

```python
# sentiment_analysis.py (NEW FILE)

class SentimentAnalyzer:
    """
    Optional module for market sentiment analysis.
    Can be disabled if sources unavailable.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.sentiment_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    def get_market_sentiment(self) -> dict:
        """
        Fetch current market sentiment.
        Returns: {
            'status': 'success'|'unavailable',
            'sentiment': 'risk-on'|'risk-off'|'neutral',
            'score': 0-100,
            'source': 'fear-and-greed',
            'timestamp': unix_timestamp
        }
        """
    
    def adjust_signal_confidence(self, 
                                signal_action: str,  # BUY/SELL/NEUTRAL
                                base_confidence: int,
                                sentiment: dict) -> int:
        """
        Adjust confidence based on sentiment alignment.
        """
    
    def get_sentiment_badge(self, sentiment: str) -> str:
        """
        Return badge for sentiment display.
        """

# In signal_bot.py

from sentiment_analysis import SentimentAnalyzer

sentiment_analyzer = SentimentAnalyzer(enabled=True)

async def callback_timeframe_selection(...):
    # Generate base signal
    action = random.choice(["BUY", "SELL", "NEUTRAL"])
    base_confidence = random.randint(55, 95)
    
    # Try to get sentiment (fails gracefully)
    sentiment = sentiment_analyzer.get_market_sentiment()
    
    # Adjust confidence if available
    if sentiment['status'] == 'success':
        final_confidence = sentiment_analyzer.adjust_signal_confidence(
            action, base_confidence, sentiment
        )
    else:
        final_confidence = base_confidence  # Fallback to base
    
    # Generate signal with sentiment info
    signal = generate_signal(pair, timeframe, final_confidence, sentiment)
```

---

## 💡 How Sentiment Affects Signals

### Alignment Concept

**Sentiment increases confidence when aligned with signal:**

```
BUY Signal (action: "BUY")
├─ Risk-On sentiment → Aligned ✅
│  └─ Confidence: +5-10 points
├─ Risk-Off sentiment → Misaligned ❌
│  └─ Confidence: -5-10 points
└─ Neutral sentiment → No change

SELL Signal (action: "SELL")
├─ Risk-Off sentiment → Aligned ✅
│  └─ Confidence: +5-10 points
├─ Risk-On sentiment → Misaligned ❌
│  └─ Confidence: -5-10 points
└─ Neutral sentiment → No change
```

---

### Confidence Adjustment Logic

```python
def adjust_signal_confidence(self, signal_action, base_confidence, sentiment):
    """
    Adjust confidence based on signal-sentiment alignment.
    
    Args:
        signal_action: "BUY", "SELL", or "NEUTRAL"
        base_confidence: 55-95
        sentiment: {
            'sentiment': 'risk-on'|'risk-off'|'neutral',
            'score': 0-100
        }
    
    Returns:
        Adjusted confidence (55-95, capped)
    """
    adjustment = 0
    
    if signal_action == "BUY" and sentiment['sentiment'] == "risk-on":
        # BUY + Risk-on = aligned
        adjustment = +8  # Increase confidence
    elif signal_action == "BUY" and sentiment['sentiment'] == "risk-off":
        # BUY + Risk-off = misaligned
        adjustment = -8  # Decrease confidence
    
    elif signal_action == "SELL" and sentiment['sentiment'] == "risk-off":
        # SELL + Risk-off = aligned
        adjustment = +8
    elif signal_action == "SELL" and sentiment['sentiment'] == "risk-on":
        # SELL + Risk-on = misaligned
        adjustment = -8
    
    # NEUTRAL signals unaffected by sentiment
    
    # Apply adjustment with bounds
    final_confidence = base_confidence + adjustment
    return max(55, min(95, final_confidence))  # Cap at 55-95 range
```

---

### Example Scenarios

**Scenario 1: BUY Signal During Risk-On**
```
Base signal: BUY at 72% confidence
Market sentiment: Risk-On (Fear & Greed = 75)
Alignment: ✅ Perfect match
Action: Increase confidence
Final confidence: 72% + 8% = 80%

Signal Display:
📊 TRADING SIGNAL [🟢 Risk-On]

Pair: EURUSD
Action: BUY ↗️
Timeframe: 5m
Entry Time: Now ← (confidence 80% → "Now")
Confidence: 80% ← (boosted from 72%)
Sentiment: Risk-On 🟢
```

---

**Scenario 2: BUY Signal During Risk-Off**
```
Base signal: BUY at 72% confidence
Market sentiment: Risk-Off (Fear & Greed = 25)
Alignment: ❌ Misaligned
Action: Decrease confidence
Final confidence: 72% - 8% = 64%

Signal Display:
📊 TRADING SIGNAL [🔴 Risk-Off]

Pair: EURUSD
Action: BUY ↗️
Timeframe: 5m
Entry Time: Next 15 minutes ← (confidence 64% → "Next 15 min")
Confidence: 64% ← (reduced from 72%)
Sentiment: Risk-Off 🔴
```

---

**Scenario 3: SELL Signal During Risk-Off**
```
Base signal: SELL at 68% confidence
Market sentiment: Risk-Off (Fear & Greed = 30)
Alignment: ✅ Perfect match
Action: Increase confidence
Final confidence: 68% + 8% = 76%

Signal Display:
📊 TRADING SIGNAL [🔴 Risk-Off]

Pair: GBPUSD
Action: SELL ↘️
Timeframe: 15m
Entry Time: Now ← (confidence 76% → "Now")
Confidence: 76% ← (boosted from 68%)
Sentiment: Risk-Off 🔴
```

---

## 🔌 Module Integration Points

### 1. **Signal Generation (Primary)**

```python
# Before: Just random confidence
action = random.choice(["BUY", "SELL", "NEUTRAL"])
confidence = random.randint(55, 95)

# After: Sentiment-aware confidence
action = random.choice(["BUY", "SELL", "NEUTRAL"])
base_confidence = random.randint(55, 95)
sentiment = sentiment_analyzer.get_market_sentiment()
final_confidence = sentiment_analyzer.adjust_signal_confidence(
    action, base_confidence, sentiment
)
```

---

### 2. **Signal Display (UI Enhancement)**

```python
# Add sentiment badge to signal message
sentiment_badge = "🟢 Risk-On" if sentiment['sentiment'] == "risk-on" else "🔴 Risk-Off"

signal_message = (
    f"📊 TRADING SIGNAL [{sentiment_badge}]\n\n"
    f"Pair: {pair}\n"
    f"Action: {action} {action_symbol}\n"
    f"Timeframe: {timeframe}\n"
    f"Entry Time: {entry_time}\n"
    f"Confidence: {final_confidence}%\n"
    f"Sentiment: {sentiment['sentiment'].upper()}\n\n"
    f"Key Levels:\n"
    f"Resistance: {resistance:.5f}\n"
    f"Support: {support:.5f}\n\n"
    f"{DISCLAIMER}"
)
```

---

### 3. **Configuration (Enable/Disable)**

```python
# In signal_bot.py config section

SENTIMENT_ANALYSIS_ENABLED = os.environ.get(
    "SENTIMENT_ANALYSIS_ENABLED", 
    "true"
).lower() == "true"

sentiment_analyzer = SentimentAnalyzer(
    enabled=SENTIMENT_ANALYSIS_ENABLED
)

# Users can disable via:
# export SENTIMENT_ANALYSIS_ENABLED=false
# python signal_bot.py
```

---

### 4. **Logging & Monitoring**

```python
logger.info(f"Sentiment fetched: {sentiment['sentiment']} (score: {sentiment['score']})")
logger.info(f"Confidence adjusted: {base_confidence}% → {final_confidence}%")

# If sentiment unavailable:
logger.warning("Sentiment analysis unavailable, using base confidence")
```

---

## 🛡️ Graceful Degradation

### What Happens if Sentiment Unavailable?

```python
def get_market_sentiment(self) -> dict:
    try:
        # Try to fetch from Fear & Greed Index
        response = requests.get("https://api.alternative.me/fng/", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        score = int(data['data'][0]['value'])
        
        if score < 45:
            sentiment = "risk-off"
        elif score > 55:
            sentiment = "risk-on"
        else:
            sentiment = "neutral"
        
        return {
            'status': 'success',
            'sentiment': sentiment,
            'score': score,
            'source': 'fear-and-greed',
            'timestamp': int(time.time())
        }
    
    except (requests.RequestException, ValueError, KeyError) as e:
        # Source unavailable - return neutral fallback
        logger.warning(f"Sentiment analysis failed: {e}")
        return {
            'status': 'unavailable',
            'sentiment': 'neutral',
            'score': 50,  # Neutral
            'source': 'fallback',
            'timestamp': int(time.time())
        }
```

**Behavior when unavailable:**
- ✅ Base signal still generated
- ✅ No sentiment adjustment applied
- ✅ Signal confidence unchanged
- ✅ No sentiment badge shown
- ✅ User sees normal signal
- ✅ Log warning for debugging
- ❌ No crash, no error message to user

---

## 📊 Signal Display With Sentiment

### Format 1: Sentiment Available

```
📊 TRADING SIGNAL [🟢 Risk-On]

Pair: EURUSD
Action: BUY ↗️
Timeframe: 5m
Entry Time: Now
Confidence: 80%
Sentiment: RISK-ON

Key Levels:
Resistance: 1.08520
Support: 1.08100

⚠️ DISCLAIMER
...
```

---

### Format 2: Sentiment Unavailable (Graceful Fallback)

```
📊 TRADING SIGNAL

Pair: EURUSD
Action: BUY ↗️
Timeframe: 5m
Entry Time: Now
Confidence: 72%

Key Levels:
Resistance: 1.08520
Support: 1.08100

⚠️ DISCLAIMER
...
```

*(No sentiment badge, uses base confidence)*

---

## 🔄 Data Refresh Strategy

### Caching to Minimize API Calls

```python
class SentimentAnalyzer:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.sentiment_cache = None
        self.cache_timestamp = 0
        self.cache_ttl = 3600  # 1 hour
    
    def _is_cache_valid(self) -> bool:
        """Check if cached sentiment is still valid."""
        return (time.time() - self.cache_timestamp) < self.cache_ttl
    
    def get_market_sentiment(self) -> dict:
        # Return cached if valid
        if self.sentiment_cache and self._is_cache_valid():
            return self.sentiment_cache
        
        # Fetch fresh data
        sentiment = self._fetch_sentiment()
        
        # Cache result
        self.sentiment_cache = sentiment
        self.cache_timestamp = time.time()
        
        return sentiment
```

**Caching benefits:**
- ✅ Reduces API calls (1 per hour max)
- ✅ Faster signal generation
- ✅ Reliability (doesn't block on API delay)
- ✅ Cost effective (free tiers have rate limits)

---

## 🚀 Implementation Roadmap

### Phase 1: MVP (Week 1)
```
✅ Create sentiment_analysis.py
✅ Implement Fear & Greed Index fetch
✅ Add confidence adjustment logic
✅ Integrate into signal generation
✅ Add graceful fallback
✅ Test with mock data
```

### Phase 2: Enhancement (Week 2-3)
```
⏳ Add CoinGecko market data
⏳ Implement volatility analysis
⏳ Add multi-source averaging
⏳ Create sentiment history tracking
⏳ Add admin dashboard for sentiment
```

### Phase 3: Advanced (Week 4+)
```
⏳ Twitter sentiment integration (optional)
⏳ Reddit sentiment scraping (optional)
⏳ Economic calendar integration (optional)
⏳ Machine learning confidence weighting
```

---

## 📝 Configuration

### Environment Variables

```bash
# Enable/disable sentiment analysis
export SENTIMENT_ANALYSIS_ENABLED=true

# Optional: Custom cache TTL (seconds)
export SENTIMENT_CACHE_TTL=3600

# Optional: Which sources to use
export SENTIMENT_SOURCES="fear-and-greed,market-trends"

# Optional: Adjustment intensity (0-10)
export SENTIMENT_ADJUSTMENT_STRENGTH=8
```

### Settings in Config File

```python
# In signal_bot.py or config.py

SENTIMENT_CONFIG = {
    "enabled": True,
    "sources": ["fear-and-greed"],  # Phase 1
    "cache_ttl": 3600,              # 1 hour
    "adjustment_strength": 8,        # ±8% confidence
    "timeout": 5,                    # 5 second timeout
    "fallback_sentiment": "neutral", # If all fail
}
```

---

## ⚠️ Risk & Mitigation

### Risk 1: Sentiment Data Inaccuracy
**Problem:** Fear & Greed Index is crypto-focused  
**Mitigation:** Use as general mood indicator, not pair-specific  
**Impact:** Low (confidence adjustment, not primary signal)

### Risk 2: API Unavailability
**Problem:** Free sources might go down  
**Mitigation:** Graceful fallback to no sentiment  
**Impact:** None (signals work without sentiment)

### Risk 3: False Alignment
**Problem:** Sentiment might be wrong  
**Mitigation:** Only adjust ±8% (not too aggressive)  
**Impact:** Low (small adjustment, still educational)

### Risk 4: Rate Limiting
**Problem:** Free tiers have rate limits  
**Mitigation:** Cache for 1 hour between fetches  
**Impact:** None (caching prevents issues)

---

## 🧪 Testing Strategy

### Unit Tests

```python
def test_sentiment_adjustment_buy_aligned():
    """BUY signal aligned with risk-on should increase confidence."""
    analyzer = SentimentAnalyzer()
    base = 70
    sentiment = {'sentiment': 'risk-on'}
    result = analyzer.adjust_signal_confidence("BUY", base, sentiment)
    assert result > base  # Confidence increased

def test_sentiment_adjustment_buy_misaligned():
    """BUY signal misaligned with risk-off should decrease confidence."""
    analyzer = SentimentAnalyzer()
    base = 70
    sentiment = {'sentiment': 'risk-off'}
    result = analyzer.adjust_signal_confidence("BUY", base, sentiment)
    assert result < base  # Confidence decreased

def test_graceful_fallback():
    """Should handle API failure gracefully."""
    analyzer = SentimentAnalyzer()
    # Mock API failure
    sentiment = analyzer.get_market_sentiment()
    assert sentiment['status'] in ['success', 'unavailable']
    assert 'sentiment' in sentiment
```

### Integration Tests

```python
def test_signal_with_sentiment():
    """Full signal generation with sentiment."""
    signal = generate_signal("EURUSD", "5m", include_sentiment=True)
    assert "TRADING SIGNAL" in signal
    # Might or might not have sentiment badge
    # (depends on API availability)
```

---

## 📊 Example Code: sentiment_analysis.py

```python
"""
Optional market sentiment analysis module.
Can be disabled if data sources unavailable.
"""

import requests
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyzes general market sentiment from free public sources.
    Used to adjust signal confidence based on market-wide mood.
    """
    
    FEAR_GREED_URL = "https://api.alternative.me/fng/"
    TIMEOUT = 5
    CACHE_TTL = 3600  # 1 hour
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.sentiment_cache = None
        self.cache_timestamp = 0
    
    def _is_cache_valid(self) -> bool:
        return (time.time() - self.cache_timestamp) < self.CACHE_TTL
    
    def get_market_sentiment(self) -> Dict:
        """
        Get current market sentiment.
        
        Returns:
            Dict with keys:
            - status: 'success' or 'unavailable'
            - sentiment: 'risk-on', 'risk-off', or 'neutral'
            - score: 0-100 (if available)
            - source: 'fear-and-greed' or 'fallback'
        """
        if not self.enabled:
            return {'status': 'unavailable', 'sentiment': 'neutral', 'score': 50}
        
        # Check cache
        if self.sentiment_cache and self._is_cache_valid():
            return self.sentiment_cache
        
        # Fetch fresh data
        try:
            response = requests.get(self.FEAR_GREED_URL, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            score = int(data['data'][0]['value'])
            
            if score < 45:
                sentiment_type = 'risk-off'
            elif score > 55:
                sentiment_type = 'risk-on'
            else:
                sentiment_type = 'neutral'
            
            result = {
                'status': 'success',
                'sentiment': sentiment_type,
                'score': score,
                'source': 'fear-and-greed'
            }
            
            # Cache result
            self.sentiment_cache = result
            self.cache_timestamp = time.time()
            
            return result
        
        except Exception as e:
            logger.warning(f"Sentiment fetch failed: {e}")
            return {
                'status': 'unavailable',
                'sentiment': 'neutral',
                'score': 50,
                'source': 'fallback'
            }
    
    def adjust_signal_confidence(self, 
                                signal_action: str,
                                base_confidence: int,
                                sentiment: Dict) -> int:
        """
        Adjust signal confidence based on sentiment alignment.
        
        Args:
            signal_action: 'BUY', 'SELL', or 'NEUTRAL'
            base_confidence: 55-95
            sentiment: Dict from get_market_sentiment()
        
        Returns:
            Adjusted confidence (55-95)
        """
        if not self.enabled or sentiment['status'] != 'success':
            return base_confidence
        
        sentiment_type = sentiment['sentiment']
        adjustment = 0
        
        if signal_action == "BUY" and sentiment_type == "risk-on":
            adjustment = +8
        elif signal_action == "BUY" and sentiment_type == "risk-off":
            adjustment = -8
        elif signal_action == "SELL" and sentiment_type == "risk-off":
            adjustment = +8
        elif signal_action == "SELL" and sentiment_type == "risk-on":
            adjustment = -8
        # NEUTRAL signals: no adjustment
        
        final = base_confidence + adjustment
        return max(55, min(95, final))  # Clamp to 55-95
    
    def get_sentiment_badge(self) -> str:
        """Get emoji badge for sentiment."""
        sentiment = self.get_market_sentiment()
        if sentiment['sentiment'] == 'risk-on':
            return "🟢 Risk-On"
        elif sentiment['sentiment'] == 'risk-off':
            return "🔴 Risk-Off"
        else:
            return "⚪ Neutral"
```

---

## 🎯 Non-Financial Language Requirement

**What NOT to say:**
- ❌ "Market is going up" (sounds like advice)
- ❌ "Bullish conditions" (advisory tone)
- ❌ "You should buy now" (financial advice)

**What TO say:**
- ✅ "Risk-on sentiment detected" (factual observation)
- ✅ "Sentiment aligned with BUY signal" (contextual info)
- ✅ "Confidence adjusted based on market mood" (mechanical explanation)

**Example signal with proper language:**
```
📊 TRADING SIGNAL [🟢 Risk-On]

Sentiment Impact:
Market sentiment is risk-on (Fear & Greed: 75).
Your BUY signal aligns with current market mood.
Confidence adjusted from 72% → 80% accordingly.

This is informational only. Make trading decisions
based on your own analysis, not sentiment signals.
```

---

## 🔗 Dependencies

### New Python Package
```
requests>=2.28.0  # Already in requirements.txt
```

No new dependencies needed! Uses only `requests` which is already in project.

---

## ✅ Implementation Checklist

- [ ] Create `sentiment_analysis.py` module
- [ ] Implement `SentimentAnalyzer` class
- [ ] Add Fear & Greed Index fetching
- [ ] Implement confidence adjustment logic
- [ ] Add caching mechanism
- [ ] Implement graceful fallback
- [ ] Integrate into `signal_bot.py`
- [ ] Update signal display format
- [ ] Add environment variable configuration
- [ ] Write unit tests
- [ ] Update documentation
- [ ] Test with real Fear & Greed data
- [ ] Test with unavailable API (fallback)
- [ ] Update requirements.txt (if needed)

---

## 📚 Documentation Updates Needed

### In signal_bot.py
```python
"""
Telegram Trading Signal Bot - Market-Aware Edition

Features:
- Interactive pair and timeframe selection
- On-demand signal generation
- Dynamic market status detection (Forex/OTC)
- Optional sentiment analysis (Risk-On/Risk-Off)
- Professional signal formatting
- Educational disclaimers

Optional Features:
- Sentiment analysis can be disabled via SENTIMENT_ANALYSIS_ENABLED env var
- Gracefully falls back if data sources unavailable
- Does not block signal generation if sentiment fetch fails
"""
```

---

## 🎓 Summary

**Sentiment module will:**

✅ Fetch free market sentiment from Fear & Greed Index  
✅ Adjust signal confidence based on alignment (±8%)  
✅ Display sentiment badge in signals (🟢 🔴)  
✅ Cache data for 1 hour (minimize API calls)  
✅ Gracefully disable if API unavailable  
✅ Not block signal generation  
✅ Use non-financial advisory language  
✅ Be optional (can be disabled entirely)  

**No paid APIs. No financial advice language. No crashes if unavailable.**

---

## 🚀 Next Steps

1. **Review this design** - Feedback on approach?
2. **Approve implementation** - Ready to code?
3. **Code sentiment_analysis.py** - Create module
4. **Integrate into signal_bot.py** - Wire up
5. **Test thoroughly** - All scenarios
6. **Document** - Add to README

Ready to implement Phase 1? 🎯

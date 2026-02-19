# Telegram Trading Signal Bot

A Telegram bot that generates educational trading signals for Forex OTC pairs and other assets. This is a demo/educational tool for learning purposes only—**not intended for real trading**.

## Features

- **Interactive pair selection**: Users select from 10 popular trading pairs (EURUSD, GBPUSD, USDJPY, XAUUSD, etc.)
- **Timeframe menu**: Choose from 7 timeframes (5s, 10s, 15s, 30s, 1m, 3m, 5m)
- **On-demand signal generation**: Signals are generated when user requests them
- **Price fetching**: Real-time price data from Alpha Vantage (with fallback to exchangerate.host)
- **Clear disclaimer**: Every signal includes a disclaimer for educational purposes
- **User state tracking**: Per-user session management

## Commands

- `/start` – Launch the bot and display trading pair menu
- `/stop` – Pause signals and clear user session

## Setup

### Prerequisites
- Python 3.7+
- A Telegram Bot Token (from BotFather)
- (Optional) Alpha Vantage API key for better price data

### Installation

1. Clone or download the project folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Set environment variables:

```bash
# Required
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Optional (recommended for accurate price data)
export ALPHAVANTAGE_API_KEY="your_alpha_vantage_key_here"
```

**Windows (PowerShell)**:
```powershell
$env:TELEGRAM_BOT_TOKEN = "your_bot_token_here"
$env:ALPHAVANTAGE_API_KEY = "your_alpha_vantage_key_here"
```

### Running the Bot

```bash
python signal_bot.py
```

The bot will start polling Telegram for messages. Send `/start` to begin.

## How It Works

1. User sends `/start`
2. Bot displays a grid of trading pairs
3. User selects a pair
4. Bot shows timeframe options
5. User selects a timeframe
6. Bot generates and displays a signal with:
   - Current price
   - Signal direction (CALL/PUT/NEUTRAL)
   - Signal strength (Strong/Medium/Weak)
   - Confidence percentage (60-95%)
   - **Disclaimer** (always included)

## Technical Details

- **Framework**: python-telegram-bot (v20+)
- **Architecture**: Callback-based handlers with inline buttons
- **State tracking**: In-memory dictionary (per-chat session)
- **Price source**: Alpha Vantage FX_INTRADAY + exchangerate.host fallback
- **Signal logic**: Demo randomizer (replace with real technical analysis in production)

## Important Disclaimers

⚠️ **Educational Use Only**

This bot is intended for **educational and demo purposes only**. It does **NOT** provide financial advice and should **NOT** be used for real trading or financial decisions. 

- Past performance does not guarantee future results.
- Always conduct your own research.
- Consult a licensed financial advisor before trading.
- No real broker integration; signals are simulated.

## File Structure

```
forex_signal_bot/
├── signal_bot.py       # Main bot code
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Future Enhancements

- Real technical analysis (SMA, RSI, MACD, Bollinger Bands)
- Persistent subscription database
- Scheduled signal push notifications
- Advanced backtesting framework
- Multi-language support
- Webhook integration with Pocket Option demo accounts

## License

Educational use only. Not for commercial trading.

## Support

For issues or questions, review the logs or check the Telegram bot output for error messages.

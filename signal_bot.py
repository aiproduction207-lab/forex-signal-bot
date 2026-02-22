#!/usr/bin/env python3
"""
Interactive Telegram Forex/OTC Signal Bot (python-telegram-bot v20+).

Features:
- Interactive /start with inline pair selection buttons
- Dynamic timeframe selection (5s, 10s, 15s, 30s, 1m, 3m, 5m)
- Diverse trading signals with RSI, ATR, volatility, trend details
- Session state management for user flow
- Async handlers with v20 syntax

Usage:
  Set TELEGRAM_BOT_TOKEN, then run: python signal_bot.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Optional, Dict, List, Tuple
import random
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from trading_logic import generate_trading_signal
except Exception as e:
    print("FATAL: could not import trading_logic:", e)
    raise

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
logger.addHandler(handler)

# Configuration
# pairs used during normal market hours (7am-5pm local time)
NORMAL_PAIRS = [
    "BTCUSD",
    "CAD/JPY",
    "GBP/JPY",
    "EUR/CAD",
    "EUR/USD",
    "USD/JPY",
    "GBP/AUD",
    "GBP/USD",
    "AUD/JPY",
    "EUR/GBP",
    "EUR/JPY",
    "USD/CNH",
    "AUD/CHF",
    "AUD/CAD",
    # note: EUR/JPY listed twice in original requirements but deduped here
]

# OTC pairs simply append " OTC" to each normal pair when active
# (list generated dynamically)

# timeframes available depending on mode
TIMEFRAMES_NORMAL = ["1m", "3m", "5m", "10m", "15m", "30m", "1h"]  # 15m or higher allowed
TIMEFRAMES_OTC = ["5s", "10s", "15s", "30s", "1m", "3m", "5m"]

# the union is used by validation later
VALID_TIMEFRAMES = set(TIMEFRAMES_NORMAL + TIMEFRAMES_OTC + ["5s", "10s", "15s", "30s"])  # include all possible

# global state for market mode (NORMAL or OTC)
MARKET_MODE: Optional[str] = None


# User session state
user_sessions: Dict = {}

# Simulated market prices
random.seed(42)

MARKET_PRICES = {
    # normal pairs (arbitrary sample prices)
    "BTCUSD": 30000.0,
    "CAD/JPY": 90.25,
    "GBP/JPY": 190.50,
    "EUR/CAD": 1.4450,
    "EUR/USD": 1.0850,
    "USD/JPY": 149.50,
    "GBP/AUD": 1.8000,
    "GBP/USD": 1.2650,
    "AUD/JPY": 105.75,
    "EUR/GBP": 0.8580,
    "EUR/JPY": 162.50,
    "USD/CNH": 7.1400,
    "AUD/CHF": 0.6675,
    "AUD/CAD": 0.9100,
}

# Add OTC variants only for forex pairs (pairs containing '/')
for p, price in list(MARKET_PRICES.items()):
    if "/" in p:
        MARKET_PRICES[p + " OTC"] = price
 


def is_market_hours() -> bool:
    """Return True if current local time is within normal market hours.

    Normal hours are 07:00 (inclusive) to 17:00 (exclusive) local server time.
    Outside that window the bot will run in OTC mode.
    """
    now = datetime.now()
    return 7 <= now.hour < 17


def get_active_pairs() -> Tuple[List[str], str]:
    """Return the list of pairs currently active and a string describing the mode.

    The mode is either "NORMAL" or "OTC".
    """
    if is_market_hours():
        return NORMAL_PAIRS, "NORMAL"
    else:
        # append OTC suffix to forex pairs only (leave BTCUSD unchanged)
        otc_pairs = [p if "/" not in p else p + " OTC" for p in NORMAL_PAIRS]
        return otc_pairs, "OTC"


def get_active_timeframes() -> List[str]:
    """Return the list of valid timeframes for the current mode."""
    return TIMEFRAMES_NORMAL if is_market_hours() else TIMEFRAMES_OTC



def get_current_price(pair: str) -> float:
    """Get current price with slight randomness for demo."""
    base = MARKET_PRICES.get(pair, 1.0)
    change = random.uniform(-0.005, 0.005)
    return base * (1 + change)


def format_signal_message(signal) -> str:
    """Format signal with detailed indicator info."""
    action = getattr(signal, "action", "UNKNOWN")
    if hasattr(action, "value"):
        action = action.value
    
    confidence = getattr(signal, "confidence", 0)
    reasoning = getattr(signal, "reasoning", "No reasoning provided.")
    support = getattr(signal, "support", None)
    resistance = getattr(signal, "resistance", None)
    pair = getattr(signal, "pair", "N/A")
    timeframe = getattr(signal, "timeframe", "N/A")

    # add emoji marker based on confidence
    if confidence >= 75:
        conf_marker = "🟢"  # high confidence
    elif confidence >= 50:
        conf_marker = "🟡"  # moderate confidence
    else:
        conf_marker = "🔴"  # low confidence

    lines = [
        f"*Pair:* {pair} | *Timeframe:* {timeframe}",
        f"*Signal:* {action}",
        f"*Confidence:* {confidence}% {conf_marker}",
        "",
        f"*Analysis:*\n{reasoning}"
    ]

    if support is not None and resistance is not None:
        try:
            lines.append(f"\n*Key Levels:*\nS: {support:.6f} | R: {resistance:.6f}")
        except Exception:
            pass

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pair selection menu based on current market mode."""
    user_id = update.effective_user.id
    user_sessions[user_id] = {}
    
    active_pairs, mode = get_active_pairs()
    badge = "🟢 NORMAL" if mode == "NORMAL" else "🟠 OTC"

    keyboard = []
    for i in range(0, len(active_pairs), 2):
        row = [InlineKeyboardButton(active_pairs[i], callback_data=f"pair_{active_pairs[i]}")]
        if i + 1 < len(active_pairs):
            row.append(InlineKeyboardButton(active_pairs[i+1], callback_data=f"pair_{active_pairs[i+1]}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📈 *Trading Signal Bot* ({badge})\n\nSelect a trading pair:\n━━━━━━━━━━━━━━━━━",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def pair_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pair selection and validate against current mode."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pair = query.data.replace("pair_", "")

    # re-fetch active pairs in case mode changed while user was interacting
    active_pairs, mode = get_active_pairs()
    if pair not in active_pairs:
        await query.edit_message_text(
            "⚠️ Selected pair is no longer available for the current market mode. Please use /start to refresh.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]["pair"] = pair
    
    # Show timeframe buttons for current mode
    tfs = get_active_timeframes()
    keyboard = []
    for i in range(0, len(tfs), 3):
        row = []
        for j in range(3):
            if i + j < len(tfs):
                tf = tfs[i + j]
                row.append(InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ *Selected Pair:* {pair}\n\nNow select a timeframe:\n━━━━━━━━━━━━━━━━━",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def timeframe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle timeframe selection, validate current mode, and generate signal."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in user_sessions or "pair" not in user_sessions[user_id]:
        await query.edit_message_text("Session expired. Use /start to begin.")
        return
    
    timeframe = query.data.replace("tf_", "")
    pair = user_sessions[user_id]["pair"]

    # validate that pair/timeframe still valid for current mode
    active_pairs, mode = get_active_pairs()
    active_tfs = get_active_timeframes()
    if pair not in active_pairs or timeframe not in active_tfs:
        await query.edit_message_text(
            "⚠️ Market mode changed while you were selecting. Please /start again to get updated pairs/timeframes.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    current_price = get_current_price(pair)
    
    await query.edit_message_text(
        f"⏳ Generating signal for {pair} ({timeframe})...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        signal = await asyncio.to_thread(generate_trading_signal, pair, timeframe, current_price)
        message = format_signal_message(signal)
    except Exception as e:
        logger.exception("Error generating signal")
        message = f"❌ Error: {e}"
    
    keyboard = [[InlineKeyboardButton("🔄 New Signal", callback_data="restart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def restart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart signal generation."""
    query = update.callback_query
    await query.answer()
    await start(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help."""
    await update.message.reply_text(
        "*Commands:*\n"
        "/start - Begin signal generation\n"
        "/help - Show this message\n\n"
        "Use inline buttons to select pairs and timeframes.",
        parse_mode=ParseMode.MARKDOWN
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("❌ An error occurred. Use /start to try again.")
    except Exception:
        logger.exception("Failed to send error message")


def build_application(token: str):
    """Build and configure the Telegram bot application."""
    app = ApplicationBuilder().token(token).build()
    
    # initialize market mode state
    global MARKET_MODE
    MARKET_MODE = "NORMAL" if is_market_hours() else "OTC"
    logger.info("Initial market mode: %s", MARKET_MODE)

    # schedule periodic check to update mode and log switches
    def market_mode_job(context: ContextTypes.DEFAULT_TYPE) -> None:
        global MARKET_MODE
        new_mode = "NORMAL" if is_market_hours() else "OTC"
        if new_mode != MARKET_MODE:
            MARKET_MODE = new_mode
            logger.info("Market mode switched to %s", MARKET_MODE)

    # first run after a few seconds to catch startup boundary
    app.job_queue.run_repeating(market_mode_job, interval=30, first=5)

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Callback handlers for interactive buttons
    app.add_handler(CallbackQueryHandler(pair_selection, pattern="^pair_"))
    app.add_handler(CallbackQueryHandler(timeframe_selection, pattern="^tf_"))
    app.add_handler(CallbackQueryHandler(restart_handler, pattern="^restart$"))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    return app


def main() -> None:
    """Main entry point."""
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set. Exiting.")
        sys.exit(1)

    logger.info("Starting Interactive Trading Signal Bot")
    app = build_application(token)

    # let operator know when the polling loop has started
    logger.info("Bot is now running and polling...")
    try:
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception:
        logger.exception("Bot crashed")


if __name__ == "__main__":
    main()

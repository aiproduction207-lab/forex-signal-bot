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
from typing import Optional, Dict
import random

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
FOREX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURJPY", "GBPJPY"]
OTC_PAIRS = ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD"]
ALL_PAIRS = FOREX_PAIRS + OTC_PAIRS

TIMEFRAMES = ["5s", "10s", "15s", "30s", "1m", "3m", "5m"]

# User session state
user_sessions: Dict = {}

# Simulated market prices
random.seed(42)

MARKET_PRICES = {
    "EURUSD": 1.0850,
    "GBPUSD": 1.2650,
    "USDJPY": 149.50,
    "AUDUSD": 0.6750,
    "USDCAD": 1.3450,
    "EURJPY": 162.50,
    "GBPJPY": 189.75,
    "XAUUSD": 2050.00,
    "XAGUSD": 24.50,
    "BTCUSD": 42500.00,
    "ETHUSD": 2250.00,
}


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
    """Show pair selection menu."""
    user_id = update.effective_user.id
    user_sessions[user_id] = {}
    
    keyboard = []
    for i in range(0, len(ALL_PAIRS), 2):
        row = [InlineKeyboardButton(ALL_PAIRS[i], callback_data=f"pair_{ALL_PAIRS[i]}")]
        if i + 1 < len(ALL_PAIRS):
            row.append(InlineKeyboardButton(ALL_PAIRS[i+1], callback_data=f"pair_{ALL_PAIRS[i+1]}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📈 *Trading Signal Bot*\n\nSelect a trading pair:\n━━━━━━━━━━━━━━━━━",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def pair_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pair selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pair = query.data.replace("pair_", "")
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]["pair"] = pair
    
    # Show timeframe buttons
    keyboard = []
    for i in range(0, len(TIMEFRAMES), 3):
        row = []
        for j in range(3):
            if i + j < len(TIMEFRAMES):
                tf = TIMEFRAMES[i + j]
                row.append(InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ *Selected Pair:* {pair}\n\nNow select a timeframe:\n━━━━━━━━━━━━━━━━━",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def timeframe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle timeframe selection and generate signal."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in user_sessions or "pair" not in user_sessions[user_id]:
        await query.edit_message_text("Session expired. Use /start to begin.")
        return
    
    timeframe = query.data.replace("tf_", "")
    pair = user_sessions[user_id]["pair"]
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

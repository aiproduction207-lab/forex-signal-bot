"""
Forex Signal Bot - Telegram Trading Signal Generator
Package initialization
"""

__version__ = "1.0.0"
__author__ = "Trading Bot Team"

# Make modules available at package level
from .trading_logic import generate_trading_signal, SignalAction

__all__ = [
    "generate_trading_signal",
    "SignalAction",
]

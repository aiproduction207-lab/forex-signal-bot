#!/usr/bin/env python3
"""Simple test runner without Unicode characters for Windows"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from trading_logic import generate_trading_signal, SignalAction

def run_simple_tests():
    tests = [
        ("TEST 1", "EURUSD", "15s", 1.0840, [SignalAction.BUY, SignalAction.WAIT], "Oversold Bounce"),
        ("TEST 2", "GBPUSD", "5m", 1.2750, [SignalAction.BUY, SignalAction.WAIT], "Uptrend Pullback"),
        ("TEST 3", "USDJPY", "1m", 145.30, [SignalAction.WAIT], "Flat Market"),
        ("TEST 4", "XAUUSD", "3m", 2050.00, [SignalAction.WAIT], "High Volatility"),
        ("TEST 5", "AUDUSD", "3m", 0.6540, [SignalAction.SELL, SignalAction.WAIT], "Downtrend"),
    ]
    
    passed = 0
    failed = 0
    
    for test_num, pair, timeframe, price, expected_actions, description in tests:
        signal = generate_trading_signal(pair, timeframe, price)
        
        is_pass = signal.action in expected_actions
        status = "PASS" if is_pass else "FAIL"
        
        if is_pass:
            passed += 1
        else:
            failed += 1
        
        print(f"{test_num}: {description:<25} [{timeframe:>3}]")
        print(f"  Pair: {pair}, Price: {price}")
        print(f"  Got: {signal.action.value} (conf: {signal.confidence}%) | Expected: {[a.value for a in expected_actions]}")
        print(f"  Reasoning: {signal.reasoning[:70]}")
        print(f"  RSI calc: Check if indicator calculation correct")
        print(f"  Status: {status}")
        print()
    
    print("="*70)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {passed+failed} tests")
    print(f"Success rate: {100*passed/(passed+failed):.0f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)

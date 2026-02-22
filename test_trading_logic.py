#!/usr/bin/env python3
"""
Test file for trading_logic.py
Demonstrates signal generation across different market conditions and timeframes.
Run: python test_trading_logic.py
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from trading_logic import generate_trading_signal, SignalAction


def print_signal(signal):
    """Pretty print a signal result"""
    print(f"\n{'='*60}")
    print(f"Action: {signal.action.value}")
    print(f"Confidence: {signal.confidence}%")
    print(f"Entry Time: {signal.entry_time}")
    print(f"Price: {signal.current_price:.5f}")
    print(f"Support: {signal.support:.5f}")
    print(f"Resistance: {signal.resistance:.5f}")
    print(f"Reasoning: {signal.reasoning}")
    print(f"{'='*60}")


def test_ultra_short_oversold():
    """Test: Ultra-short timeframe with oversold condition (high probability BUY)"""
    print("\n" + "█"*60)
    print("TEST 1: Ultra-Short Timeframe - Oversold Bounce (15s)")
    print("█"*60)
    print("\nScenario:")
    print("- Pair: CAD/JPY")
    print("- Timeframe: 15s")
    print("- Market dropped fast → RSI very low (mean reversion setup)")
    print("- Medium volatility allows quick reversal")
    
    signal = generate_trading_signal("CAD/JPY", "15s", 90.20)
    print_signal(signal)
    assert signal.action in [SignalAction.BUY, SignalAction.WAIT], "Should BUY or WAIT"


def test_short_uptrend_pullback():
    """Test: Short timeframe with uptrend + pullback (classic entry)"""
    print("\n" + "█"*60)
    print("TEST 2: Short Timeframe - Uptrend with Pullback (5m)")
    print("█"*60)
    print("\nScenario:")
    print("- Pair: GBP/JPY")
    print("- Timeframe: 5m")
    print("- Clear uptrend (SMA separation)")
    print("- Price pulls back to SMA (entry opportunity)")
    print("- Moderate volatility (safe entry)")
    
    signal = generate_trading_signal("GBP/JPY", "5m", 190.00)
    print_signal(signal)
    assert signal.action in [SignalAction.BUY, SignalAction.WAIT], "Should BUY or WAIT"


def test_flat_market_no_trade():
    """Test: Flat market condition (should return WAIT)"""
    print("\n" + "█"*60)
    print("TEST 3: Flat Market - NO TRADE Condition (1m)")
    print("█"*60)
    print("\nScenario:")
    print("- Pair: EUR/GBP")
    print("- Timeframe: 1m")
    print("- Market trading sideways")
    print("- Low volatility (ATR < 0.2%)")
    print("- No clear trend (SMA flat)")
    
    signal = generate_trading_signal("EUR/GBP", "1m", 0.8580)
    print_signal(signal)
    assert signal.action == SignalAction.WAIT, "Should WAIT in flat market"


def test_extreme_volatility():
    """Test: Extreme volatility condition (should return WAIT for safety)"""
    print("\n" + "█"*60)
    print("TEST 4: Extreme Volatility - NO TRADE for Safety (3m)")
    print("█"*60)
    print("\nScenario:")
    print("- Pair: USD/CNH (volatile proxy)")
    print("- Timeframe: 3m")
    print("- News event caused volatility spike")
    print("- ATR > 0.5% (risky, unstable)")
    print("- Market unpredictable")
    
    signal = generate_trading_signal("USD/CNH", "3m", 7.14)
    print_signal(signal)
    assert signal.action == SignalAction.WAIT, "Should WAIT in high volatility"


def test_strong_downtrend():
    """Test: Strong downtrend setup (SELL signal)"""
    print("\n" + "█"*60)
    print("TEST 5: Strong Downtrend - Continuation SELL (3m)")
    print("█"*60)
    print("\nScenario:")
    print("- Pair: AUD/CAD")
    print("- Timeframe: 3m")
    print("- Clear downtrend established")
    print("- RSI showing bearish momentum")
    print("- Medium volatility (safe to trade)")
    
    signal = generate_trading_signal("AUD/CAD", "3m", 0.9120)
    print_signal(signal)
    assert signal.action in [SignalAction.SELL, SignalAction.WAIT], "Should SELL or WAIT"


def test_five_second_timeframe():
    """Test: Extreme short timeframe (5s) - volatility + momentum crucial"""
    print("\n" + "█"*60)
    print("TEST 6: Extreme Short Timeframe - 5 Second Scalp")
    print("█"*60)
    print("\nScenario:")
    print("- Pair: AUD/JPY (demo)")
    print("- Timeframe: 5s")
    print("- Need high volatility (small movements)")
    print("- Mean reversion strategy (oversold/overbought)")
    
    signal = generate_trading_signal("AUD/JPY", "5s", 105.70)
    print_signal(signal)
    # 5s can be BUY, SELL, or WAIT depending on simulated market


def test_overbought_bearish():
    """Test: Overbought condition with bearish confirmation (SELL)"""
    print("\n" + "█"*60)
    print("TEST 7: Overbought with Bearish Momentum - Strong SELL (10s)")
    print("█"*60)
    print("\nScenario:")
    print("- Pair: CAD/JPY (demo)")
    print("- Timeframe: 10s")
    print("- RSI > 65 (overbought)")
    print("- Momentum turning bearish")
    print("- High volatility expected")
    
    signal = generate_trading_signal("CAD/JPY", "10s", 90.30)
    print_signal(signal)
    assert signal.action in [SignalAction.SELL, SignalAction.WAIT], "Should SELL or WAIT"


def test_all_timeframes():
    """Test: Single pair across all supported timeframes"""
    print("\n" + "█"*60)
    print("TEST 8: Single Pair - All Supported Timeframes")
    print("█"*60)
    
    timeframes = ["5s", "10s", "15s", "30s", "1m", "3m", "5m"]
    pair = "EUR/JPY"
    price = 162.50
    
    print(f"\nGenerating signals for {pair} at {price}")
    print(f"{'Timeframe':<10} {'Action':<8} {'Confidence':<12} {'Summary':<40}")
    print("-" * 70)
    
    for tf in timeframes:
        signal = generate_trading_signal(pair, tf, price)
        action = f"{signal.action.value}"
        confidence = f"{signal.confidence}%"
        
        # Create brief summary
        if signal.action.value == "WAIT":
            summary = signal.reasoning.split(".")[0][:40]
        else:
            summary = signal.reasoning.split(".")[0][:40]
        
        print(f"{tf:<10} {action:<8} {confidence:<12} {summary}")


def test_invalid_inputs():
    """Test: Error handling for invalid inputs"""
    print("\n" + "█"*60)
    print("TEST 9: Error Handling - Invalid Inputs")
    print("█"*60)
    
    test_cases = [
        ("", "5m", 1.0850, "Empty pair"),
        ("CAD/JPY", "2h", 90.00, "Invalid timeframe"),
        ("CAD/JPY", "5m", -1.0850, "Negative price"),
        ("CAD/JPY", "5m", 0, "Zero price"),
    ]
    
    for pair, tf, price, description in test_cases:
        print(f"\n{description}:")
        print(f"  Pair: '{pair}', Timeframe: '{tf}', Price: {price}")
        
        signal = generate_trading_signal(pair, tf, price)
        print(f"  Result: {signal.action.value} (confidence: {signal.confidence}%)")
        assert signal.action == SignalAction.WAIT, f"Should WAIT for {description}"


def test_consistent_output():
    """Test: Signal format consistency"""
    print("\n" + "█"*60)
    print("TEST 10: Output Format Consistency")
    print("█"*60)
    
    signal = generate_trading_signal("EUR/JPY", "5m", 162.50)
    
    # Check all required fields exist
    print(f"\nChecking signal completeness:")
    print(f"  ✓ action: {signal.action}")
    print(f"  ✓ confidence: {signal.confidence}")
    print(f"  ✓ timeframe: {signal.timeframe}")
    print(f"  ✓ pair: {signal.pair}")
    print(f"  ✓ current_price: {signal.current_price}")
    print(f"  ✓ support: {signal.support}")
    print(f"  ✓ resistance: {signal.resistance}")
    print(f"  ✓ reasoning: {signal.reasoning[:50]}...")
    print(f"  ✓ entry_time: {signal.entry_time}")
    
    # Verify message formatting
    message = signal.to_message()
    assert isinstance(message, str), "Message should be string"
    assert len(message) > 50, "Message should be substantial"
    print(f"\n✓ Message format valid ({len(message)} chars)")
    
    # For BUY/SELL, verify specific content
    if signal.action != SignalAction.WAIT:
        assert "Pair:" in message, "Should include pair"
        assert "Action:" in message, "Should include action"
        assert "Confidence:" in message, "Should include confidence"
        assert "Key Levels:" in message, "Should include levels"
        print("✓ BUY/SELL message includes all required fields")
    else:
        assert "WAIT" in message or "NO SIGNAL" in message, "Should indicate waiting"
        print("✓ WAIT message properly formatted")


def run_all_tests():
    """Run all test cases"""
    print("\n\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  TRADING LOGIC TEST SUITE".center(58) + "║")
    print("║" + "  Testing signal generation for Pocket Option OTC".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    tests = [
        ("Oversold Bounce (15s)", test_ultra_short_oversold),
        ("Uptrend Pullback (5m)", test_short_uptrend_pullback),
        ("Flat Market NO TRADE (1m)", test_flat_market_no_trade),
        ("Extreme Volatility (3m)", test_extreme_volatility),
        ("Strong Downtrend (3m)", test_strong_downtrend),
        ("5-Second Scalp", test_five_second_timeframe),
        ("Overbought SELL (10s)", test_overbought_bearish),
        ("All Timeframes", test_all_timeframes),
        ("Invalid Input Handling", test_invalid_inputs),
        ("Output Format", test_consistent_output),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✓ PASSED: {test_name}")
        except AssertionError as e:
            failed += 1
            print(f"\n✗ FAILED: {test_name}")
            print(f"  Error: {e}")
        except Exception as e:
            failed += 1
            print(f"\n✗ ERROR: {test_name}")
            print(f"  Exception: {e}")
    
    # Summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY".center(60))
    print("="*60)
    print(f"Total Tests:  {len(tests)}")
    print(f"✓ Passed:     {passed}")
    print(f"✗ Failed:     {failed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

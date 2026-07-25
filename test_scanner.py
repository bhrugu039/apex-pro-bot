"""
Test Scanner - Use specific date
"""

import os
import sys
from datetime import datetime, timedelta

# Set the date to last trading day (e.g., July 24, 2026)
# Adjust this date to the last trading day
TEST_DATE = datetime(2026, 7, 24)  # Format: YYYY, MM, DD

# Override the download function to use specific date
from scanner import download_bhavcopy, get_stock_data, calculate_indicators, TARGET_STOCKS, send_telegram_message

def test_scan():
    print(f"🔍 Testing scanner with data from {TEST_DATE.strftime('%Y-%m-%d')}")
    
    # Test with a few stocks first
    test_stocks = ["IRCTC", "RELIANCE", "TCS", "INFY", "HDFC", "HDFCBANK", "SBIN", "ITC"]
    
    signals = []
    
    for symbol in test_stocks:
        print(f"📊 Fetching data for {symbol}...")
        
        # Get data
        df = get_stock_data(symbol, days=300)
        if df is None or df.empty:
            print(f"⚠️ No data for {symbol}")
            continue
        
        # Calculate indicators
        result = calculate_indicators(df)
        if result is None:
            continue
        
        # Check last bar for buy signal
        last = result.iloc[-1]
        
        if last.get('buy_signal', False):
            signals.append({
                'symbol': symbol,
                'price': last['close'],
                'rsi': last['rsi'],
                'stoch_k': last['stoch_k'],
                'stoch_d': last['stoch_d'],
                'in_deep': last['in_deep'],
                'date': df['date'].iloc[-1]
            })
            print(f"✅ Signal found for {symbol}!")
        else:
            print(f"ℹ️ No signal for {symbol}")
    
    # Print results
    if signals:
        print(f"\n✅ Found {len(signals)} signals:")
        for s in signals:
            print(f"   {s['symbol']}: ₹{s['price']:.2f} | RSI: {s['rsi']:.1f} | {'DEEP' if s['in_deep'] else 'DISCOUNT'}")
    else:
        print("\nℹ️ No signals found")
    
    return signals

if __name__ == "__main__":
    test_scan()
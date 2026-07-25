"""
APEX PRO - NSE Bhavcopy Scanner
Scans all NSE stocks daily for APEX ADIV buy signals
"""

import os
import re
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from io import BytesIO
import zipfile
import json

# ============ CONFIGURATION ============
BOT_TOKEN = "8962365949:AAHhoTogxKuhW_Pta7yXjRqCoJTFtBhPZd8"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = "728405872"

# Scanner parameters (matching your PineScript)
ZONE_LOOKBACK = 252
DEEP_PCT = 0.25
RSI_LEN = 14
STOCH_RSI_LEN = 14
STOCH_LEN = 14
STOCH_THRESH = 20

# ============ STOCK LIST ============
TARGET_STOCKS = [
    "IRCTC", "RELIANCE", "TCS", "INFY", "WIPRO",
    "HDFC", "HDFCBANK", "ICICI", "SBIN", "ITC",
    "TATAMOTORS", "TATACONSUM", "TATASTEEL", "TATAPOWER",
    "ONGC", "MARUTI", "SUZLON", "ZOMATO", "PAYTM",
    "DMART", "NYKAA", "HAL", "ADANIENT", "ADANIPORTS",
    "BAJFINANCE", "BAJAJFINSV", "LT", "TITAN", "ASIANPAINT",
    "HINDUNILVR", "NTPC", "POWERGRID", "ULTRACEMCO",
    "AXISBANK", "KOTAKBANK", "BHARTIARTL", "HCLTECH", "TECHM",
    "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "BIOCON",
    "JSWSTEEL", "COALINDIA", "VEDL", "HINDALCO", "NMDC",
    "PFC", "RECLTD", "IRFC", "IREDA", "RVNL",
    "BANKBARODA", "PNB", "CANBK", "UNIONBANK", "INDUSINDBK",
    "FEDERALBNK", "BANDHANBNK", "AUBANK", "YESBANK", "IDFCFIRST",
    "IOC", "BPCL", "HPCL", "GAIL", "M&M",
    "EICHERMOT", "HEROMOTOCO", "TVSMOTOR", "BAJAJ-AUTO",
    "TITAGARH", "VOLTAS", "SIEMENS", "ABB", "BHEL",
    "THERMAX", "KEC", "ENGINEERSIND", "NBCC", "IRB",
    "JUBLFOOD", "DEVYANI", "SAPPHIRE", "RESTAURANT",
    "BARBEQUE", "TRENT", "POLYCAB", "HAVELLS", "NESTLEIND",
    "BRITANNIA", "DABUR", "MARICO", "GODREJCP", "PIDILITIND",
    "EMAMILTD", "TORNTPHARM", "LUPIN", "GLENMARK", "SYNGENE",
    "LAURUSLABS", "APOLLOHOSP", "FORTIS", "MAXHEALTH", "NARAYANHOSP",
    "KIMS", "RAINBOW", "AMBUJACEM", "ACC", "RAMCOCEM",
    "DALBHARAT", "JKLAKSHMI", "BIRLACORPN", "HINDZINC",
    "NATIONALUM", "MOIL", "SAIL", "JINDALSTEL", "JINDALSAW",
    "SJVN", "NHPC", "ADANIGREEN", "ADANITRANS", "ADANIENSOL",
    "ADANITOTAL", "ADANIWILMAR", "ADANIPOWER", "JSWENERGY"
]

# ============ NSE BHAVCOPY FUNCTIONS ============
def download_bhavcopy(date):
    """Download NSE bhavcopy for a given date"""
    try:
        date_str = date.strftime("%d%m%Y")
        
        # Try multiple sources
        urls = [
            f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date.strftime('%Y%m%d')}_F_0000.csv.zip",
            f"https://www.nseindia.com/api/equity-stock?csv=true&date={date_str}",
            f"https://archives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date.strftime('%Y%m%d')}_F_0000.csv.zip"
        ]
        
        for url in urls:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive'
                }
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    # Try to unzip
                    try:
                        with zipfile.ZipFile(BytesIO(response.content)) as z:
                            csv_filename = z.namelist()[0]
                            df = pd.read_csv(z.open(csv_filename))
                            return df
                    except:
                        # If not zip, try direct CSV
                        df = pd.read_csv(BytesIO(response.content))
                        return df
            except:
                continue
        
        print(f"⚠️ No data for {date.strftime('%Y-%m-%d')}")
        return None
        
    except Exception as e:
        print(f"❌ Error downloading bhavcopy: {e}")
        return None


def get_stock_data(symbol, days=300):
    """Get historical data for a stock from NSE archives"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    all_data = []
    current_date = start_date
    
    print(f"📊 Fetching data for {symbol}...")
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:
            df = download_bhavcopy(current_date)
            if df is not None:
                # Find the symbol
                symbol_df = df[df['SYMBOL'] == symbol]
                if not symbol_df.empty:
                    row = symbol_df.iloc[0]
                    all_data.append({
                        'date': current_date,
                        'open': row.get('OPEN', 0),
                        'high': row.get('HIGH', 0),
                        'low': row.get('LOW', 0),
                        'close': row.get('CLOSE', 0),
                        'volume': row.get('TOTTRDQTY', 0)
                    })
        
        current_date += timedelta(days=1)
        time.sleep(0.1)  # Rate limiting
    
    if not all_data:
        return None
    
    df = pd.DataFrame(all_data)
    if df.empty or len(df) < 50:
        return None
    
    return df


# ============ APEX ADIV INDICATOR ============
def calculate_indicators(df):
    """Calculate all indicators for APEX ADIV"""
    
    if df is None or len(df) < 50:
        return None
    
    df = df.copy()
    
    # Calculate RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=RSI_LEN).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_LEN).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Calculate StochRSI
    rsi_min = df['rsi'].rolling(window=STOCH_RSI_LEN).min()
    rsi_max = df['rsi'].rolling(window=STOCH_RSI_LEN).max()
    stoch_rsi = (df['rsi'] - rsi_min) / (rsi_max - rsi_min)
    df['stoch_k'] = stoch_rsi.rolling(window=STOCH_LEN).mean() * 100
    df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
    
    # Zone calculation
    df['hh'] = df['high'].rolling(window=ZONE_LOOKBACK).max()
    df['ll'] = df['low'].rolling(window=ZONE_LOOKBACK).min()
    df['range'] = df['hh'] - df['ll']
    df['equilibrium'] = (df['hh'] + df['ll']) / 2
    df['deep_line'] = df['ll'] + df['range'] * DEEP_PCT
    df['in_discount'] = df['close'] < df['equilibrium']
    df['in_deep'] = df['close'] < df['deep_line']
    
    # Find RSI pivot lows
    pivot_condition = (
        (df['rsi'].shift(1) > df['rsi']) &
        (df['rsi'].shift(2) > df['rsi']) &
        (df['rsi'].shift(-1) > df['rsi']) &
        (df['rsi'].shift(-2) > df['rsi'])
    )
    df['rsi_pivot_low'] = np.where(pivot_condition, df['rsi'], np.nan)
    df['price_at_pivot'] = np.where(pivot_condition, df['low'], np.nan)
    
    # Detect regular bullish divergence
    df['prev_rsi_low'] = df['rsi_pivot_low'].shift(1)
    df['prev_price_low'] = df['price_at_pivot'].shift(1)
    df['prev_pivot_bar'] = df.index.shift(1)
    
    # Divergence condition: price lower low, RSI higher low
    df['price_lower_low'] = df['low'] < df['prev_price_low']
    df['rsi_higher_low'] = df['rsi'] > df['prev_rsi_low']
    
    # StochRSI oversold
    df['stoch_oversold'] = (df['stoch_k'] < STOCH_THRESH) & (df['stoch_d'] < STOCH_THRESH)
    
    # Final buy signal
    df['bull_div'] = (
        df['prev_rsi_low'].notna() &
        df['prev_price_low'].notna() &
        df['price_lower_low'] &
        df['rsi_higher_low']
    )
    
    df['buy_signal'] = (
        df['bull_div'] &
        df['in_discount'] &
        df['stoch_oversold']
    )
    
    df['deep_buy'] = df['buy_signal'] & df['in_deep']
    
    return df


# ============ TELEGRAM FUNCTIONS ============
def send_telegram_message(message):
    """Send message to Telegram"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return None


def send_alert(signal):
    """Send APEX ADIV alert for a stock"""
    
    alert_type = "🚨 **DEEP DISCOUNT BUY!**" if signal['in_deep'] else "🔵 **DISCOUNT BUY!**"
    
    message = f"""
{alert_type}

📊 *{signal['symbol']}*
💰 Price: ₹{signal['price']:.2f}
📈 RSI: {signal['rsi']:.1f}
📉 Stoch K: {signal['stoch_k']:.1f} | Stoch D: {signal['stoch_d']:.1f}
📅 Date: {signal['date'].strftime('%d %b %Y')}

✅ *APEX ADIV Conditions Met:*
• RSI Bullish Divergence ✅
• Discount Zone ✅
• StochRSI Oversold ✅
{"• Deep Discount Zone ✅" if signal['in_deep'] else ""}

🔍 Running APEX PRO Analysis...
"""
    
    send_telegram_message(message)
    
    # Call APEX analysis from bot
    try:
        from bot import analyze_stock_from_symbol
        analyze_stock_from_symbol(signal['symbol'])
    except:
        # If bot not imported, send basic info
        send_telegram_message(f"📊 APEX PRO Analysis for {signal['symbol']} is ready!")


def scan_and_notify():
    """Main scanner function"""
    
    print("🚀 APEX PRO Scanner Started")
    print(f"📊 Scanning {len(TARGET_STOCKS)} stocks...")
    
    signals_found = []
    
    for symbol in TARGET_STOCKS:
        print(f"🔍 Scanning {symbol}...")
        
        try:
            # Get historical data
            df = get_stock_data(symbol)
            if df is None or df.empty:
                continue
            
            # Calculate indicators
            result = calculate_indicators(df)
            if result is None:
                continue
            
            # Check last bar for buy signal
            last = result.iloc[-1]
            
            if last.get('buy_signal', False):
                signals_found.append({
                    'symbol': symbol,
                    'price': last['close'],
                    'rsi': last['rsi'],
                    'stoch_k': last['stoch_k'],
                    'stoch_d': last['stoch_d'],
                    'in_deep': last['in_deep'],
                    'date': df['date'].iloc[-1]
                })
                
        except Exception as e:
            print(f"⚠️ Error scanning {symbol}: {e}")
            continue
        
        time.sleep(0.5)  # Rate limiting
    
    # Send alerts
    if signals_found:
        print(f"✅ Found {len(signals_found)} signals!")
        for signal in signals_found:
            send_alert(signal)
    else:
        print("ℹ️ No signals found today")
        send_telegram_message("📊 *APEX PRO Scanner*\n\nℹ️ No buy signals found today.")
    
    return signals_found


def run_scanner():
    """Run scanner and send summary"""
    
    print(f"📅 Scanner started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        signals = scan_and_notify()
        
        # Send summary
        summary = f"""
📊 *APEX PRO Scanner Summary*
📅 {datetime.now().strftime('%d %b %Y')}

🔍 Stocks Scanned: {len(TARGET_STOCKS)}
✅ Signals Found: {len(signals)}

"""
        if signals:
            summary += "*Signals:*\n"
            for s in signals:
                summary += f"• {s['symbol']} ₹{s['price']:.2f} {'(DEEP)' if s['in_deep'] else ''}\n"
        else:
            summary += "No signals found today."
        
        send_telegram_message(summary)
        
    except Exception as e:
        error_msg = f"❌ Scanner error: {e}"
        print(error_msg)
        send_telegram_message(error_msg)


# ============ MAIN ============
if __name__ == "__main__":
    run_scanner()
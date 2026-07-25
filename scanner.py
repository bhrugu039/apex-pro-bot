"""
APEX PRO - NSE Bhavcopy Scanner
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from io import BytesIO
import zipfile

# ============ CONFIGURATION ============
BOT_TOKEN = "8962365949:AAHhoTogxKuhW_Pta7yXjRqCoJTFtBhPZd8"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = "728405872"

# Scanner parameters
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
]

# ============ BHAVCOPY FUNCTIONS ============
def download_bhavcopy(date):
    """Download NSE bhavcopy"""
    try:
        urls = [
            f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date.strftime('%Y%m%d')}_F_0000.csv.zip",
            f"https://archives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date.strftime('%Y%m%d')}_F_0000.csv.zip",
        ]
        
        for url in urls:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                }
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    with zipfile.ZipFile(BytesIO(response.content)) as z:
                        csv_filename = z.namelist()[0]
                        df = pd.read_csv(z.open(csv_filename))
                        return df
            except:
                continue
        
        return None
        
    except Exception as e:
        return None

def get_stock_data(symbol, days=300):
    """Get historical data for a stock"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    all_data = []
    current_date = start_date
    
    print(f"   Fetching {symbol}...")
    
    while current_date <= end_date:
        if current_date.weekday() < 5:
            df = download_bhavcopy(current_date)
            if df is not None:
                # Find symbol column
                symbol_col = None
                for col in df.columns:
                    if col.upper().strip() in ['SYMBOL', 'SYMBOL ', 'SC_NAME', 'SECURITY']:
                        symbol_col = col
                        break
                
                if symbol_col is None and len(df.columns) > 0:
                    symbol_col = df.columns[0]
                
                if symbol_col is None:
                    current_date += timedelta(days=1)
                    continue
                
                # Find price columns
                close_col = None
                open_col = None
                high_col = None
                low_col = None
                volume_col = None
                
                for col in df.columns:
                    col_upper = col.upper().strip()
                    if col_upper in ['CLOSE', 'CLOSING_PRICE', 'LAST']:
                        close_col = col
                    elif col_upper in ['OPEN']:
                        open_col = col
                    elif col_upper in ['HIGH']:
                        high_col = col
                    elif col_upper in ['LOW']:
                        low_col = col
                    elif col_upper in ['TOTTRDQTY', 'VOLUME']:
                        volume_col = col
                
                if close_col is None:
                    current_date += timedelta(days=1)
                    continue
                
                # Find the symbol
                try:
                    symbol_df = df[df[symbol_col].astype(str).str.strip() == symbol]
                except:
                    symbol_df = df[df[symbol_col] == symbol]
                
                if not symbol_df.empty:
                    row = symbol_df.iloc[0]
                    try:
                        close_val = float(row[close_col]) if close_col in row else 0
                        open_val = float(row[open_col]) if open_col and open_col in row else 0
                        high_val = float(row[high_col]) if high_col and high_col in row else 0
                        low_val = float(row[low_col]) if low_col and low_col in row else 0
                        volume_val = float(row[volume_col]) if volume_col and volume_col in row else 0
                        
                        if close_val > 0:
                            all_data.append({
                                'date': current_date,
                                'open': open_val,
                                'high': high_val,
                                'low': low_val,
                                'close': close_val,
                                'volume': volume_val
                            })
                    except:
                        pass
        
        current_date += timedelta(days=1)
        time.sleep(0.05)
    
    if not all_data or len(all_data) < 50:
        return None
    
    return pd.DataFrame(all_data)

# ============ INDICATOR CALCULATIONS ============
def calculate_indicators(df):
    """Calculate all indicators"""
    
    if df is None or len(df) < 50:
        return None
    
    df = df.copy()
    
    try:
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=RSI_LEN).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_LEN).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # StochRSI
        rsi_min = df['rsi'].rolling(window=STOCH_RSI_LEN).min()
        rsi_max = df['rsi'].rolling(window=STOCH_RSI_LEN).max()
        stoch_rsi = (df['rsi'] - rsi_min) / (rsi_max - rsi_min)
        df['stoch_k'] = stoch_rsi.rolling(window=STOCH_LEN).mean() * 100
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        # Zones
        df['hh'] = df['high'].rolling(window=ZONE_LOOKBACK).max()
        df['ll'] = df['low'].rolling(window=ZONE_LOOKBACK).min()
        df['range'] = df['hh'] - df['ll']
        df['equilibrium'] = (df['hh'] + df['ll']) / 2
        df['deep_line'] = df['ll'] + df['range'] * DEEP_PCT
        df['in_discount'] = df['close'] < df['equilibrium']
        df['in_deep'] = df['close'] < df['deep_line']
        
        # Pivot detection
        pivot_condition = (
            (df['rsi'].shift(1) > df['rsi']) &
            (df['rsi'].shift(2) > df['rsi']) &
            (df['rsi'].shift(-1) > df['rsi']) &
            (df['rsi'].shift(-2) > df['rsi'])
        )
        df['rsi_pivot_low'] = np.where(pivot_condition, df['rsi'], np.nan)
        df['price_at_pivot'] = np.where(pivot_condition, df['low'], np.nan)
        
        # Divergence
        df['prev_rsi_low'] = df['rsi_pivot_low'].shift(1)
        df['prev_price_low'] = df['price_at_pivot'].shift(1)
        df['price_lower_low'] = df['low'] < df['prev_price_low']
        df['rsi_higher_low'] = df['rsi'] > df['prev_rsi_low']
        df['stoch_oversold'] = (df['stoch_k'] < STOCH_THRESH) & (df['stoch_d'] < STOCH_THRESH)
        
        df['bull_div'] = (
            df['prev_rsi_low'].notna() &
            df['prev_price_low'].notna() &
            df['price_lower_low'] &
            df['rsi_higher_low']
        )
        
        df['buy_signal'] = df['bull_div'] & df['in_discount'] & df['stoch_oversold']
        df['deep_buy'] = df['buy_signal'] & df['in_deep']
        
        return df
        
    except Exception as e:
        print(f"   Indicator error: {e}")
        return None

# ============ SEND TELEGRAM ALERT ============
def send_telegram_message(message):
    """Send message to Telegram"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# ============ MAIN ============
if __name__ == "__main__":
    print("🚀 APEX PRO Scanner Started")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    signals = []
    
    for symbol in TARGET_STOCKS:
        print(f"\n📊 Scanning {symbol}...")
        
        try:
            df = get_stock_data(symbol, days=300)
            if df is None or df.empty:
                print(f"   ❌ No data")
                continue
            
            print(f"   ✅ {len(df)} data points")
            print(f"   📅 Latest: {df['date'].iloc[-1].strftime('%Y-%m-%d')}")
            
            result = calculate_indicators(df)
            if result is None:
                continue
            
            last = result.iloc[-1]
            print(f"   💰 ₹{last['close']:.2f} | RSI: {last['rsi']:.1f} | Buy: {last['buy_signal']}")
            
            if last.get('buy_signal', False):
                signals.append(symbol)
                print(f"   ✅ *** BUY SIGNAL! ***")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Signals Found: {len(signals)}")
    
    if signals:
        print(f"✅ {', '.join(signals)}")
        # Send Telegram alert
        alert_msg = f"🚨 *APEX ADIV Signals Found!*\n\n"
        for s in signals:
            alert_msg += f"✅ {s}\n"
        send_telegram_message(alert_msg)
    else:
        print("ℹ️ No signals found")

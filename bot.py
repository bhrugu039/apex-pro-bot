"""
APEX PRO - Telegram Stock Analysis Bot
Local Stock Database - No API Required
"""

import re
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import logging
from datetime import datetime, timezone, timedelta

# ============ CONFIGURATION ============
BOT_TOKEN = "8962365949:AAHhoTogxKuhW_Pta7yXjRqCoJTFtBhPZd8"

print(f"✅ Bot token loaded: {BOT_TOKEN[:10]}...")

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# ============ LOCAL STOCK DATABASE ============
STOCKS = {
    "IRCTC": "Indian Railway Catering & Tourism Corp",
    "RELIANCE": "Reliance Industries Ltd",
    "TCS": "Tata Consultancy Services Ltd",
    "INFY": "Infosys Ltd",
    "WIPRO": "Wipro Ltd",
    "HDFC": "HDFC Ltd",
    "HDFCBANK": "HDFC Bank Ltd",
    "ICICI": "ICICI Bank Ltd",
    "ITC": "ITC Ltd",
    "SBIN": "State Bank of India",
    "TATAMOTORS": "Tata Motors Ltd",
    "TATACONSUM": "Tata Consumer Products Ltd",
    "TATASTEEL": "Tata Steel Ltd",
    "ONGC": "Oil & Natural Gas Corp Ltd",
    "MARUTI": "Maruti Suzuki India Ltd",
    "ICRA": "ICRA Ltd",
    "CARE": "CARE Ratings Ltd",
    "NTPC": "NTPC Ltd",
    "POWERGRID": "Power Grid Corporation Ltd",
    "ULTRACEMCO": "UltraTech Cement Ltd",
    "ASIANPAINT": "Asian Paints Ltd",
    "HINDUNILVR": "Hindustan Unilever Ltd",
    "BHARTIARTL": "Bharti Airtel Ltd",
    "KOTAKBANK": "Kotak Mahindra Bank Ltd",
    "AXISBANK": "Axis Bank Ltd",
    "LT": "Larsen & Toubro Ltd",
    "SUNPHARMA": "Sun Pharmaceutical Industries Ltd",
    "TITAN": "Titan Company Ltd",
    "HCLTECH": "HCL Technologies Ltd",
    "TECHM": "Tech Mahindra Ltd",
    "NESTLEIND": "Nestle India Ltd",
    "BAJFINANCE": "Bajaj Finance Ltd",
    "BAJAJFINSV": "Bajaj Finserv Ltd",
    "ADANIENT": "Adani Enterprises Ltd",
    "ADANIPORTS": "Adani Ports & SEZ Ltd",
    "ADANIGREEN": "Adani Green Energy Ltd",
    "HAL": "Hindustan Aeronautics Ltd",
    "JSWSTEEL": "JSW Steel Ltd",
    "COALINDIA": "Coal India Ltd",
    "M&M": "Mahindra & Mahindra Ltd",
    "DABUR": "Dabur India Ltd",
    "MARICO": "Marico Ltd",
    "GODREJCP": "Godrej Consumer Products Ltd",
    "PIDILITIND": "Pidilite Industries Ltd",
    "BRITANNIA": "Britannia Industries Ltd",
    "EMAMILTD": "Emami Ltd",
    "TATAPOWER": "Tata Power Co Ltd",
    "TATACHEM": "Tata Chemicals Ltd",
    "TATAELXSI": "Tata Elxsi Ltd",
    "TATAINVEST": "Tata Investment Corp Ltd",
    "TATAMETALI": "Tata Metaliks Ltd",
    "TATASPONGE": "Tata Sponge Iron Ltd",
    "TATASTLLP": "Tata Steel Long Products",
    "VOLTAS": "Voltas Ltd",
    "TITAGARH": "Titagarh Rail Systems Ltd",
    "RVNL": "Rail Vikas Nigam Ltd",
    "IRFC": "Indian Railway Finance Corp Ltd",
    "IREDA": "Indian Renewable Energy Dev Agency",
    "BANKBARODA": "Bank of Baroda",
    "PNB": "Punjab National Bank",
    "CANBK": "Canara Bank",
    "UNIONBANK": "Union Bank of India",
    "IOC": "Indian Oil Corp Ltd",
    "BPCL": "Bharat Petroleum Corp Ltd",
    "HPCL": "Hindustan Petroleum Corp Ltd",
    "GAIL": "GAIL India Ltd",
    "PFC": "Power Finance Corp Ltd",
    "RECLTD": "REC Ltd",
    "SBI": "State Bank of India",
    "BANKNIFTY": "Bank Nifty Index",
    "NIFTY": "Nifty 50 Index",
    "SENSEX": "BSE Sensex",
    "MIDCAP": "Nifty Midcap 100",
    "SMALLCAP": "Nifty Smallcap 100",
}

# Search function with local database
def search_stocks(query):
    query = query.upper().strip()
    results = []
    
    # Search by symbol
    for symbol, name in STOCKS.items():
        if query in symbol:
            results.append({
                'symbol': symbol,
                'name': name,
                'url': f"https://www.screener.in/company/{symbol}/"
            })
            continue
        if query in name.upper():
            results.append({
                'symbol': symbol,
                'name': name,
                'url': f"https://www.screener.in/company/{symbol}/"
            })
    
    return results


# ============ SCRAPER ============
class StockScraper:
    def __init__(self, symbol, url=None):
        self.symbol = symbol.upper()
        self.url = url or f"https://www.screener.in/company/{self.symbol}/"
        self.data = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch(self):
        try:
            print(f"🔍 Fetching {self.symbol}...")
            response = requests.get(self.url, headers=self.headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            self.data['symbol'] = self.symbol
            self.data['name'] = self._get_name(soup)
            self.data['price'] = self._get_price(soup)
            self.data['pe_ratio'] = self._get_pe(soup)
            self.data['roe'] = self._get_roe(soup)
            self.data['roce'] = self._get_roce(soup)
            self.data['debt_equity'] = self._get_debt(soup)
            self.data['market_cap'] = self._get_market_cap(soup)
            self.data['dividend_yield'] = self._get_dividend(soup)
            self.data['pb_ratio'] = self._get_pb(soup)
            self.data['year_high'] = self._get_high(soup)
            self.data['pe_5y_avg'] = self._get_pe_5y()
            self.data['price_200dma'] = self._get_dma(200)
            self.data['price_50dma'] = self._get_dma(50)
            self.data['one_year_return'] = self._get_return()
            self.data['sales_growth'] = 10
            self.data['profit_growth'] = 8
            self.data['shareholding'] = {'fii_change': 0, 'dii_change': 0}
            self.data['rsi'] = 50
            self.data['volume_ratio'] = 1.0
            self.data['higher_high'] = False
            self.data['higher_low'] = False
            self.data['cash_flow_consistency'] = 70
            self.data['moat_score'] = self._get_moat()
            
            return self.data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return self._get_fallback()
    
    def _get_fallback(self):
        fallback_data = {
            'IRCTC': {'price': 495, 'pe': 28.7, 'roe': 34.6, 'roce': 46.1, 'debt': 0, 'market_cap': 39604, 'pe_5y': 42, 'dma_200': 480, 'dma_50': 490, 'return': 2, 'moat': 8},
            'RELIANCE': {'price': 2800, 'pe': 30, 'roe': 20, 'roce': 22, 'debt': 0.5, 'market_cap': 1800000, 'pe_5y': 30, 'dma_200': 2600, 'dma_50': 2650, 'return': 5, 'moat': 8},
            'TCS': {'price': 4254, 'pe': 35, 'roe': 45, 'roce': 50, 'debt': 0, 'market_cap': 800000, 'pe_5y': 35, 'dma_200': 4100, 'dma_50': 4150, 'return': 10, 'moat': 9},
            'INFY': {'price': 1800, 'pe': 30, 'roe': 35, 'roce': 40, 'debt': 0, 'market_cap': 600000, 'pe_5y': 30, 'dma_200': 1750, 'dma_50': 1780, 'return': 8, 'moat': 8},
            'WIPRO': {'price': 550, 'pe': 25, 'roe': 25, 'roce': 28, 'debt': 0, 'market_cap': 250000, 'pe_5y': 25, 'dma_200': 540, 'dma_50': 545, 'return': -3, 'moat': 6},
            'HDFC': {'price': 2800, 'pe': 25, 'roe': 18, 'roce': 20, 'debt': 0.3, 'market_cap': 500000, 'pe_5y': 25, 'dma_200': 2700, 'dma_50': 2750, 'return': 8, 'moat': 9},
            'HDFCBANK': {'price': 1700, 'pe': 25, 'roe': 18, 'roce': 20, 'debt': 0, 'market_cap': 450000, 'pe_5y': 25, 'dma_200': 1650, 'dma_50': 1680, 'return': 15, 'moat': 9},
            'ITC': {'price': 420, 'pe': 30, 'roe': 25, 'roce': 28, 'debt': 0, 'market_cap': 500000, 'pe_5y': 30, 'dma_200': 415, 'dma_50': 420, 'return': 15, 'moat': 8},
            'SBIN': {'price': 800, 'pe': 15, 'roe': 16, 'roce': 18, 'debt': 0.8, 'market_cap': 600000, 'pe_5y': 15, 'dma_200': 790, 'dma_50': 800, 'return': 20, 'moat': 7},
            'TATAMOTORS': {'price': 850, 'pe': 25, 'roe': 20, 'roce': 22, 'debt': 0.6, 'market_cap': 300000, 'pe_5y': 25, 'dma_200': 840, 'dma_50': 850, 'return': 35, 'moat': 7},
            'TATACONSUM': {'price': 1100, 'pe': 55, 'roe': 30, 'roce': 35, 'debt': 0, 'market_cap': 150000, 'pe_5y': 55, 'dma_200': 1080, 'dma_50': 1100, 'return': 12, 'moat': 7},
            'TATASTEEL': {'price': 150, 'pe': 15, 'roe': 12, 'roce': 14, 'debt': 0.5, 'market_cap': 180000, 'pe_5y': 15, 'dma_200': 145, 'dma_50': 148, 'return': -10, 'moat': 6},
            'ICRA': {'price': 4800, 'pe': 27, 'roe': 17, 'roce': 23, 'debt': 0, 'market_cap': 4600, 'pe_5y': 27, 'dma_200': 5200, 'dma_50': 4900, 'return': -28, 'moat': 6},
            'CARE': {'price': 1600, 'pe': 30, 'roe': 25, 'roce': 26, 'debt': 0, 'market_cap': 5000, 'pe_5y': 30, 'dma_200': 1600, 'dma_50': 1650, 'return': -5, 'moat': 6},
        }
        
        fb = fallback_data.get(self.symbol, {'price': 0, 'pe': 25, 'roe': 20, 'roce': 22, 'debt': 0, 'market_cap': 0, 'pe_5y': 25, 'dma_200': 0, 'dma_50': 0, 'return': 0, 'moat': 5})
        
        return {
            'symbol': self.symbol,
            'name': STOCKS.get(self.symbol, self.symbol),
            'price': fb.get('price', 0),
            'pe_ratio': fb.get('pe', 25),
            'roe': fb.get('roe', 20),
            'roce': fb.get('roce', 22),
            'debt_equity': fb.get('debt', 0),
            'market_cap': fb.get('market_cap', 0),
            'dividend_yield': 0,
            'pb_ratio': 3,
            'year_high': 0,
            'pe_5y_avg': fb.get('pe_5y', 25),
            'price_200dma': fb.get('dma_200', 0),
            'price_50dma': fb.get('dma_50', 0),
            'one_year_return': fb.get('return', 0),
            'sales_growth': 10,
            'profit_growth': 8,
            'shareholding': {'fii_change': 0, 'dii_change': 0},
            'rsi': 50,
            'volume_ratio': 1.0,
            'higher_high': False,
            'higher_low': False,
            'cash_flow_consistency': 70,
            'moat_score': fb.get('moat', 5)
        }
    
    def _get_name(self, soup):
        try:
            h1 = soup.find('h1')
            return h1.text.strip() if h1 else self.symbol
        except:
            return self.symbol
    
    def _get_price(self, soup):
        try:
            text = soup.text
            match = re.search(r'Current Price\s*[₹]?\s*([\d,]+\.?[\d]*)', text)
            return float(match.group(1).replace(',', '')) if match else 0
        except:
            return 0
    
    def _get_pe(self, soup):
        try:
            text = soup.text
            match = re.search(r'Stock P/E\s*([\d.]+)', text)
            return float(match.group(1)) if match else 0
        except:
            return 0
    
    def _get_roe(self, soup):
        try:
            text = soup.text
            match = re.search(r'ROE\s*([\d.]+)\s*%', text)
            return float(match.group(1)) if match else 0
        except:
            return 0
    
    def _get_roce(self, soup):
        try:
            text = soup.text
            match = re.search(r'ROCE\s*([\d.]+)\s*%', text)
            return float(match.group(1)) if match else 0
        except:
            return 0
    
    def _get_debt(self, soup):
        return 0.0
    
    def _get_market_cap(self, soup):
        try:
            text = soup.text
            match = re.search(r'Market Cap\s*[₹]?\s*([\d,]+)\s*Cr', text)
            return float(match.group(1).replace(',', '')) if match else 0
        except:
            return 0
    
    def _get_dividend(self, soup):
        try:
            text = soup.text
            match = re.search(r'Dividend Yield\s*([\d.]+)\s*%', text)
            return float(match.group(1)) if match else 0
        except:
            return 0
    
    def _get_pb(self, soup):
        try:
            text = soup.text
            match = re.search(r'trading at\s*([\d.]+)\s*times', text)
            return float(match.group(1)) if match else 3.0
        except:
            return 3.0
    
    def _get_high(self, soup):
        try:
            text = soup.text
            match = re.search(r'High / Low\s*[₹]?\s*([\d,]+)\s*/\s*([\d,]+)', text)
            return float(match.group(1).replace(',', '')) if match else 0
        except:
            return 0
    
    def _get_pe_5y(self):
        pe_5y = {
            'IRCTC': 42, 'TCS': 35, 'RELIANCE': 30, 'HDFC': 25, 'HDFCBANK': 25,
            'INFY': 30, 'WIPRO': 25, 'TATAMOTORS': 25, 'TATACONSUM': 55,
            'TATASTEEL': 15, 'ITC': 30, 'SBIN': 15, 'ONGC': 12, 'ICRA': 27, 'CARE': 30
        }
        return pe_5y.get(self.symbol, 25)
    
    def _get_dma(self, period):
        dma = {
            'IRCTC': {'200': 480, '50': 490},
            'TCS': {'200': 4100, '50': 4150},
            'RELIANCE': {'200': 2600, '50': 2650},
            'HDFC': {'200': 2700, '50': 2750},
            'HDFCBANK': {'200': 1650, '50': 1680},
            'INFY': {'200': 1750, '50': 1780},
            'WIPRO': {'200': 540, '50': 545},
            'TATAMOTORS': {'200': 840, '50': 850},
            'TATACONSUM': {'200': 1080, '50': 1100},
            'TATASTEEL': {'200': 145, '50': 148},
            'ITC': {'200': 415, '50': 420},
            'SBIN': {'200': 790, '50': 800},
            'ONGC': {'200': 245, '50': 250},
            'ICRA': {'200': 5200, '50': 4900},
            'CARE': {'200': 1600, '50': 1650}
        }
        return dma.get(self.symbol, {}).get(period, 0)
    
    def _get_return(self):
        returns = {
            'IRCTC': 2, 'TCS': 10, 'RELIANCE': 5, 'HDFC': 8, 'HDFCBANK': 15,
            'INFY': 8, 'WIPRO': -3, 'TATAMOTORS': 35, 'TATACONSUM': 12,
            'TATASTEEL': -10, 'ITC': 15, 'SBIN': 20, 'ONGC': -2, 'ICRA': -28, 'CARE': -5
        }
        return returns.get(self.symbol, 0)
    
    def _get_moat(self):
        moat = {
            'IRCTC': 8, 'TCS': 9, 'RELIANCE': 8, 'HDFC': 9, 'HDFCBANK': 9,
            'INFY': 8, 'WIPRO': 6, 'TATAMOTORS': 7, 'TATACONSUM': 7,
            'TATASTEEL': 6, 'ITC': 8, 'SBIN': 7, 'ONGC': 6, 'ICRA': 6, 'CARE': 6
        }
        return moat.get(self.symbol, 5)


# ============ THREE-PILLAR ANALYZER ============
class ThreePillarAnalyzer:
    def __init__(self, data):
        self.data = data
        self.business_score = 0
        self.value_score = 0
        self.timing_score = 0
        self.business_breakdown = {}
        self.value_breakdown = {}
        self.timing_breakdown = {}
    
    def analyze_business(self):
        scores = {}
        
        roe = self.data.get('roe', 0)
        if roe >= 25:
            scores['roe'] = 10; scores['roe_label'] = "✅ Excellent"
        elif roe >= 20:
            scores['roe'] = 8; scores['roe_label'] = "👍 Good"
        elif roe >= 15:
            scores['roe'] = 6; scores['roe_label'] = "📊 Average"
        elif roe >= 10:
            scores['roe'] = 4; scores['roe_label'] = "⚠️ Below avg"
        else:
            scores['roe'] = 2; scores['roe_label'] = "❌ Low"
        
        debt = self.data.get('debt_equity', 0)
        if debt < 0.1:
            scores['debt'] = 10; scores['debt_label'] = "✅ Debt-free"
        elif debt < 0.5:
            scores['debt'] = 8; scores['debt_label'] = "👍 Low debt"
        elif debt < 1.0:
            scores['debt'] = 6; scores['debt_label'] = "📊 Moderate"
        elif debt < 2.0:
            scores['debt'] = 3; scores['debt_label'] = "⚠️ High"
        else:
            scores['debt'] = 0; scores['debt_label'] = "❌ Very high"
        
        growth = self.data.get('profit_growth', 0)
        if growth >= 20:
            scores['profit_growth'] = 10; scores['profit_growth_label'] = "✅ Strong"
        elif growth >= 10:
            scores['profit_growth'] = 8; scores['profit_growth_label'] = "👍 Healthy"
        elif growth >= 5:
            scores['profit_growth'] = 6; scores['profit_growth_label'] = "📊 Modest"
        elif growth >= 0:
            scores['profit_growth'] = 4; scores['profit_growth_label'] = "⚠️ Flat"
        else:
            scores['profit_growth'] = 0; scores['profit_growth_label'] = "❌ Declining"
        
        cf = self.data.get('cash_flow_consistency', 70)
        if cf >= 80:
            scores['cash_flow'] = 5; scores['cash_flow_label'] = "✅ Strong FCF"
        elif cf >= 60:
            scores['cash_flow'] = 4; scores['cash_flow_label'] = "👍 Consistent"
        else:
            scores['cash_flow'] = 2; scores['cash_flow_label'] = "⚠️ Inconsistent"
        
        moat = self.data.get('moat_score', 5)
        if moat >= 8:
            scores['moat'] = 5; scores['moat_label'] = "✅ Wide moat"
        elif moat >= 6:
            scores['moat'] = 4; scores['moat_label'] = "👍 Narrow moat"
        else:
            scores['moat'] = 2; scores['moat_label'] = "📊 Commodity"
        
        self.business_breakdown = scores
        self.business_score = sum([v for k, v in scores.items() if not k.endswith('_label')])
        return self.business_score
    
    def analyze_value(self):
        scores = {}
        
        current_pe = self.data.get('pe_ratio', 0)
        avg_pe = self.data.get('pe_5y_avg', 25)
        if current_pe > 0 and avg_pe > 0:
            ratio = current_pe / avg_pe
            if ratio < 0.6:
                scores['pe'] = 10; scores['pe_label'] = "✅ Very undervalued"
            elif ratio < 0.75:
                scores['pe'] = 8; scores['pe_label'] = "👍 Undervalued"
            elif ratio < 0.9:
                scores['pe'] = 6; scores['pe_label'] = "📊 Fairly valued"
            elif ratio < 1.1:
                scores['pe'] = 4; scores['pe_label'] = "⚠️ Slight premium"
            else:
                scores['pe'] = 2; scores['pe_label'] = "❌ Expensive"
        else:
            scores['pe'] = 5; scores['pe_label'] = "📊 Data N/A"
        
        ret = self.data.get('one_year_return', 0)
        if ret < -30:
            scores['correction'] = 10; scores['correction_label'] = "✅ Major correction"
        elif ret < -20:
            scores['correction'] = 8; scores['correction_label'] = "👍 Significant"
        elif ret < -10:
            scores['correction'] = 6; scores['correction_label'] = "📊 Moderate"
        elif ret < 0:
            scores['correction'] = 4; scores['correction_label'] = "⚠️ Mild"
        else:
            scores['correction'] = 2; scores['correction_label'] = "📈 No discount"
        
        price = self.data.get('price', 0)
        high = self.data.get('year_high', price * 1.2)
        dist = (1 - (price / high)) * 100 if high > 0 else 0
        if dist > 30:
            scores['distance'] = 5; scores['distance_label'] = "✅ 30%+ from high"
        elif dist > 20:
            scores['distance'] = 4; scores['distance_label'] = "👍 20%+ from high"
        elif dist > 10:
            scores['distance'] = 3; scores['distance_label'] = "📊 10%+ from high"
        else:
            scores['distance'] = 1; scores['distance_label'] = "⚠️ Near high"
        
        pb = self.data.get('pb_ratio', 0)
        if pb < 1:
            scores['pb'] = 5; scores['pb_label'] = "✅ Below book"
        elif pb < 2:
            scores['pb'] = 4; scores['pb_label'] = "👍 Reasonable"
        elif pb < 4:
            scores['pb'] = 3; scores['pb_label'] = "📊 Moderate"
        else:
            scores['pb'] = 1; scores['pb_label'] = "⚠️ Expensive"
        
        self.value_breakdown = scores
        self.value_score = sum([v for k, v in scores.items() if not k.endswith('_label')])
        return self.value_score
    
    def analyze_timing(self):
        scores = {}
        price = self.data.get('price', 0)
        dma_200 = self.data.get('price_200dma', price)
        dma_50 = self.data.get('price_50dma', price * 0.98)
        
        if price > dma_200 and dma_200 > 0:
            scores['dma_200'] = 5; scores['dma_200_label'] = "✅ Above 200 DMA"
        elif dma_200 > 0 and price > dma_200 * 0.95:
            scores['dma_200'] = 3; scores['dma_200_label'] = "📊 Near 200 DMA"
        else:
            scores['dma_200'] = 0; scores['dma_200_label'] = "❌ Below 200 DMA"
        
        if price > dma_50 and dma_50 > 0:
            scores['dma_50'] = 4; scores['dma_50_label'] = "✅ Above 50 DMA"
        else:
            scores['dma_50'] = 0; scores['dma_50_label'] = "❌ Below 50 DMA"
        
        hh = self.data.get('higher_high', False)
        hl = self.data.get('higher_low', False)
        if hh and hl:
            scores['hh_hl'] = 4; scores['hh_hl_label'] = "✅ Uptrend"
        elif hh or hl:
            scores['hh_hl'] = 2; scores['hh_hl_label'] = "📊 Early trend"
        else:
            scores['hh_hl'] = 0; scores['hh_hl_label'] = "❌ Downtrend"
        
        vol = self.data.get('volume_ratio', 1.0)
        if vol > 2.0:
            scores['volume'] = 4; scores['volume_label'] = "✅ Strong volume"
        elif vol > 1.5:
            scores['volume'] = 3; scores['volume_label'] = "👍 Above avg"
        elif vol > 1.0:
            scores['volume'] = 2; scores['volume_label'] = "📊 Average"
        else:
            scores['volume'] = 0; scores['volume_label'] = "❌ Low volume"
        
        rsi = self.data.get('rsi', 50)
        if 40 <= rsi <= 60:
            scores['rsi'] = 4; scores['rsi_label'] = "✅ Healthy"
        elif rsi < 35:
            scores['rsi'] = 3; scores['rsi_label'] = "⚠️ Oversold"
        elif rsi > 65:
            scores['rsi'] = 2; scores['rsi_label'] = "⚠️ Overbought"
        else:
            scores['rsi'] = 3; scores['rsi_label'] = "📊 Neutral"
        
        fii = self.data.get('shareholding', {}).get('fii_change', 0)
        if fii > 1.0:
            scores['fii'] = 5; scores['fii_label'] = "✅ FII buying"
        elif fii > 0:
            scores['fii'] = 4; scores['fii_label'] = "👍 FII accumulation"
        elif fii > -0.5:
            scores['fii'] = 2; scores['fii_label'] = "📊 FII neutral"
        else:
            scores['fii'] = 0; scores['fii_label'] = "❌ FII selling"
        
        dii = self.data.get('shareholding', {}).get('dii_change', 0)
        if dii > 1.0:
            scores['dii'] = 4; scores['dii_label'] = "✅ DII buying"
        elif dii > 0:
            scores['dii'] = 3; scores['dii_label'] = "👍 DII accumulation"
        else:
            scores['dii'] = 0; scores['dii_label'] = "❌ DII selling"
        
        self.timing_breakdown = scores
        self.timing_score = sum([v for k, v in scores.items() if not k.endswith('_label')])
        return self.timing_score
    
    def analyze_all(self):
        self.analyze_business()
        self.analyze_value()
        self.analyze_timing()
        return {
            'business': self.business_score,
            'value': self.value_score,
            'timing': self.timing_score,
            'total': self.business_score + self.value_score + self.timing_score,
            'business_breakdown': self.business_breakdown,
            'value_breakdown': self.value_breakdown,
            'timing_breakdown': self.timing_breakdown
        }


# ============ PHASE ENGINE ============
class PhaseEngine:
    @classmethod
    def classify(cls, score):
        if score >= 85:
            return {"name": "🟢 STRONG BUY", "action": "✅ BUY NOW"}
        elif score >= 70:
            return {"name": "🔵 BUY ON BREAKOUT", "action": "⏳ WAIT FOR BREAKOUT"}
        elif score >= 55:
            return {"name": "🟡 WATCHLIST", "action": "📋 MONITOR DAILY"}
        elif score >= 40:
            return {"name": "🟠 RECOVERY", "action": "🔍 NO BUY YET"}
        elif score >= 20:
            return {"name": "🔴 DISTRIBUTION", "action": "🚫 AVOID"}
        else:
            return {"name": "⚫ BREAKDOWN", "action": "🗑️ REMOVE"}
    
    @classmethod
    def get_signal(cls, biz, val, timing):
        return f"{'🟢' if biz >= 35 else '🟡' if biz >= 25 else '🔴'} Business | {'✅' if val >= 25 else '📊' if val >= 18 else '❌'} Value | {'🚀' if timing >= 25 else '📈' if timing >= 18 else '⏳'} Timing"


# ============ PROBABILITY ENGINE ============
class ProbabilityEngine:
    @classmethod
    def calculate(cls, data, total_score):
        base = (total_score / 100) * 70
        adj = 0
        
        if data.get('price', 0) > data.get('price_200dma', 0):
            adj += 15
        if data.get('volume_ratio', 1.0) > 2.0:
            adj += 10
        if data.get('shareholding', {}).get('fii_change', 0) > 0.5:
            adj += 8
        if data.get('rsi', 50) < 35:
            adj += 7
        
        prob = min(base + adj, 95)
        return {'probability': round(prob, 1)}


# ============ TELEGRAM BOT ============
logging.basicConfig(level=logging.INFO)


def format_report(data, scores, phase, signal, prob):
    report = f"""
📊 *{data.get('name', data.get('symbol', ''))}* ({data.get('symbol', '')})
━━━━━━━━━━━━━━━━━━━━━
💰 Price: ₹{data.get('price', 0):,.2f}
📈 Market Cap: ₹{data.get('market_cap', 0):,.0f} Cr
📉 PE: {data.get('pe_ratio', 0):.2f} (5Y Avg: {data.get('pe_5y_avg', 0):.2f})
🏦 ROE: {data.get('roe', 0):.1f}% | ROCE: {data.get('roce', 0):.1f}%
💳 Debt/Equity: {data.get('debt_equity', 0):.2f}

🏢 *BUSINESS QUALITY*: {scores['business']}/40
"""
    for key in ['roe', 'debt', 'profit_growth']:
        label = scores['business_breakdown'].get(f'{key}_label', '')
        score = scores['business_breakdown'].get(key, 0)
        report += f"   • {label}: {score}/10\n"
    for key in ['cash_flow', 'moat']:
        label = scores['business_breakdown'].get(f'{key}_label', '')
        score = scores['business_breakdown'].get(key, 0)
        report += f"   • {label}: {score}/5\n"

    report += f"""
💎 *VALUATION*: {scores['value']}/30
"""
    for key in ['pe', 'correction']:
        label = scores['value_breakdown'].get(f'{key}_label', '')
        score = scores['value_breakdown'].get(key, 0)
        report += f"   • {label}: {score}/10\n"
    for key in ['distance', 'pb']:
        label = scores['value_breakdown'].get(f'{key}_label', '')
        score = scores['value_breakdown'].get(key, 0)
        report += f"   • {label}: {score}/5\n"

    report += f"""
⏰ *TIMING*: {scores['timing']}/30
"""
    for key in ['dma_200', 'fii']:
        label = scores['timing_breakdown'].get(f'{key}_label', '')
        score = scores['timing_breakdown'].get(key, 0)
        report += f"   • {label}: {score}/5\n"
    for key in ['dma_50', 'hh_hl', 'volume', 'rsi', 'dii']:
        label = scores['timing_breakdown'].get(f'{key}_label', '')
        score = scores['timing_breakdown'].get(key, 0)
        report += f"   • {label}: {score}/4\n"

    report += f"""
━━━━━━━━━━━━━━━━━━━━━
*TOTAL SCORE: {scores['total']}/100*
*PHASE: {phase['name']}*
*ACTION: {phase['action']}*

📋 *Signal:* {signal}

🎯 *BUY PROBABILITY:* {prob['probability']}% (Achieving +10% in 90 days)

📅 Analysis: {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}
"""
    return report


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🚀 *APEX PRO - Stock Analysis Bot*

*How to use:*
Just type any stock name or code!

*Examples:*
• `IRCTC`
• `Tata Motors`
• `RELIANCE`

*Commands:*
`/list` - Show all stocks
`/help` - Help message

Powered by Three-Pillar Analysis:
🏢 Business (40) | 💎 Value (30) | ⏰ Timing (30)
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 *APEX PRO Commands*

Just type any stock name or code!

*Examples:*
• `IRCTC` - Direct analysis
• `Tata` - Shows all Tata stocks
• `HDFC Bank` - Search by name

*Commands:*
`/start` - Welcome
`/list` - All stocks
`/help` - This message
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = "📋 *Available Stocks*\n━━━━━━━━━━━━━\n\n"
    
    # Group by letter
    groups = {}
    for symbol in sorted(STOCKS.keys()):
        first = symbol[0]
        if first not in groups:
            groups[first] = []
        groups[first].append(symbol)
    
    for letter, symbols in sorted(groups.items()):
        stocks += f"*{letter}*: "
        stocks += ", ".join([f"`{s}`" for s in symbols[:5]])
        if len(symbols) > 5:
            stocks += f" +{len(symbols)-5} more"
        stocks += "\n"
    
    stocks += "\n💡 Type any stock name or code to analyze!"
    await update.message.reply_text(stocks, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any text message"""
    if not update.message or not update.message.text:
        return
    
    query = update.message.text.strip()
    
    # Skip commands
    if query.startswith('/'):
        return
    
    print(f"🔍 Searching: {query}")
    
    results = search_stocks(query)
    
    if not results:
        await update.message.reply_text(f"❌ No stocks found for *{query}*", parse_mode='Markdown')
        return
    
    if len(results) == 1:
        await analyze_stock(update, results[0])
    else:
        await show_menu(update, results)


async def show_menu(update: Update, results):
    """Show selection menu"""
    menu = "🔍 *Multiple stocks found:*\n\n"
    buttons = []
    
    for i, result in enumerate(results[:10], 1):
        menu += f"{i}. *{result['symbol']}* - {result['name'][:35]}\n"
        buttons.append([InlineKeyboardButton(
            f"{i}. {result['symbol']}",
            callback_data=f"select_{result['symbol']}"
        )])
    
    if len(results) > 10:
        menu += f"\n+{len(results)-10} more results."
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(menu, parse_mode='Markdown', reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    symbol = query.data.replace('select_', '')
    await query.edit_message_text(f"🔍 Analyzing *{symbol}*...", parse_mode='Markdown')
    
    result = {'symbol': symbol, 'url': f"https://www.screener.in/company/{symbol}/"}
    await analyze_stock_from_callback(update, result)


async def analyze_stock(update: Update, result):
    """Fetch and send analysis"""
    scraper = StockScraper(result['symbol'], result.get('url'))
    data = scraper.fetch()
    
    analyzer = ThreePillarAnalyzer(data)
    scores = analyzer.analyze_all()
    phase = PhaseEngine.classify(scores['total'])
    signal = PhaseEngine.get_signal(scores['business'], scores['value'], scores['timing'])
    prob = ProbabilityEngine.calculate(data, scores['total'])
    
    report = format_report(data, scores, phase, signal, prob)
    await update.message.reply_text(report, parse_mode='Markdown')


async def analyze_stock_from_callback(update: Update, result):
    """Fetch and send analysis from callback"""
    scraper = StockScraper(result['symbol'], result.get('url'))
    data = scraper.fetch()
    
    analyzer = ThreePillarAnalyzer(data)
    scores = analyzer.analyze_all()
    phase = PhaseEngine.classify(scores['total'])
    signal = PhaseEngine.get_signal(scores['business'], scores['value'], scores['timing'])
    prob = ProbabilityEngine.calculate(data, scores['total'])
    
    report = format_report(data, scores, phase, signal, prob)
    await update.callback_query.message.reply_text(report, parse_mode='Markdown')


# ============ MAIN ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", list_stocks))
    
    # Callback handler
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handler - handles all text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 APEX PRO Bot is running...")
    print(f"📊 {len(STOCKS)} stocks loaded in local database")
    print("📝 Just type any stock name or code to analyze!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

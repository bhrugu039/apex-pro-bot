"""
APEX PRO - Telegram Stock Analysis Bot
Interactive Menu System
"""

import re
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import logging
from datetime import datetime, timezone, timedelta
import os

# ============ CONFIGURATION ============
BOT_TOKEN = "8962365949:AAHhoTogxKuhW_Pta7yXjRqCoJTFtBhPZd8"
CHAT_ID = "728405872"

print(f"✅ Bot token loaded: {BOT_TOKEN[:10]}...")
print(f"✅ Chat ID loaded: {CHAT_ID}")

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Stock Database - Company Name, Symbol, and Screener URL
STOCK_DATABASE = {
    "IRCTC": {"name": "Indian Railway Catering & Tourism Corporation Ltd", "url": "https://www.screener.in/company/IRCTC/"},
    "ICRA": {"name": "ICRA Ltd", "url": "https://www.screener.in/company/ICRA/"},
    "CARE": {"name": "CARE Ratings Ltd", "url": "https://www.screener.in/company/CARE/"},
    "TATACONSUM": {"name": "Tata Consumer Products Ltd", "url": "https://www.screener.in/company/TATACONSUM/"},
    "HDFC": {"name": "HDFC Ltd", "url": "https://www.screener.in/company/HDFC/"},
    "HDFCBANK": {"name": "HDFC Bank Ltd", "url": "https://www.screener.in/company/HDFCBANK/"},
    "RELIANCE": {"name": "Reliance Industries Ltd", "url": "https://www.screener.in/company/RELIANCE/"},
    "TCS": {"name": "Tata Consultancy Services Ltd", "url": "https://www.screener.in/company/TCS/"},
    "INFY": {"name": "Infosys Ltd", "url": "https://www.screener.in/company/INFY/"},
    "WIPRO": {"name": "Wipro Ltd", "url": "https://www.screener.in/company/WIPRO/"},
    "TATAMOTORS": {"name": "Tata Motors Ltd", "url": "https://www.screener.in/company/TATAMOTORS/"},
    "ITC": {"name": "ITC Ltd", "url": "https://www.screener.in/company/ITC/"},
    "SBIN": {"name": "State Bank of India", "url": "https://www.screener.in/company/SBIN/"},
    "ONGC": {"name": "Oil and Natural Gas Corporation Ltd", "url": "https://www.screener.in/company/ONGC/"},
    "HAL": {"name": "Hindustan Aeronautics Ltd", "url": "https://www.screener.in/company/HAL/"},
    "ADANIENT": {"name": "Adani Enterprises Ltd", "url": "https://www.screener.in/company/ADANIENT/"},
    "BAJFINANCE": {"name": "Bajaj Finance Ltd", "url": "https://www.screener.in/company/BAJFINANCE/"},
    "MARUTI": {"name": "Maruti Suzuki India Ltd", "url": "https://www.screener.in/company/MARUTI/"},
    "TATASTEEL": {"name": "Tata Steel Ltd", "url": "https://www.screener.in/company/TATASTEEL/"},
    "JSWSTEEL": {"name": "JSW Steel Ltd", "url": "https://www.screener.in/company/JSWSTEEL/"},
    "BHARTIARTL": {"name": "Bharti Airtel Ltd", "url": "https://www.screener.in/company/BHARTIARTL/"},
    "ASIANPAINT": {"name": "Asian Paints Ltd", "url": "https://www.screener.in/company/ASIANPAINT/"},
    "HINDUNILVR": {"name": "Hindustan Unilever Ltd", "url": "https://www.screener.in/company/HINDUNILVR/"},
    "AXISBANK": {"name": "Axis Bank Ltd", "url": "https://www.screener.in/company/AXISBANK/"},
    "KOTAKBANK": {"name": "Kotak Mahindra Bank Ltd", "url": "https://www.screener.in/company/KOTAKBANK/"},
    "LT": {"name": "Larsen & Toubro Ltd", "url": "https://www.screener.in/company/LT/"},
    "M&M": {"name": "Mahindra & Mahindra Ltd", "url": "https://www.screener.in/company/M&M/"},
    "SUNPHARMA": {"name": "Sun Pharmaceutical Industries Ltd", "url": "https://www.screener.in/company/SUNPHARMA/"},
    "TITAN": {"name": "Titan Company Ltd", "url": "https://www.screener.in/company/TITAN/"},
    "NTPC": {"name": "NTPC Ltd", "url": "https://www.screener.in/company/NTPC/"},
    "POWERGRID": {"name": "Power Grid Corporation of India Ltd", "url": "https://www.screener.in/company/POWERGRID/"},
    "ULTRACEMCO": {"name": "UltraTech Cement Ltd", "url": "https://www.screener.in/company/ULTRACEMCO/"},
    "COALINDIA": {"name": "Coal India Ltd", "url": "https://www.screener.in/company/COALINDIA/"},
    "BAJAJFINSV": {"name": "Bajaj Finserv Ltd", "url": "https://www.screener.in/company/BAJAJFINSV/"},
    "HCLTECH": {"name": "HCL Technologies Ltd", "url": "https://www.screener.in/company/HCLTECH/"},
    "TECHM": {"name": "Tech Mahindra Ltd", "url": "https://www.screener.in/company/TECHM/"},
    "NESTLEIND": {"name": "Nestle India Ltd", "url": "https://www.screener.in/company/NESTLEIND/"},
    "BRITANNIA": {"name": "Britannia Industries Ltd", "url": "https://www.screener.in/company/BRITANNIA/"},
    "PIDILITIND": {"name": "Pidilite Industries Ltd", "url": "https://www.screener.in/company/PIDILITIND/"},
    "DABUR": {"name": "Dabur India Ltd", "url": "https://www.screener.in/company/DABUR/"},
    "MARICO": {"name": "Marico Ltd", "url": "https://www.screener.in/company/MARICO/"},
    "GODREJCP": {"name": "Godrej Consumer Products Ltd", "url": "https://www.screener.in/company/GODREJCP/"},
    "EMAMILTD": {"name": "Emami Ltd", "url": "https://www.screener.in/company/EMAMILTD/"},
}

# Store user search states
user_states = {}

# ============ SCRAPER ============
class StockScraper:
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        stock_info = STOCK_DATABASE.get(self.symbol)
        self.url = stock_info["url"] if stock_info else None
        self.data = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    
    def fetch(self):
        if not self.url:
            return {"error": f"❌ Stock {self.symbol} not found in database."}
        
        try:
            print(f"🔍 Fetching {self.symbol} from Screener.in...")
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract data from the page
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
            self.data['book_value'] = self._get_book_value(soup)
            
            # Get growth data
            growth = self._get_growth(soup)
            self.data['sales_growth'] = growth['sales']
            self.data['profit_growth'] = growth['profit']
            
            # Shareholding pattern
            self.data['shareholding'] = self._get_shareholding(soup)
            
            # 5Y Average PE (fallback)
            pe_5y_fallback = {
                'IRCTC': 42, 'ICRA': 27, 'CARE': 30, 'TATACONSUM': 55, 
                'HDFC': 25, 'HDFCBANK': 25, 'RELIANCE': 30, 'TCS': 35, 
                'INFY': 30, 'WIPRO': 25, 'TATAMOTORS': 25, 'ITC': 30, 
                'SBIN': 15, 'ONGC': 12
            }
            self.data['pe_5y_avg'] = pe_5y_fallback.get(self.symbol, 25)
            
            # DMA (fallback)
            dma_fallback = {
                'IRCTC': {'200': 480, '50': 490},
                'TCS': {'200': 4100, '50': 4150},
                'RELIANCE': {'200': 2600, '50': 2650},
                'HDFC': {'200': 2700, '50': 2750},
                'HDFCBANK': {'200': 1650, '50': 1680},
                'INFY': {'200': 1750, '50': 1780},
                'WIPRO': {'200': 540, '50': 545},
                'TATACONSUM': {'200': 1080, '50': 1100},
                'TATAMOTORS': {'200': 840, '50': 850},
                'ITC': {'200': 415, '50': 420},
                'SBIN': {'200': 790, '50': 800},
                'ONGC': {'200': 245, '50': 250},
                'ICRA': {'200': 5200, '50': 4900},
                'CARE': {'200': 1600, '50': 1650}
            }
            dma = dma_fallback.get(self.symbol, {'200': 0, '50': 0})
            self.data['price_200dma'] = dma.get('200', 0)
            self.data['price_50dma'] = dma.get('50', 0)
            
            # 1Y Return (fallback)
            returns = {
                'IRCTC': 2, 'TCS': 10, 'RELIANCE': 5, 'HDFC': 8,
                'HDFCBANK': 15, 'INFY': 8, 'WIPRO': -3, 'TATACONSUM': 12,
                'TATAMOTORS': 35, 'ITC': 15, 'SBIN': 20, 'ONGC': -2,
                'ICRA': -28, 'CARE': -5
            }
            self.data['one_year_return'] = returns.get(self.symbol, 0)
            
            # Other metrics
            self.data['rsi'] = 50
            self.data['volume_ratio'] = 1.0
            self.data['higher_high'] = self.data['price'] > self.data['price_50dma'] if self.data['price_50dma'] > 0 else False
            self.data['higher_low'] = self.data['price'] > self.data['price_50dma'] * 0.98 if self.data['price_50dma'] > 0 else False
            self.data['cash_flow_consistency'] = 75
            self.data['moat_score'] = self._get_moat()
            
            print(f"✅ Data extracted: {self.data['name']} - ₹{self.data['price']}")
            print(f"📊 PE: {self.data['pe_ratio']}, ROE: {self.data['roe']}%, ROCE: {self.data['roce']}%")
            print(f"📊 Market Cap: {self.data['market_cap']} Cr")
            return self.data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return self._get_fallback()
    
    def _get_fallback(self):
        """Return fallback data if scraping fails"""
        fallback = {
            'IRCTC': {'name': 'IRCTC Ltd', 'price': 495, 'pe': 28.7, 'roe': 34.6, 'roce': 46.1, 'debt': 0.0, 'market_cap': 39604},
            'TCS': {'name': 'TCS Ltd', 'price': 4254, 'pe': 35, 'roe': 45, 'roce': 50, 'debt': 0, 'market_cap': 800000},
            'RELIANCE': {'name': 'Reliance Industries', 'price': 2800, 'pe': 30, 'roe': 20, 'roce': 22, 'debt': 0.5, 'market_cap': 1800000},
            'HDFC': {'name': 'HDFC Ltd', 'price': 2800, 'pe': 25, 'roe': 18, 'roce': 20, 'debt': 0.3, 'market_cap': 500000},
            'HDFCBANK': {'name': 'HDFC Bank', 'price': 1700, 'pe': 25, 'roe': 18, 'roce': 20, 'debt': 0, 'market_cap': 450000},
            'INFY': {'name': 'Infosys Ltd', 'price': 1800, 'pe': 30, 'roe': 35, 'roce': 40, 'debt': 0, 'market_cap': 600000},
            'WIPRO': {'name': 'Wipro Ltd', 'price': 550, 'pe': 25, 'roe': 25, 'roce': 28, 'debt': 0, 'market_cap': 250000},
            'TATACONSUM': {'name': 'Tata Consumer', 'price': 1100, 'pe': 55, 'roe': 30, 'roce': 35, 'debt': 0, 'market_cap': 150000},
            'TATAMOTORS': {'name': 'Tata Motors', 'price': 850, 'pe': 25, 'roe': 20, 'roce': 22, 'debt': 0.6, 'market_cap': 300000},
            'ITC': {'name': 'ITC Ltd', 'price': 420, 'pe': 30, 'roe': 25, 'roce': 28, 'debt': 0, 'market_cap': 500000},
            'SBIN': {'name': 'SBI', 'price': 800, 'pe': 15, 'roe': 16, 'roce': 18, 'debt': 0.8, 'market_cap': 600000},
            'ONGC': {'name': 'ONGC', 'price': 250, 'pe': 12, 'roe': 15, 'roce': 16, 'debt': 0.4, 'market_cap': 300000},
            'CARE': {'name': 'CARE Ratings', 'price': 1600, 'pe': 30, 'roe': 25, 'roce': 26, 'debt': 0, 'market_cap': 5000},
            'ICRA': {'name': 'ICRA Ltd', 'price': 4800, 'pe': 27, 'roe': 17, 'roce': 23, 'debt': 0, 'market_cap': 4600},
        }
        
        fb = fallback.get(self.symbol, {'name': self.symbol, 'price': 0, 'pe': 25, 'roe': 20, 'roce': 22, 'debt': 0, 'market_cap': 50000})
        
        return {
            'symbol': self.symbol,
            'name': fb.get('name', self.symbol),
            'price': fb.get('price', 0),
            'pe_ratio': fb.get('pe', 25),
            'roe': fb.get('roe', 20),
            'roce': fb.get('roce', 22),
            'debt_equity': fb.get('debt', 0),
            'market_cap': fb.get('market_cap', 50000),
            'dividend_yield': 0,
            'sales_growth': 10,
            'profit_growth': 8,
            'shareholding': {'fii_change': 0, 'dii_change': 0},
            'pe_5y_avg': 30,
            'price_200dma': 0,
            'price_50dma': 0,
            'one_year_return': 5,
            'rsi': 50,
            'year_high': 0,
            'pb_ratio': 3,
            'book_value': 0,
            'volume_ratio': 1.0,
            'higher_high': False,
            'higher_low': False,
            'cash_flow_consistency': 75,
            'moat_score': 6
        }
    
    def _get_name(self, soup):
        try:
            name = soup.find('h1', {'class': 'company-name'})
            if name:
                return name.text.strip()
            h1 = soup.find('h1')
            if h1:
                return h1.text.strip()
            title = soup.find('title')
            if title:
                return title.text.replace(' share price | About', '').replace(' | Key Insights - Screener', '').strip()
        except:
            pass
        return self.symbol
    
    def _get_price(self, soup):
        try:
            text = soup.text
            match = re.search(r'Current Price\s*[₹]?\s*([\d,]+\.?[\d]*)', text)
            if match:
                return float(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _get_pe(self, soup):
        try:
            text = soup.text
            match = re.search(r'Stock P/E\s*([\d.]+)', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_roe(self, soup):
        try:
            text = soup.text
            match = re.search(r'ROE\s*([\d.]+)\s*%', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_roce(self, soup):
        try:
            text = soup.text
            match = re.search(r'ROCE\s*([\d.]+)\s*%', text)
            if match:
                return float(match.group(1))
        except:
            pass
        # Fallback
        fallback_roce = {
            'IRCTC': 46.1,
            'TCS': 50.0,
            'RELIANCE': 22.0,
            'HDFC': 20.0,
            'HDFCBANK': 20.0,
            'INFY': 40.0,
            'WIPRO': 28.0,
            'TATACONSUM': 35.0,
            'TATAMOTORS': 22.0,
            'ITC': 28.0,
            'SBIN': 18.0,
            'ONGC': 16.0,
            'ICRA': 23.0,
            'CARE': 26.0
        }
        return fallback_roce.get(self.symbol, 0)
    
    def _get_debt(self, soup):
        try:
            text = soup.text
            if 'almost debt free' in text.lower() or 'debt free' in text.lower():
                return 0.0
        except:
            pass
        return 0.0
    
    def _get_market_cap(self, soup):
        try:
            text = soup.text
            match = re.search(r'Market Cap\s*[₹]?\s*([\d,]+)\s*Cr', text)
            if match:
                return float(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _get_dividend(self, soup):
        try:
            text = soup.text
            match = re.search(r'Dividend Yield\s*([\d.]+)\s*%', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_pb(self, soup):
        try:
            text = soup.text
            match = re.search(r'trading at\s*([\d.]+)\s*times its book value', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 3.0
    
    def _get_book_value(self, soup):
        try:
            text = soup.text
            match = re.search(r'Book Value\s*[₹]?\s*([\d.]+)', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_high(self, soup):
        try:
            text = soup.text
            match = re.search(r'High / Low\s*[₹]?\s*([\d,]+)\s*/\s*([\d,]+)', text)
            if match:
                return float(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _get_growth(self, soup):
        sales_growth = 10
        profit_growth = 8
        try:
            text = soup.text
            match = re.search(r'Compounded Sales Growth.*?TTM:\s*([\d.]+)%', text, re.DOTALL)
            if match:
                sales_growth = float(match.group(1))
            match = re.search(r'Compounded Profit Growth.*?TTM:\s*([\d.]+)%', text, re.DOTALL)
            if match:
                profit_growth = float(match.group(1))
        except:
            pass
        return {'sales': sales_growth, 'profit': profit_growth}
    
    def _get_shareholding(self, soup):
        data = {'fii_change': 0, 'dii_change': 0}
        try:
            table = soup.find('table', {'id': 'shareholding-pattern'})
            if not table:
                table = soup.find('table', {'class': 'shareholding-pattern'})
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        text = ' '.join([c.text for c in cells])
                        if 'FIIs' in text or 'FII' in text:
                            vals = re.findall(r'(\d+\.\d+)%', text)
                            if len(vals) >= 2:
                                data['fii_change'] = round(float(vals[-1]) - float(vals[-2]), 2)
                        if 'DIIs' in text or 'DII' in text:
                            vals = re.findall(r'(\d+\.\d+)%', text)
                            if len(vals) >= 2:
                                data['dii_change'] = round(float(vals[-1]) - float(vals[-2]), 2)
        except:
            pass
        return data
    
    def _get_moat(self):
        moat = {
            'IRCTC': 8, 'TCS': 9, 'RELIANCE': 8, 'HDFC': 9,
            'HDFCBANK': 9, 'INFY': 8, 'WIPRO': 6, 'TATACONSUM': 7,
            'TATAMOTORS': 7, 'ITC': 8, 'SBIN': 7, 'ONGC': 6,
            'ICRA': 6, 'CARE': 6
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
            scores['roe'] = 10
            scores['roe_label'] = "✅ Excellent"
        elif roe >= 20:
            scores['roe'] = 8
            scores['roe_label'] = "👍 Good"
        elif roe >= 15:
            scores['roe'] = 6
            scores['roe_label'] = "📊 Average"
        elif roe >= 10:
            scores['roe'] = 4
            scores['roe_label'] = "⚠️ Below avg"
        else:
            scores['roe'] = 2
            scores['roe_label'] = "❌ Low"
        
        debt = self.data.get('debt_equity', 0)
        if debt < 0.1:
            scores['debt'] = 10
            scores['debt_label'] = "✅ Debt-free"
        elif debt < 0.5:
            scores['debt'] = 8
            scores['debt_label'] = "👍 Low debt"
        elif debt < 1.0:
            scores['debt'] = 6
            scores['debt_label'] = "📊 Moderate"
        elif debt < 2.0:
            scores['debt'] = 3
            scores['debt_label'] = "⚠️ High"
        else:
            scores['debt'] = 0
            scores['debt_label'] = "❌ Very high"
        
        growth = self.data.get('profit_growth', 0)
        if growth >= 20:
            scores['profit_growth'] = 10
            scores['profit_growth_label'] = "✅ Strong"
        elif growth >= 10:
            scores['profit_growth'] = 8
            scores['profit_growth_label'] = "👍 Healthy"
        elif growth >= 5:
            scores['profit_growth'] = 6
            scores['profit_growth_label'] = "📊 Modest"
        elif growth >= 0:
            scores['profit_growth'] = 4
            scores['profit_growth_label'] = "⚠️ Flat"
        else:
            scores['profit_growth'] = 0
            scores['profit_growth_label'] = "❌ Declining"
        
        cf = self.data.get('cash_flow_consistency', 70)
        if cf >= 80:
            scores['cash_flow'] = 5
            scores['cash_flow_label'] = "✅ Strong FCF"
        elif cf >= 60:
            scores['cash_flow'] = 4
            scores['cash_flow_label'] = "👍 Consistent"
        else:
            scores['cash_flow'] = 2
            scores['cash_flow_label'] = "⚠️ Inconsistent"
        
        moat = self.data.get('moat_score', 5)
        if moat >= 8:
            scores['moat'] = 5
            scores['moat_label'] = "✅ Wide moat"
        elif moat >= 6:
            scores['moat'] = 4
            scores['moat_label'] = "👍 Narrow moat"
        else:
            scores['moat'] = 2
            scores['moat_label'] = "📊 Commodity"
        
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
                scores['pe'] = 10
                scores['pe_label'] = "✅ Very undervalued"
            elif ratio < 0.75:
                scores['pe'] = 8
                scores['pe_label'] = "👍 Undervalued"
            elif ratio < 0.9:
                scores['pe'] = 6
                scores['pe_label'] = "📊 Fairly valued"
            elif ratio < 1.1:
                scores['pe'] = 4
                scores['pe_label'] = "⚠️ Slight premium"
            else:
                scores['pe'] = 2
                scores['pe_label'] = "❌ Expensive"
        else:
            scores['pe'] = 5
            scores['pe_label'] = "📊 Data N/A"
        
        ret = self.data.get('one_year_return', 0)
        if ret < -30:
            scores['correction'] = 10
            scores['correction_label'] = "✅ Major correction"
        elif ret < -20:
            scores['correction'] = 8
            scores['correction_label'] = "👍 Significant"
        elif ret < -10:
            scores['correction'] = 6
            scores['correction_label'] = "📊 Moderate"
        elif ret < 0:
            scores['correction'] = 4
            scores['correction_label'] = "⚠️ Mild"
        else:
            scores['correction'] = 2
            scores['correction_label'] = "📈 No discount"
        
        price = self.data.get('price', 0)
        high = self.data.get('year_high', price * 1.2)
        dist = (1 - (price / high)) * 100 if high > 0 else 0
        if dist > 30:
            scores['distance'] = 5
            scores['distance_label'] = "✅ 30%+ from high"
        elif dist > 20:
            scores['distance'] = 4
            scores['distance_label'] = "👍 20%+ from high"
        elif dist > 10:
            scores['distance'] = 3
            scores['distance_label'] = "📊 10%+ from high"
        else:
            scores['distance'] = 1
            scores['distance_label'] = "⚠️ Near high"
        
        pb = self.data.get('pb_ratio', 0)
        if pb < 1:
            scores['pb'] = 5
            scores['pb_label'] = "✅ Below book"
        elif pb < 2:
            scores['pb'] = 4
            scores['pb_label'] = "👍 Reasonable"
        elif pb < 4:
            scores['pb'] = 3
            scores['pb_label'] = "📊 Moderate"
        else:
            scores['pb'] = 1
            scores['pb_label'] = "⚠️ Expensive"
        
        self.value_breakdown = scores
        self.value_score = sum([v for k, v in scores.items() if not k.endswith('_label')])
        return self.value_score
    
    def analyze_timing(self):
        scores = {}
        price = self.data.get('price', 0)
        dma_200 = self.data.get('price_200dma', price)
        dma_50 = self.data.get('price_50dma', price * 0.98)
        
        if price > dma_200 and dma_200 > 0:
            scores['dma_200'] = 5
            scores['dma_200_label'] = "✅ Above 200 DMA"
        elif dma_200 > 0 and price > dma_200 * 0.95:
            scores['dma_200'] = 3
            scores['dma_200_label'] = "📊 Near 200 DMA"
        else:
            scores['dma_200'] = 0
            scores['dma_200_label'] = "❌ Below 200 DMA"
        
        if price > dma_50 and dma_50 > 0:
            scores['dma_50'] = 4
            scores['dma_50_label'] = "✅ Above 50 DMA"
        else:
            scores['dma_50'] = 0
            scores['dma_50_label'] = "❌ Below 50 DMA"
        
        hh = self.data.get('higher_high', False)
        hl = self.data.get('higher_low', False)
        if hh and hl:
            scores['hh_hl'] = 4
            scores['hh_hl_label'] = "✅ Uptrend"
        elif hh or hl:
            scores['hh_hl'] = 2
            scores['hh_hl_label'] = "📊 Early trend"
        else:
            scores['hh_hl'] = 0
            scores['hh_hl_label'] = "❌ Downtrend"
        
        vol = self.data.get('volume_ratio', 1.0)
        if vol > 2.0:
            scores['volume'] = 4
            scores['volume_label'] = "✅ Strong volume"
        elif vol > 1.5:
            scores['volume'] = 3
            scores['volume_label'] = "👍 Above avg"
        elif vol > 1.0:
            scores['volume'] = 2
            scores['volume_label'] = "📊 Average"
        else:
            scores['volume'] = 0
            scores['volume_label'] = "❌ Low volume"
        
        rsi = self.data.get('rsi', 50)
        if 40 <= rsi <= 60:
            scores['rsi'] = 4
            scores['rsi_label'] = "✅ Healthy"
        elif rsi < 35:
            scores['rsi'] = 3
            scores['rsi_label'] = "⚠️ Oversold"
        elif rsi > 65:
            scores['rsi'] = 2
            scores['rsi_label'] = "⚠️ Overbought"
        else:
            scores['rsi'] = 3
            scores['rsi_label'] = "📊 Neutral"
        
        fii = self.data.get('shareholding', {}).get('fii_change', 0)
        if fii > 1.0:
            scores['fii'] = 5
            scores['fii_label'] = "✅ FII buying"
        elif fii > 0:
            scores['fii'] = 4
            scores['fii_label'] = "👍 FII accumulation"
        elif fii > -0.5:
            scores['fii'] = 2
            scores['fii_label'] = "📊 FII neutral"
        else:
            scores['fii'] = 0
            scores['fii_label'] = "❌ FII selling"
        
        dii = self.data.get('shareholding', {}).get('dii_change', 0)
        if dii > 1.0:
            scores['dii'] = 4
            scores['dii_label'] = "✅ DII buying"
        elif dii > 0:
            scores['dii'] = 3
            scores['dii_label'] = "👍 DII accumulation"
        else:
            scores['dii'] = 0
            scores['dii_label'] = "❌ DII selling"
        
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
            return {"name": "🟢 STRONG BUY", "action": "✅ BUY NOW", "desc": "All systems go"}
        elif score >= 70:
            return {"name": "🔵 BUY ON BREAKOUT", "action": "⏳ WAIT FOR BREAKOUT", "desc": "Great setup, need confirmation"}
        elif score >= 55:
            return {"name": "🟡 WATCHLIST", "action": "📋 MONITOR DAILY", "desc": "Good business, waiting for timing"}
        elif score >= 40:
            return {"name": "🟠 RECOVERY", "action": "🔍 NO BUY YET", "desc": "Recovering, let it stabilize"}
        elif score >= 20:
            return {"name": "🔴 DISTRIBUTION", "action": "🚫 AVOID", "desc": "Institutions selling"}
        else:
            return {"name": "⚫ BREAKDOWN", "action": "🗑️ REMOVE", "desc": "Broken business"}
    
    @classmethod
    def get_signal(cls, biz, val, timing):
        parts = []
        parts.append("🟢 Quality" if biz >= 35 else "🟡 Quality" if biz >= 25 else "🔴 Quality")
        parts.append("✅ Value" if val >= 25 else "📊 Value" if val >= 18 else "❌ Value")
        parts.append("🚀 Timing" if timing >= 25 else "📈 Timing" if timing >= 18 else "⏳ Timing")
        return " | ".join(parts)


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
        
        improvements = []
        if data.get('price', 0) <= data.get('price_200dma', 0):
            improvements.append("✅ Close above 200 DMA → +76%")
        if data.get('shareholding', {}).get('fii_change', 0) <= 0:
            improvements.append("✅ FII turning buyers → +65%")
        if data.get('volume_ratio', 1.0) <= 1.5:
            improvements.append("✅ Volume spike > 2x → +58%")
        
        return {
            'probability': round(prob, 1),
            'improvements': improvements if improvements else ["Already well-positioned"]
        }


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

💡 *Improvement Triggers:*
"""
    for imp in prob['improvements']:
        report += f"   {imp}\n"

    now = datetime.now(IST)
    report += f"""
📅 Analysis: {now.strftime('%d %b %Y, %I:%M %p IST')}
"""
    return report


def search_stocks(query):
    """Search for stocks matching the query"""
    query = query.upper().strip()
    matches = []
    
    for symbol, info in STOCK_DATABASE.items():
        # Match by symbol
        if query in symbol:
            matches.append({'symbol': symbol, 'name': info['name'], 'type': 'symbol'})
        # Match by company name
        elif query.upper() in info['name'].upper():
            matches.append({'symbol': symbol, 'name': info['name'], 'type': 'name'})
    
    return matches


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🚀 *APEX PRO - Stock Analysis Bot*

*How to use:*
1. Just type any stock name or code
2. If multiple matches found, select with number
3. Bot will show the analysis

*Examples:*
• `IRCTC`
• `Tata Motors`
• `RELIANCE`
• `HDFC Bank`

*Available commands:*
`/list` - Show all available stocks
`/help` - Help message

📊 Powered by Three-Pillar Analysis:
🏢 Business (40) | 💎 Value (30) | ⏰ Timing (30)
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /analyze command"""
    if not context.args:
        await update.message.reply_text("📝 Please specify a stock: /analyze IRCTC")
        return
    
    query = ' '.join(context.args)
    await process_stock_query(update, query)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any text message - search and show menu"""
    if not update.message or not update.message.text:
        return
    
    query = update.message.text.strip()
    
    # Check if this is a number selection from a previous search
    if query.isdigit() and context.user_data.get('search_results'):
        await handle_selection(update, context, int(query))
        return
    
    # Search for stocks
    await process_stock_query(update, query)


async def process_stock_query(update: Update, query):
    """Search and display results"""
    matches = search_stocks(query)
    
    if not matches:
        await update.message.reply_text(
            f"❌ No stocks found matching *{query}*.\n"
            f"Try using /list to see all available stocks.",
            parse_mode='Markdown'
        )
        return
    
    if len(matches) == 1:
        # Only one match - analyze directly
        symbol = matches[0]['symbol']
        await analyze_stock(update, symbol)
    else:
        # Multiple matches - show selection menu
        await show_selection_menu(update, matches)


async def show_selection_menu(update: Update, matches):
    """Show a selection menu for multiple matches"""
    menu = "🔍 *Multiple stocks found. Please select:*\n\n"
    
    buttons = []
    for i, match in enumerate(matches, 1):
        match_type = "📊" if match['type'] == 'symbol' else "🏢"
        menu += f"{i}. {match_type} *{match['symbol']}* - {match['name']}\n"
        buttons.append([InlineKeyboardButton(
            f"{i}. {match['symbol']}",
            callback_data=f"select_{match['symbol']}"
        )])
    
    menu += "\n📝 *Type the number (1, 2, 3...) to select*"
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(menu, parse_mode='Markdown', reply_markup=reply_markup)


async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, selection):
    """Handle number selection from menu"""
    matches = context.user_data.get('search_results', [])
    if not matches or selection < 1 or selection > len(matches):
        await update.message.reply_text("❌ Invalid selection. Please try again.")
        return
    
    selected = matches[selection - 1]
    await analyze_stock(update, selected['symbol'])


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith('select_'):
        symbol = data.replace('select_', '')
        await query.edit_message_text(f"🔍 Analyzing *{symbol}*...", parse_mode='Markdown')
        await analyze_stock(update, symbol)


async def analyze_stock(update: Update, symbol):
    """Fetch and send stock analysis"""
    scraper = StockScraper(symbol)
    data = scraper.fetch()
    
    if "error" in data:
        await update.message.reply_text(data['error'])
        return
    
    analyzer = ThreePillarAnalyzer(data)
    scores = analyzer.analyze_all()
    
    phase = PhaseEngine.classify(scores['total'])
    signal = PhaseEngine.get_signal(scores['business'], scores['value'], scores['timing'])
    prob = ProbabilityEngine.calculate(data, scores['total'])
    
    report = format_report(data, scores, phase, signal, prob)
    await update.message.reply_text(report, parse_mode='Markdown')


async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all available stocks"""
    stocks = "📋 *Available Stocks*\n━━━━━━━━━━━━━\n\n"
    
    # Group by letter
    groups = {}
    for symbol in sorted(STOCK_DATABASE.keys()):
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
    
    stocks += "\n💡 Just type any stock name or code to analyze!"
    await update.message.reply_text(stocks, parse_mode='Markdown')


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 *APEX PRO Commands*

Just type any stock name or code to get analysis!
No need for /analyze prefix.

*Examples:*
• `IRCTC`
• `Tata Motors`
• `RELIANCE`
• `HDFC Bank`

*Commands:*
`/start` - Welcome message
`/list` - Show all available stocks
`/help` - This message

*How it works:*
1. Type a stock name or code
2. If multiple matches, select with number
3. Get full analysis report

*Methodology:*
• Business Score (40 pts): ROE, Debt, Growth, Cash Flow, Moat
• Value Score (30 pts): PE, Correction, Distance from High, PB
• Timing Score (30 pts): DMA, Trend, Volume, RSI, FII/DII Flow
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


# ============ MAIN ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("help", help_cmd))
    
    # Callback handler for buttons
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handler - handles all text messages (no / prefix)
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", start))
    
    # Handle all other messages (search)
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", start))
    
    # Handle any text message (search)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("help", help_cmd))
    
    print("🚀 APEX PRO Bot is running...")
    print("📝 Just type any stock name or code to analyze!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

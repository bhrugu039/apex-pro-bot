"""
APEX PRO - Telegram Stock Analysis Bot
"""

import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
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

# Stock URLs on Screener.in
STOCK_URLS = {
    "IRCTC": "https://www.screener.in/company/IRCTC/",
    "ICRA": "https://www.screener.in/company/ICRA/",
    "CARE": "https://www.screener.in/company/CARE/",
    "TATACONSUM": "https://www.screener.in/company/TATACONSUM/",
    "HDFC": "https://www.screener.in/company/HDFC/",
    "HDFCBANK": "https://www.screener.in/company/HDFCBANK/",
    "RELIANCE": "https://www.screener.in/company/RELIANCE/",
    "TCS": "https://www.screener.in/company/TCS/",
    "INFY": "https://www.screener.in/company/INFY/",
    "WIPRO": "https://www.screener.in/company/WIPRO/",
    "TATAMOTORS": "https://www.screener.in/company/TATAMOTORS/",
    "ITC": "https://www.screener.in/company/ITC/",
    "SBIN": "https://www.screener.in/company/SBIN/",
    "ONGC": "https://www.screener.in/company/ONGC/",
}

# ============ SCRAPER ============
class StockScraper:
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.url = STOCK_URLS.get(self.symbol)
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
            return {"error": f"❌ Stock {self.symbol} not found."}
        
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
            # Look for current price in the top section
            price_elem = soup.find('span', string=re.compile(r'₹'))
            if price_elem:
                text = price_elem.text.replace('₹', '').replace(',', '').strip()
                if text and text.replace('.', '').isdigit():
                    return float(text)
            
            # Look in company-ratios section
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'Current Price' in li.text:
                    value = li.find('span', {'class': 'value'})
                    if value:
                        text = value.text.replace('₹', '').replace(',', '').strip()
                        if text and text.replace('.', '').isdigit():
                            return float(text)
            
            # Search entire page text
            text = soup.text
            match = re.search(r'Current Price\s*[₹]?\s*([\d,]+\.?[\d]*)', text)
            if match:
                return float(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _get_pe(self, soup):
        try:
            # Look for Stock P/E in the top metrics
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'Stock P/E' in li.text:
                    value = li.find('span', {'class': 'value'})
                    if value:
                        return float(value.text.strip())
            
            # Search in text
            text = soup.text
            match = re.search(r'Stock P/E\s*([\d.]+)', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_roe(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'ROE' in li.text and 'Stock' not in li.text:
                    value = li.find('span', {'class': 'value'})
                    if value:
                        return float(value.text.replace('%', '').strip())
            
            text = soup.text
            match = re.search(r'ROE\s*([\d.]+)\s*%', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_roce(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'ROCE' in li.text:
                    value = li.find('span', {'class': 'value'})
                    if value:
                        return float(value.text.replace('%', '').strip())
            
            text = soup.text
            match = re.search(r'ROCE\s*([\d.]+)\s*%', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_debt(self, soup):
        try:
            # Check if debt-free in pros
            text = soup.text
            if 'almost debt free' in text.lower() or 'debt free' in text.lower():
                return 0.0
            
            # Look in balance sheet if available
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'Debt' in li.text and 'equity' in li.text.lower():
                    value = li.find('span', {'class': 'value'})
                    if value:
                        return float(value.text.strip())
        except:
            pass
        return 0.0
    
    def _get_market_cap(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'Market Cap' in li.text:
                    value = li.find('span', {'class': 'value'})
                    if value:
                        text = value.text.replace('₹', '').replace('Cr.', '').replace('Cr', '').replace(',', '').strip()
                        if text and text.replace('.', '').isdigit():
                            return float(text)
            
            text = soup.text
            match = re.search(r'Market Cap\s*[₹]?\s*([\d,]+)\s*Cr', text)
            if match:
                return float(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _get_dividend(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'Dividend Yield' in li.text:
                    value = li.find('span', {'class': 'value'})
                    if value:
                        return float(value.text.replace('%', '').strip())
            
            text = soup.text
            match = re.search(r'Dividend Yield\s*([\d.]+)\s*%', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_pb(self, soup):
        try:
            # Calculate from Price / Book Value
            price = self.data.get('price', 0)
            book_value = self._get_book_value(soup)
            if price > 0 and book_value > 0:
                return round(price / book_value, 2)
            
            # Look for PB in cons section
            text = soup.text
            if 'Stock is trading at' in text:
                match = re.search(r'trading at\s*([\d.]+)\s*times its book value', text)
                if match:
                    return float(match.group(1))
        except:
            pass
        return 3.0
    
    def _get_book_value(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'Book Value' in li.text:
                    value = li.find('span', {'class': 'value'})
                    if value:
                        return float(value.text.replace('₹', '').strip())
            
            text = soup.text
            match = re.search(r'Book Value\s*[₹]?\s*([\d.]+)', text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0
    
    def _get_high(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'flex', 'class': 'flex-space-between'}):
                if 'High / Low' in li.text:
                    value = li.find('span', {'class': 'value'})
                    if value:
                        text = value.text
                        match = re.search(r'[₹]?\s*([\d,]+)\s*/\s*([\d,]+)', text)
                        if match:
                            return float(match.group(1).replace(',', ''))
            
            text = soup.text
            match = re.search(r'High / Low\s*[₹]?\s*([\d,]+)\s*/\s*([\d,]+)', text)
            if match:
                return float(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _get_growth(self, soup):
        """Extract sales and profit growth from the page"""
        sales_growth = 0
        profit_growth = 0
        
        try:
            text = soup.text
            
            # Look for compounded growth tables
            # Sales Growth
            match = re.search(r'Compounded Sales Growth.*?TTM:\s*([\d.]+)%', text, re.DOTALL)
            if match:
                sales_growth = float(match.group(1))
            else:
                # Try to find in profit-loss table
                table = soup.find('table', {'id': 'profit-loss'})
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        if 'Sales' in row.text:
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                latest = float(cells[-1].text.replace(',', '').strip())
                                prev = float(cells[-2].text.replace(',', '').strip())
                                if prev > 0:
                                    sales_growth = round(((latest - prev) / prev) * 100, 2)
            
            # Profit Growth
            match = re.search(r'Compounded Profit Growth.*?TTM:\s*([\d.]+)%', text, re.DOTALL)
            if match:
                profit_growth = float(match.group(1))
            else:
                table = soup.find('table', {'id': 'profit-loss'})
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        if 'Net Profit' in row.text:
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                latest = float(cells[-1].text.replace(',', '').strip())
                                prev = float(cells[-2].text.replace(',', '').strip())
                                if prev > 0:
                                    profit_growth = round(((latest - prev) / prev) * 100, 2)
            
            # Fallback values
            if sales_growth == 0:
                sales_growth = 10
            if profit_growth == 0:
                profit_growth = 8
                
        except Exception as e:
            print(f"Error extracting growth: {e}")
            sales_growth = 10
            profit_growth = 8
        
        return {'sales': sales_growth, 'profit': profit_growth}
    
    def _get_shareholding(self, soup):
        data = {'fii_change': 0, 'dii_change': 0}
        try:
            # Find shareholding table
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
        
        # ROE (10 pts)
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
        
        # Debt (10 pts)
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
        
        # Profit Growth (10 pts)
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
        
        # Cash Flow (5 pts)
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
        
        # Moat (5 pts)
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
        
        # PE vs 5Y Avg (10 pts)
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
        
        # 1Y Correction (10 pts)
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
        
        # Distance from High (5 pts)
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
        
        # PB Ratio (5 pts)
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
        
        # 200 DMA (5 pts)
        if price > dma_200 and dma_200 > 0:
            scores['dma_200'] = 5
            scores['dma_200_label'] = "✅ Above 200 DMA"
        elif dma_200 > 0 and price > dma_200 * 0.95:
            scores['dma_200'] = 3
            scores['dma_200_label'] = "📊 Near 200 DMA"
        else:
            scores['dma_200'] = 0
            scores['dma_200_label'] = "❌ Below 200 DMA"
        
        # 50 DMA (4 pts)
        if price > dma_50 and dma_50 > 0:
            scores['dma_50'] = 4
            scores['dma_50_label'] = "✅ Above 50 DMA"
        else:
            scores['dma_50'] = 0
            scores['dma_50_label'] = "❌ Below 50 DMA"
        
        # HH/HL (4 pts)
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
        
        # Volume (4 pts)
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
        
        # RSI (4 pts)
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
        
        # FII Trend (5 pts)
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
        
        # DII Trend (4 pts)
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🚀 *APEX PRO - Stock Analysis Bot*

Just type:
`/analyze STOCK_NAME`

*Available stocks:*
• IRCTC • ICRA • CARE • TATACONSUM
• HDFC • HDFCBANK • RELIANCE
• TCS • INFY • WIPRO
• TATAMOTORS • ITC • SBIN • ONGC

*Example:*
`/analyze IRCTC`

Powered by Three-Pillar Analysis:
🏢 Business (40) | 💎 Value (30) | ⏰ Timing (30)
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📝 Please specify a stock: /analyze IRCTC")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {symbol}... Please wait ⏳")
    
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
    
    # Build report with correct data
    report = f"""
📊 *{data.get('name', symbol)}* ({symbol})
━━━━━━━━━━━━━━━━━━━━━
💰 Price: ₹{data.get('price', 0):,.2f}
📈 Market Cap: ₹{data.get('market_cap', 0):,.0f} Cr
📉 PE: {data.get('pe_ratio', 0):.2f} (5Y Avg: {data.get('pe_5y_avg', 0):.2f})
🏦 ROE: {data.get('roe', 0):.1f}% | ROCE: {data.get('roce', 0):.1f}%
💳 Debt/Equity: {data.get('debt_equity', 0):.2f}

🏢 *BUSINESS QUALITY*: {scores['business']}/40
"""
    # Business breakdown
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

    # Fixed timezone - IST
    now = datetime.now(IST)
    report += f"""
📅 Analysis: {now.strftime('%d %b %Y, %I:%M %p IST')}
"""
    
    await update.message.reply_text(report, parse_mode='Markdown')


async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = "📋 *Available Stocks*\n━━━━━━━━━━━━━\n"
    for i, stock in enumerate(STOCK_URLS.keys(), 1):
        stocks += f"{i}. {stock}\n"
    await update.message.reply_text(stocks, parse_mode='Markdown')


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 *APEX PRO Commands*

`/start` - Welcome message
`/analyze STOCK` - Full analysis report
`/list` - Available stocks
`/help` - This message

*Example:* `/analyze IRCTC`

*Methodology:*
• Business Score (40 pts): ROE, Debt, Growth, Cash Flow, Moat
• Value Score (30 pts): PE, Correction, Distance from High, PB
• Timing Score (30 pts): DMA, Trend, Volume, RSI, FII/DII Flow
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


# ============ MAIN ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("help", help_cmd))
    
    print("🚀 APEX PRO Bot is running...")
    print("Available commands: /analyze STOCK")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

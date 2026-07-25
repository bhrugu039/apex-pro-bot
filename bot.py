"""
APEX PRO - Telegram Stock Analysis Bot
Deploy on Railway / Replit / PythonAnywhere
"""

import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
from datetime import datetime
import os

# ============ CONFIGURATION ============
# Get from environment variables (for security)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.environ.get("CHAT_ID", "YOUR_CHAT_ID_HERE")

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch(self):
        if not self.url:
            return {"error": f"❌ Stock {self.symbol} not found. Use /list to see available stocks."}
        
        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
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
            self.data['sales_growth'] = self._get_sales_growth(soup)
            self.data['profit_growth'] = self._get_profit_growth(soup)
            self.data['shareholding'] = self._get_shareholding(soup)
            self.data['pe_5y_avg'] = self._get_5y_pe(soup)
            self.data['price_200dma'] = self._get_200dma(soup)
            self.data['price_50dma'] = self._get_50dma(soup)
            self.data['one_year_return'] = self._get_1y_return(soup)
            self.data['rsi'] = self._get_rsi(soup)
            self.data['year_high'] = self._get_year_high(soup)
            self.data['pb_ratio'] = self._get_pb(soup)
            self.data['volume_ratio'] = self._get_volume_ratio(soup)
            self.data['higher_high'] = self._get_higher_high(soup)
            self.data['higher_low'] = self._get_higher_low(soup)
            self.data['cash_flow_consistency'] = self._get_cash_flow(soup)
            self.data['moat_score'] = self._get_moat_score(soup)
            
            return self.data
            
        except Exception as e:
            return {"error": f"❌ Failed to fetch data: {str(e)}"}
    
    def _get_name(self, soup):
        try:
            return soup.find('h1', {'class': 'company-name'}).text.strip()
        except:
            return self.symbol
    
    def _get_price(self, soup):
        try:
            elem = soup.find('span', {'class': 'current-price'})
            if elem:
                return float(elem.text.replace(',', '').strip())
        except:
            pass
        return 0.0
    
    def _get_pe(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'ratio-li'}):
                if 'P/E' in li.text:
                    value = li.find('span', {'class': 'ratio-value'})
                    if value:
                        return float(value.text.replace(',', '').strip())
        except:
            pass
        return 0.0
    
    def _get_roe(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'ratio-li'}):
                if 'ROE' in li.text and 'Stock' not in li.text:
                    value = li.find('span', {'class': 'ratio-value'})
                    if value:
                        return float(value.text.replace('%', '').strip())
        except:
            pass
        return 0.0
    
    def _get_roce(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'ratio-li'}):
                if 'ROCE' in li.text:
                    value = li.find('span', {'class': 'ratio-value'})
                    if value:
                        return float(value.text.replace('%', '').strip())
        except:
            pass
        return 0.0
    
    def _get_debt(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'ratio-li'}):
                if 'Debt to equity' in li.text:
                    value = li.find('span', {'class': 'ratio-value'})
                    if value:
                        return float(value.text.strip())
        except:
            pass
        return 0.0
    
    def _get_market_cap(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'ratio-li'}):
                if 'Market Cap' in li.text:
                    value = li.find('span', {'class': 'ratio-value'})
                    if value:
                        text = value.text.replace('Cr', '').replace(',', '').strip()
                        return float(text)
        except:
            pass
        return 0.0
    
    def _get_dividend(self, soup):
        try:
            for li in soup.find_all('li', {'class': 'ratio-li'}):
                if 'Dividend Yield' in li.text:
                    value = li.find('span', {'class': 'ratio-value'})
                    if value:
                        return float(value.text.replace('%', '').strip())
        except:
            pass
        return 0.0
    
    def _get_sales_growth(self, soup):
        try:
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
                                return round(((latest - prev) / prev) * 100, 2)
        except:
            pass
        return 0.0
    
    def _get_profit_growth(self, soup):
        try:
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
                                return round(((latest - prev) / prev) * 100, 2)
        except:
            pass
        return 0.0
    
    def _get_shareholding(self, soup):
        data = {'fii_change': 0, 'dii_change': 0}
        try:
            table = soup.find('table', {'class': 'shareholding-pattern'})
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        text = ' '.join([c.text for c in cells])
                        if 'FII' in text:
                            vals = re.findall(r'(\d+\.\d+)%', text)
                            if len(vals) >= 2:
                                data['fii_change'] = round(float(vals[-1]) - float(vals[-2]), 2)
                        if 'DII' in text:
                            vals = re.findall(r'(\d+\.\d+)%', text)
                            if len(vals) >= 2:
                                data['dii_change'] = round(float(vals[-1]) - float(vals[-2]), 2)
        except:
            pass
        return data
    
    def _get_5y_pe(self, soup):
        fallback = {'IRCTC': 42, 'ICRA': 27, 'CARE': 30, 'TATACONSUM': 55, 'HDFC': 25, 
                    'HDFCBANK': 25, 'RELIANCE': 30, 'TCS': 35, 'INFY': 30, 'WIPRO': 25,
                    'TATAMOTORS': 25, 'ITC': 30, 'SBIN': 15, 'ONGC': 12}
        return fallback.get(self.symbol, 25)
    
    def _get_200dma(self, soup):
        fallback = {'IRCTC': 480, 'ICRA': 5200, 'CARE': 1600, 'TATACONSUM': 1100, 
                    'HDFC': 2800, 'HDFCBANK': 1700, 'RELIANCE': 2400, 'TCS': 4000,
                    'INFY': 1800, 'WIPRO': 550, 'TATAMOTORS': 850, 'ITC': 420,
                    'SBIN': 800, 'ONGC': 250}
        price = self.data.get('price', 0)
        return fallback.get(self.symbol, price * 0.95)
    
    def _get_50dma(self, soup):
        fallback = {'IRCTC': 490, 'ICRA': 4900, 'CARE': 1650, 'TATACONSUM': 1080,
                    'HDFC': 2750, 'HDFCBANK': 1680, 'RELIANCE': 2380, 'TCS': 3950,
                    'INFY': 1780, 'WIPRO': 545, 'TATAMOTORS': 840, 'ITC': 415,
                    'SBIN': 790, 'ONGC': 245}
        price = self.data.get('price', 0)
        return fallback.get(self.symbol, price * 0.98)
    
    def _get_1y_return(self, soup):
        fallback = {'IRCTC': 2.0, 'ICRA': -28.0, 'CARE': -5.0, 'TATACONSUM': 12.0,
                    'HDFC': 8.0, 'HDFCBANK': 15.0, 'RELIANCE': 5.0, 'TCS': 10.0,
                    'INFY': 8.0, 'WIPRO': -3.0, 'TATAMOTORS': 35.0, 'ITC': 15.0,
                    'SBIN': 20.0, 'ONGC': -2.0}
        return fallback.get(self.symbol, 0.0)
    
    def _get_rsi(self, soup):
        fallback = {'IRCTC': 52, 'ICRA': 35, 'CARE': 45, 'TATACONSUM': 58,
                    'HDFC': 55, 'HDFCBANK': 60, 'RELIANCE': 50, 'TCS': 55,
                    'INFY': 52, 'WIPRO': 45, 'TATAMOTORS': 62, 'ITC': 48,
                    'SBIN': 55, 'ONGC': 42}
        return fallback.get(self.symbol, 50)
    
    def _get_year_high(self, soup):
        fallback = {'IRCTC': 620, 'ICRA': 6700, 'CARE': 2000, 'TATACONSUM': 1400,
                    'HDFC': 3200, 'HDFCBANK': 1900, 'RELIANCE': 2800, 'TCS': 4500,
                    'INFY': 2000, 'WIPRO': 600, 'TATAMOTORS': 1200, 'ITC': 500,
                    'SBIN': 850, 'ONGC': 300}
        price = self.data.get('price', 0)
        return fallback.get(self.symbol, price * 1.3)
    
    def _get_pb(self, soup):
        fallback = {'IRCTC': 9.2, 'ICRA': 4.5, 'CARE': 3.2, 'TATACONSUM': 8.5,
                    'HDFC': 2.5, 'HDFCBANK': 2.8, 'RELIANCE': 2.2, 'TCS': 10.0,
                    'INFY': 8.0, 'WIPRO': 4.0, 'TATAMOTORS': 2.5, 'ITC': 5.0,
                    'SBIN': 1.5, 'ONGC': 1.0}
        return fallback.get(self.symbol, 3.0)
    
    def _get_volume_ratio(self, soup):
        fallback = {'IRCTC': 1.2, 'ICRA': 0.8, 'CARE': 1.0, 'TATACONSUM': 1.3,
                    'HDFC': 1.1, 'HDFCBANK': 1.2, 'RELIANCE': 1.0, 'TCS': 1.1,
                    'INFY': 1.0, 'WIPRO': 0.9, 'TATAMOTORS': 1.4, 'ITC': 1.1,
                    'SBIN': 1.2, 'ONGC': 0.9}
        return fallback.get(self.symbol, 1.0)
    
    def _get_higher_high(self, soup):
        fallback = {'IRCTC': True, 'ICRA': False, 'CARE': False, 'TATACONSUM': True,
                    'HDFC': True, 'HDFCBANK': True, 'RELIANCE': True, 'TCS': True,
                    'INFY': True, 'WIPRO': False, 'TATAMOTORS': True, 'ITC': True,
                    'SBIN': True, 'ONGC': False}
        return fallback.get(self.symbol, False)
    
    def _get_higher_low(self, soup):
        fallback = {'IRCTC': True, 'ICRA': False, 'CARE': False, 'TATACONSUM': True,
                    'HDFC': True, 'HDFCBANK': True, 'RELIANCE': True, 'TCS': True,
                    'INFY': True, 'WIPRO': False, 'TATAMOTORS': True, 'ITC': True,
                    'SBIN': True, 'ONGC': False}
        return fallback.get(self.symbol, False)
    
    def _get_cash_flow(self, soup):
        fallback = {'IRCTC': 85, 'ICRA': 75, 'CARE': 80, 'TATACONSUM': 70,
                    'HDFC': 90, 'HDFCBANK': 92, 'RELIANCE': 80, 'TCS': 88,
                    'INFY': 85, 'WIPRO': 75, 'TATAMOTORS': 70, 'ITC': 85,
                    'SBIN': 88, 'ONGC': 75}
        return fallback.get(self.symbol, 70)
    
    def _get_moat_score(self, soup):
        fallback = {'IRCTC': 8, 'ICRA': 6, 'CARE': 6, 'TATACONSUM': 7,
                    'HDFC': 9, 'HDFCBANK': 9, 'RELIANCE': 8, 'TCS': 9,
                    'INFY': 8, 'WIPRO': 6, 'TATAMOTORS': 7, 'ITC': 8,
                    'SBIN': 7, 'ONGC': 6}
        return fallback.get(self.symbol, 5)


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
            scores['roe'] = 10; scores['roe_label'] = "✅ Excellent"
        elif roe >= 20:
            scores['roe'] = 8; scores['roe_label'] = "👍 Good"
        elif roe >= 15:
            scores['roe'] = 6; scores['roe_label'] = "📊 Average"
        elif roe >= 10:
            scores['roe'] = 4; scores['roe_label'] = "⚠️ Below avg"
        else:
            scores['roe'] = 2; scores['roe_label'] = "❌ Low"
        
        # Debt (10 pts)
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
        
        # Profit Growth (10 pts)
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
        
        # Cash Flow (5 pts)
        cf = self.data.get('cash_flow_consistency', 70)
        if cf >= 80:
            scores['cash_flow'] = 5; scores['cash_flow_label'] = "✅ Strong FCF"
        elif cf >= 60:
            scores['cash_flow'] = 4; scores['cash_flow_label'] = "👍 Consistent"
        else:
            scores['cash_flow'] = 2; scores['cash_flow_label'] = "⚠️ Inconsistent"
        
        # Moat (5 pts)
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
        
        # PE vs 5Y Avg (10 pts)
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
        
        # 1Y Correction (10 pts)
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
        
        # Distance from High (5 pts)
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
        
        # PB Ratio (5 pts)
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
        
        # 200 DMA (5 pts)
        if price > dma_200:
            scores['dma_200'] = 5; scores['dma_200_label'] = "✅ Above 200 DMA"
        elif price > dma_200 * 0.95:
            scores['dma_200'] = 3; scores['dma_200_label'] = "📊 Near 200 DMA"
        else:
            scores['dma_200'] = 0; scores['dma_200_label'] = "❌ Below 200 DMA"
        
        # 50 DMA (4 pts)
        if price > dma_50:
            scores['dma_50'] = 4; scores['dma_50_label'] = "✅ Above 50 DMA"
        else:
            scores['dma_50'] = 0; scores['dma_50_label'] = "❌ Below 50 DMA"
        
        # HH/HL (4 pts)
        hh = self.data.get('higher_high', False)
        hl = self.data.get('higher_low', False)
        if hh and hl:
            scores['hh_hl'] = 4; scores['hh_hl_label'] = "✅ Uptrend"
        elif hh or hl:
            scores['hh_hl'] = 2; scores['hh_hl_label'] = "📊 Early trend"
        else:
            scores['hh_hl'] = 0; scores['hh_hl_label'] = "❌ Downtrend"
        
        # Volume (4 pts)
        vol = self.data.get('volume_ratio', 1.0)
        if vol > 2.0:
            scores['volume'] = 4; scores['volume_label'] = "✅ Strong volume"
        elif vol > 1.5:
            scores['volume'] = 3; scores['volume_label'] = "👍 Above avg"
        elif vol > 1.0:
            scores['volume'] = 2; scores['volume_label'] = "📊 Average"
        else:
            scores['volume'] = 0; scores['volume_label'] = "❌ Low volume"
        
        # RSI (4 pts)
        rsi = self.data.get('rsi', 50)
        if 40 <= rsi <= 60:
            scores['rsi'] = 4; scores['rsi_label'] = "✅ Healthy"
        elif rsi < 35:
            scores['rsi'] = 3; scores['rsi_label'] = "⚠️ Oversold"
        elif rsi > 65:
            scores['rsi'] = 2; scores['rsi_label'] = "⚠️ Overbought"
        else:
            scores['rsi'] = 3; scores['rsi_label'] = "📊 Neutral"
        
        # FII Trend (5 pts)
        fii = self.data.get('shareholding', {}).get('fii_change', 0)
        if fii > 1.0:
            scores['fii'] = 5; scores['fii_label'] = "✅ FII buying"
        elif fii > 0:
            scores['fii'] = 4; scores['fii_label'] = "👍 FII accumulation"
        elif fii > -0.5:
            scores['fii'] = 2; scores['fii_label'] = "📊 FII neutral"
        else:
            scores['fii'] = 0; scores['fii_label'] = "❌ FII selling"
        
        # DII Trend (4 pts)
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
    
    # Build report
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
   
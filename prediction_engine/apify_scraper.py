"""
Apify Scraper - אינטגרציה עם Apify API ל-scraping רשימת מניות
"""

import logging
from typing import List, Dict, Any
from apify_client import ApifyClient
from datetime import datetime

from .config import APIFY_CONFIG
from .db_client import SupabaseClient

logger = logging.getLogger(__name__)


class ApifyScraper:
    """
    מחלקה ל-scraping רשימת מניות דרך Apify
    """
    
    def __init__(self):
        """אתחול Apify client"""
        api_token = APIFY_CONFIG['api_token']
        if not api_token:
            raise ValueError("APIFY_API_TOKEN נדרש. בדוק את משתני הסביבה.")
        
        self.client = ApifyClient(api_token)
        self.actor_id = APIFY_CONFIG['actor_id']
        self.input_url = APIFY_CONFIG['input_url']
        self.db_client = SupabaseClient()
    
    def scrape_stock_list(self) -> Dict[str, Any]:
        """
        Scraping של רשימת מניות דרך Apify
        
        Returns:
            Dict עם:
            - success: האם הצליח
            - stocks_scraped: מספר מניות שנמצאו
            - stocks_added: מספר מניות חדשות
            - stocks_updated: מספר מניות שעודכנו
            - message: הודעת סטטוס
        """
        try:
            logger.info("🚀 מתחיל scraping של רשימת מניות דרך Apify...")
            
            # אם יש actor_id, השתמש בו
            if self.actor_id:
                stocks = self._scrape_with_actor()
            else:
                # אחרת, נסה scraping ישיר מ-Wikipedia
                stocks = self._scrape_wikipedia_direct()
            
            if not stocks:
                return {
                    'success': False,
                    'stocks_scraped': 0,
                    'stocks_added': 0,
                    'stocks_updated': 0,
                    'message': 'לא נמצאו מניות'
                }
            
            # עדכון DB
            result = self._update_stock_list(stocks)
            
            logger.info(f"✅ Scraping הושלם: {result['stocks_scraped']} מניות")
            return result
            
        except Exception as e:
            logger.error(f"❌ שגיאה ב-scraping: {e}")
            return {
                'success': False,
                'stocks_scraped': 0,
                'stocks_added': 0,
                'stocks_updated': 0,
                'message': f'שגיאה: {str(e)}'
            }
    
    def _scrape_with_actor(self) -> List[Dict[str, Any]]:
        """
        Scraping דרך Apify Actor
        
        Returns:
            רשימת מניות
        """
        try:
            # הפעלת Actor
            run = self.client.actor(self.actor_id).call(run_input={
                'url': self.input_url
            })
            
            # המתנה לסיום
            run = self.client.run(run['id']).wait_for_finish()
            
            # שליפת תוצאות
            dataset_items = list(self.client.dataset(run['defaultDatasetId']).iterate_items())
            
            stocks = []
            for item in dataset_items:
                # התאמה לפורמט הצפוי
                stock = {
                    'symbol': item.get('symbol') or item.get('Symbol') or item.get('ticker'),
                    'company_name': item.get('company_name') or item.get('Company') or item.get('name'),
                    'sector': item.get('sector') or item.get('Sector') or None
                }
                
                if stock['symbol']:
                    stocks.append(stock)
            
            return stocks
            
        except Exception as e:
            logger.error(f"❌ שגיאה ב-Apify Actor: {e}")
            # נסה scraping ישיר
            return self._scrape_wikipedia_direct()
    
    def _scrape_wikipedia_direct(self) -> List[Dict[str, Any]]:
        """
        Scraping ישיר מ-Wikipedia (fallback)
        
        Returns:
            רשימת מניות
        """
        try:
            import requests
            import pandas as pd
            from io import StringIO
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.input_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            tables = pd.read_html(StringIO(response.text))
            if not tables:
                raise Exception("לא נמצאו טבלאות")
            
            sp500_table = tables[0]
            
            # זיהוי עמודות
            symbol_col = None
            name_col = None
            sector_col = None
            
            for col in sp500_table.columns:
                col_lower = str(col).lower()
                if 'symbol' in col_lower or 'ticker' in col_lower:
                    symbol_col = col
                elif 'company' in col_lower or 'name' in col_lower:
                    name_col = col
                elif 'sector' in col_lower:
                    sector_col = col
            
            if not symbol_col:
                raise Exception("לא נמצאה עמודת סימולים")
            
            stocks = []
            for _, row in sp500_table.iterrows():
                symbol = str(row[symbol_col]).strip()
                if symbol and symbol != 'nan':
                    stock = {
                        'symbol': symbol,
                        'company_name': str(row[name_col]).strip() if name_col else None,
                        'sector': str(row[sector_col]).strip() if sector_col else None
                    }
                    stocks.append(stock)
            
            return stocks
            
        except Exception as e:
            logger.error(f"❌ שגיאה ב-scraping ישיר: {e}")
            return []
    
    def _update_stock_list(self, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        עדכון רשימת מניות ב-DB
        
        Args:
            stocks: רשימת מניות חדשות
            
        Returns:
            Dict עם סטטיסטיקות
        """
        # שליפת מניות קיימות
        existing_stocks = self.db_client.get_stock_list(active_only=False)
        existing_symbols = {s['symbol'] for s in existing_stocks}
        
        stocks_to_insert = []
        stocks_added = 0
        stocks_updated = 0
        
        for stock in stocks:
            symbol = stock['symbol']
            
            if symbol not in existing_symbols:
                # מניה חדשה
                stocks_to_insert.append({
                    'symbol': symbol,
                    'company_name': stock.get('company_name'),
                    'sector': stock.get('sector'),
                    'is_active': True,
                    'scraped_at': datetime.now().isoformat()
                })
                stocks_added += 1
            else:
                # עדכון מניה קיימת
                stocks_to_insert.append({
                    'symbol': symbol,
                    'company_name': stock.get('company_name'),
                    'sector': stock.get('sector'),
                    'is_active': True,
                    'scraped_at': datetime.now().isoformat()
                })
                stocks_updated += 1
        
        # עדכון DB
        if stocks_to_insert:
            self.db_client.upsert_stock_list(stocks_to_insert)
        
        # סימון מניות שהוסרו כלא פעילות
        new_symbols = {s['symbol'] for s in stocks}
        for existing in existing_stocks:
            if existing['symbol'] not in new_symbols and existing['is_active']:
                self.db_client.client.table('stock_list')\
                    .update({'is_active': False})\
                    .eq('symbol', existing['symbol'])\
                    .execute()
        
        return {
            'success': True,
            'stocks_scraped': len(stocks),
            'stocks_added': stocks_added,
            'stocks_updated': stocks_updated,
            'message': f'רשימת מניות עודכנה בהצלחה: {stocks_added} חדשות, {stocks_updated} עודכנו'
        }


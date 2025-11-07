"""
מודול הורדת נתונים מ-Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import time
import os
import pickle


class DataFetcher:
    """
    מחלקה להורדת ועדכון נתוני מניות
    """
    
    def __init__(self, cache_dir: str = "data_cache"):
        """
        אתחול
        
        Args:
            cache_dir: תיקיית קאש לשמירת נתונים
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def get_sp500_symbols(self) -> List[str]:
        """
        קבלת רשימת המניות של S&P 500
        """
        # הורדה מוויקיפדיה
        try:
            import requests
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            
            # הוספת headers כדי להימנע מ-403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # ניסיון עם requests + pandas
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                from io import StringIO
                tables = pd.read_html(StringIO(response.text))
                sp500_table = tables[0]
                symbols = sp500_table['Symbol'].tolist()
                
                # ניקוי סימנים מיוחדים
                symbols = [s.replace('.', '-') for s in symbols]
                
                print(f"נמצאו {len(symbols)} מניות ב-S&P 500")
                return symbols
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            print(f"שגיאה בהורדת רשימת S&P 500: {e}")
            print("מנסה שוב עם pandas.read_html ישירות...")
            
            # ניסיון נוסף ישירות עם pandas
            try:
                url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
                tables = pd.read_html(url, header=0)
                sp500_table = tables[0]
                symbols = sp500_table['Symbol'].tolist()
                symbols = [s.replace('.', '-') for s in symbols]
                print(f"נמצאו {len(symbols)} מניות ב-S&P 500")
                return symbols
            except Exception as e2:
                print(f"גם הניסיון השני נכשל: {e2}")
                print("משתמש ברשימת ברירת מחדל חלקית")
                # רשימה חלקית כברירת מחדל
                return self._get_default_symbols()
    
    def load_symbols_from_file(self, filepath: str) -> List[str]:
        """
        טעינת רשימת מניות מקובץ
        
        Args:
            filepath: נתיב לקובץ (txt או csv עם עמודה אחת של סימולים)
        
        Returns:
            רשימת סימולים
        """
        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
                # נסה עמודה ראשונה או עמודה בשם 'Symbol'
                if 'Symbol' in df.columns:
                    symbols = df['Symbol'].tolist()
                else:
                    symbols = df.iloc[:, 0].tolist()
            else:
                # קובץ טקסט - שורה אחת לכל סימול
                with open(filepath, 'r', encoding='utf-8') as f:
                    symbols = [line.strip() for line in f if line.strip()]
            
            # ניקוי סימנים מיוחדים
            symbols = [s.replace('.', '-') for s in symbols if s]
            print(f"נטענו {len(symbols)} מניות מקובץ: {filepath}")
            return symbols
        except Exception as e:
            print(f"שגיאה בטעינת קובץ מניות: {e}")
            return []
    
    def _get_default_symbols(self) -> List[str]:
        """
        רשימת ברירת מחדל של מניות (למקרה שההורדה נכשלת)
        """
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM',
            'V', 'JNJ', 'WMT', 'PG', 'MA', 'HD', 'BAC', 'DIS', 'ADBE', 'NFLX',
            'CRM', 'CSCO', 'PEP', 'KO', 'INTC', 'AMD', 'PYPL', 'NKE', 'MRK',
            'TMO', 'ABBV', 'ABT', 'COST', 'ACN', 'AVGO', 'TXN', 'DHR', 'LLY',
            'UNP', 'NEE', 'PM', 'BMY', 'UPS', 'LOW', 'QCOM', 'HON', 'ORCL',
            'IBM', 'AMGN', 'GE', 'MDT', 'CAT', 'BA', 'MMM', 'GS', 'AXP'
        ]
    
    def download_stock_data(self, 
                          symbol: str,
                          start_date: str = "2012-01-01",
                          end_date: str = None,
                          use_cache: bool = True) -> pd.DataFrame:
        """
        הורדת נתוני מניה בודדת
        
        Args:
            symbol: סימול המניה
            start_date: תאריך התחלה (ברירת מחדל: 2012-01-01)
            end_date: תאריך סיום (ברירת מחדל: היום)
            use_cache: האם להשתמש בקאש
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_file = os.path.join(self.cache_dir, f"{symbol}_{start_date}_{end_date}.pkl")
        
        # בדוק קאש
        if use_cache and os.path.exists(cache_file):
            # בדוק אם הקובץ עודכן היום
            file_date = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if file_date.date() == datetime.now().date():
                try:
                    with open(cache_file, 'rb') as f:
                        df = pickle.load(f)
                    return df
                except:
                    pass
        
        # הורדה מ-Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                print(f"אין נתונים עבור {symbol}")
                return None
            
            # שמירה בקאש
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            
            return df
            
        except Exception as e:
            print(f"שגיאה בהורדת {symbol}: {e}")
            return None
    
    def download_multiple_stocks(self,
                                symbols: List[str],
                                start_date: str = "2012-01-01",
                                end_date: str = None,
                                use_cache: bool = True,
                                max_workers: int = 10) -> pd.DataFrame:
        """
        הורדת נתונים של מספר מניות
        
        Returns:
            DataFrame עם MultiIndex: (symbol, field)
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"מוריד נתונים עבור {len(symbols)} מניות...")
        print(f"תקופה: {start_date} עד {end_date}")
        
        all_data = {}
        failed_symbols = []
        
        for i, symbol in enumerate(symbols):
            if (i + 1) % 50 == 0:
                print(f"התקדמות: {i+1}/{len(symbols)}")
            
            df = self.download_stock_data(symbol, start_date, end_date, use_cache)
            
            if df is not None and not df.empty:
                # שמור רק את השדות הנדרשים
                for field in ['Close', 'Volume']:
                    all_data[(symbol, field)] = df[field]
            else:
                failed_symbols.append(symbol)
            
            # השהייה קלה כדי לא להעמיס על השרת
            if not use_cache:
                time.sleep(0.1)
        
        if failed_symbols:
            print(f"\nנכשלו {len(failed_symbols)} מניות: {failed_symbols[:10]}...")
        
        # יצירת DataFrame אחד גדול
        combined_df = pd.DataFrame(all_data)
        
        print(f"\nהושלמה הורדה של {len(combined_df.columns)//2} מניות")
        print(f"תקופה: {combined_df.index.min()} עד {combined_df.index.max()}")
        print(f"מספר ימים: {len(combined_df)}")
        
        return combined_df
    
    def update_daily(self, symbols: List[str]) -> pd.DataFrame:
        """
        עדכון יומי - מוריד רק את הנתונים החדשים
        """
        # מצא את התאריך האחרון בקאש
        latest_date = None
        
        for symbol in symbols[:5]:  # בדוק 5 מניות ראשונות
            cache_files = [f for f in os.listdir(self.cache_dir) if f.startswith(symbol)]
            if cache_files:
                latest_file = max(cache_files, key=lambda f: os.path.getmtime(
                    os.path.join(self.cache_dir, f)
                ))
                file_date = datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(self.cache_dir, latest_file))
                )
                if latest_date is None or file_date > latest_date:
                    latest_date = file_date
        
        if latest_date and latest_date.date() == datetime.now().date():
            print("הנתונים כבר עודכנו היום")
            return None
        
        # הורד נתונים חדשים
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"מעדכן נתונים מ-{yesterday} עד {today}")
        
        return self.download_multiple_stocks(
            symbols,
            start_date=yesterday,
            end_date=today,
            use_cache=False
        )
    
    def get_reference_stock_data(self,
                                symbol: str = "SPY",
                                start_date: str = "2012-01-01",
                                end_date: str = None) -> Dict[str, pd.Series]:
        """
        הורדת נתוני מניית ייחוס (ברירת מחדל: SPY - S&P 500 ETF)
        
        Returns:
            Dict עם 'price' ו-'volume'
        """
        df = self.download_stock_data(symbol, start_date, end_date)
        
        if df is None:
            return None
        
        return {
            'price': df['Close'],
            'volume': df['Volume']
        }
    
    def clear_cache(self):
        """
        ניקוי קאש
        """
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)
        print("קאש נוקה")


def test_fetcher():
    """
    בדיקה בסיסית של מודול ההורדה
    """
    fetcher = DataFetcher()
    
    # בדיקה עם מספר קטן של מניות
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META']
    
    print("=== בדיקת הורדת נתונים ===")
    data = fetcher.download_multiple_stocks(
        test_symbols,
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    
    print("\n=== מידע על הנתונים ===")
    print(f"צורה: {data.shape}")
    print(f"עמודות: {data.columns.tolist()[:10]}")
    print(f"\nדוגמה:")
    print(data.head())
    
    # בדיקת מניית ייחוס
    print("\n=== בדיקת מניית ייחוס ===")
    ref_data = fetcher.get_reference_stock_data("SPY", "2023-01-01", "2023-12-31")
    print(f"מחיר: {len(ref_data['price'])} ימים")
    print(f"נפח: {len(ref_data['volume'])} ימים")


if __name__ == '__main__':
    test_fetcher()

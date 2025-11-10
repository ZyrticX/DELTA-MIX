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
        # ניסיון 1: הורדה מוויקיפדיה עם requests
        try:
            import requests
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            
            # הוספת headers כדי להימנע מ-403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # ניסיון עם requests + pandas (עם timeout)
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                from io import StringIO
                tables = pd.read_html(StringIO(response.text))
                if tables and len(tables) > 0:
                    sp500_table = tables[0]
                    if 'Symbol' in sp500_table.columns:
                        symbols = sp500_table['Symbol'].tolist()
                        # ניקוי סימנים מיוחדים
                        symbols = [s.replace('.', '-') for s in symbols if pd.notna(s)]
                        if len(symbols) >= 400:  # בדיקה שיש לפחות 400 מניות
                            print(f"✅ נמצאו {len(symbols)} מניות ב-S&P 500 (מוויקיפדיה)")
                            return symbols
        except Exception as e:
            print(f"ניסיון 1 נכשל: {e}")
        
        # ניסיון 2: pandas.read_html ישירות
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url, header=0, timeout=10)
            if tables and len(tables) > 0:
                sp500_table = tables[0]
                if 'Symbol' in sp500_table.columns:
                    symbols = sp500_table['Symbol'].tolist()
                    symbols = [s.replace('.', '-') for s in symbols if pd.notna(s)]
                    if len(symbols) >= 400:
                        print(f"✅ נמצאו {len(symbols)} מניות ב-S&P 500 (מוויקיפדיה - שיטה 2)")
                        return symbols
        except Exception as e:
            print(f"ניסיון 2 נכשל: {e}")
        
        # ניסיון 3: רשימה מלאה של S&P 500 (גיבוי)
        print("⚠️ ההורדה מוויקיפדיה נכשלה, משתמש ברשימה מלאה של S&P 500")
        return self._get_full_sp500_symbols()
    
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
        רשימת ברירת מחדל של מניות (למקרה שההורדה נכשלת) - רשימה חלקית
        """
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM',
            'V', 'JNJ', 'WMT', 'PG', 'MA', 'HD', 'BAC', 'DIS', 'ADBE', 'NFLX',
            'CRM', 'CSCO', 'PEP', 'KO', 'INTC', 'AMD', 'PYPL', 'NKE', 'MRK',
            'TMO', 'ABBV', 'ABT', 'COST', 'ACN', 'AVGO', 'TXN', 'DHR', 'LLY',
            'UNP', 'NEE', 'PM', 'BMY', 'UPS', 'LOW', 'QCOM', 'HON', 'ORCL',
            'IBM', 'AMGN', 'GE', 'MDT', 'CAT', 'BA', 'MMM', 'GS', 'AXP'
        ]
    
    def _get_full_sp500_symbols(self) -> List[str]:
        """
        רשימה מלאה של כל מניות S&P 500 (גיבוי כשהורדה מוויקיפדיה נכשלת)
        רשימה מעודכנת ל-2025 - כל 503 מניות S&P 500
        """
        # רשימה מלאה של S&P 500 (מעודכנת 2025)
        # מבוססת על רשימה רשמית מעודכנת
        # רשימה מלאה של S&P 500 - מעודכנת לפי הרשימה החדשה
        # כל 503 מניות לפי הסדר מהרשימה המעודכנת
        all_symbols = [
            'NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'AVGO', 'GOOG', 'META', 'TSLA', 'BRK-B',
            'JPM', 'LLY', 'WMT', 'ORCL', 'V', 'MA', 'XOM', 'NFLX', 'JNJ', 'PLTR',
            'COST', 'BAC', 'ABBV', 'AMD', 'HD', 'PG', 'GE', 'CVX', 'KO', 'IBM',
            'UNH', 'CSCO', 'WFC', 'CAT', 'MU', 'MS', 'AXP', 'GS', 'PM', 'RTX',
            'CRM', 'TMUS', 'ABT', 'MCD', 'MRK', 'TMO', 'APP', 'LRCX', 'DIS', 'LIN',
            'PEP', 'ISRG', 'UBER', 'QCOM', 'AMAT', 'INTU', 'C', 'INTC', 'NOW', 'T',
            'SCHW', 'NEE', 'AMGN', 'VZ', 'APH', 'ANET', 'BLK', 'TJX', 'BKNG', 'KLAC',
            'GILD', 'ACN', 'BA', 'DHR', 'SPGI', 'GEV', 'BSX', 'TXN', 'ETN', 'PANW',
            'PFE', 'COF', 'ADBE', 'SYK', 'CRWD', 'LOW', 'UNP', 'WELL', 'DE', 'HON',
            'PGR', 'PLD', 'MDT', 'ADI', 'BX', 'HOOD', 'CB', 'KKR', 'LMT', 'HCA',
            'COP', 'VRTX', 'MCK', 'PH', 'CEG', 'ADP', 'SO', 'CMCSA', 'CVS', 'DELL',
            'CME', 'TT', 'MO', 'DUK', 'BMY', 'SBUX', 'GD', 'NKE', 'NEM', 'CDNS',
            'MMM', 'MMC', 'MCO', 'ICE', 'DASH', 'AMT', 'SHW', 'HWM', 'NOC', 'WM',
            'EQIX', 'ORLY', 'JCI', 'UPS', 'COIN', 'ABNB', 'MAR', 'BK', 'APO', 'CTAS',
            'GLW', 'EMR', 'MDLZ', 'SNPS', 'AON', 'USB', 'ECL', 'TDG', 'PNC', 'WMB',
            'TEL', 'ITW', 'COR', 'ELV', 'CI', 'RCL', 'REGN', 'MNST', 'DDOG', 'CSX',
            'PWR', 'MSI', 'AEP', 'GM', 'CMI', 'RSG', 'AJG', 'NSC', 'CL', 'ADSK',
            'TRV', 'HLT', 'PYPL', 'VST', 'FDX', 'SRE', 'FTNT', 'AZO', 'AFL', 'WDAY',
            'SPG', 'KMI', 'STX', 'EOG', 'DLR', 'APD', 'FCX', 'IDXX', 'MPC', 'TFC',
            'WBD', 'PSX', 'WDC', 'SLB', 'VLO', 'LHX', 'URI', 'ZTS', 'ROST', 'ALL',
            'PCAR', 'O', 'D', 'NXPI', 'F', 'BDX', 'MET', 'EA', 'NDAQ', 'AIG',
            'EW', 'PSA', 'XEL', 'ROP', 'CARR', 'BKR', 'FAST', 'CAH', 'AXON', 'EXC',
            'GWW', 'MPWR', 'AME', 'TTWO', 'CBRE', 'MSCI', 'ETR', 'OKE', 'CTVA', 'DHI',
            'LVS', 'AMP', 'KR', 'ROK', 'PEG', 'YUM', 'A', 'TGT', 'FANG', 'PAYX',
            'CMG', 'FICO', 'OXY', 'GRMN', 'CPRT', 'CCI', 'VMC', 'XYZ', 'DAL', 'PRU',
            'XYL', 'EBAY', 'TRGP', 'MLM', 'RMD', 'KDP', 'WEC', 'PCG', 'IQV', 'HIG',
            'ED', 'OTIS', 'VTR', 'SYY', 'CTSH', 'WAB', 'EQT', 'CCL', 'HSY', 'GEHC',
            'NUE', 'KMB', 'FIS', 'FI', 'STT', 'ACGL', 'NRG', 'KEYS', 'VICI', 'RJF',
            'LYV', 'EL', 'KVUE', 'MTD', 'EXPE', 'WTW', 'IBKR', 'IR', 'LEN', 'HPE',
            'UAL', 'MCHP', 'HUM', 'VRSK', 'IRM', 'EME', 'K', 'ODFL', 'CSGP', 'FSLR',
            'TER', 'CHTR', 'ROL', 'KHC', 'ATO', 'FITB', 'MTB', 'WRB', 'DTE', 'TSCO',
            'EXR', 'AEE', 'ADM', 'PPL', 'ES', 'SYF', 'CBOE', 'EXE', 'FE', 'BRO',
            'STE', 'CNP', 'AWK', 'BR', 'CINF', 'EFX', 'AVB', 'GIS', 'DOV', 'VLTO',
            'LDOS', 'HPQ', 'NTRS', 'HUBB', 'HBAN', 'TDY', 'SMCI', 'TPL', 'WSM', 'PHM',
            'HAL', 'BIIB', 'ULTA', 'JBL', 'TTD', 'PODD', 'DXCM', 'NTAP', 'STZ', 'EQR',
            'STLD', 'TROW', 'VRSN', 'WAT', 'CMS', 'CFG', 'EIX', 'PPG', 'RF', 'DG',
            'L', 'PTC', 'LH', 'SBAC', 'DLTR', 'CHD', 'DVN', 'DRI', 'INCY', 'TPR',
            'CTRA', 'NI', 'TYL', 'NVR', 'ON', 'WST', 'DGX', 'Q', 'CPAY', 'LULU',
            'RL', 'AMCR', 'KEY', 'IP', 'BG', 'TRMB', 'TSN', 'CDW', 'SW', 'J',
            'PFG', 'CNC', 'EXPD', 'GPN', 'GDDY', 'SNA', 'PKG', 'APTV', 'ZBH', 'CHRW',
            'PNR', 'GPC', 'MKC', 'LII', 'EVRG', 'LNT', 'INVH', 'BBY', 'HOLX', 'ESS',
            'WY', 'PSKY', 'DD', 'IT', 'FTV', 'LUV', 'IFF', 'JBHT', 'GEN', 'DOW',
            'MAA', 'TKO', 'ERIE', 'TXT', 'UHS', 'FFIV', 'ALLE', 'OMC', 'FOX', 'FOXA',
            'KIM', 'LYB', 'EG', 'DPZ', 'COO', 'AVY', 'CF', 'BALL', 'CLX', 'NDSN',
            'ZBRA', 'MAS', 'WYNN', 'BF-B', 'REG', 'IEX', 'BEN', 'DOC', 'HII', 'HRL',
            'HST', 'BLDR', 'JKHY', 'VTRS', 'DECK', 'SOLV', 'SJM', 'UDR', 'AKAM', 'BXP',
            'DAY', 'AIZ', 'HAS', 'ALB', 'GL', 'CPT', 'PNW', 'SWKS', 'SWK', 'IVZ',
            'RVTY', 'AES', 'ALGN', 'FDS', 'NWSA', 'MRNA', 'EPAM', 'PAYC', 'BAX', 'POOL',
            'ARE', 'IPG', 'AOS', 'TECH', 'CPB', 'GNRC', 'TAP', 'MGM', 'LW', 'DVA',
            'APA', 'CRL', 'NCLH', 'FRT', 'HSIC', 'CAG', 'MOS', 'MTCH', 'LKQ', 'MOH',
            'SOLS', 'MHK', 'NWS'
        ]
        
        # ניקוי כפילויות ושמירה על סדר
        seen = set()
        unique_symbols = []
        for symbol in all_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        # ניקוי סימנים מיוחדים
        cleaned_symbols = [s.replace('.', '-') for s in unique_symbols if s]
        
        print(f"✅ רשימה מלאה של S&P 500: {len(cleaned_symbols)} מניות")
        return cleaned_symbols
    
    def download_stock_data(self, 
                          symbol: str,
                          start_date: str = "2012-01-01",
                          end_date: str = None,
                          use_cache: bool = True,
                          force_download: bool = False) -> pd.DataFrame:
        """
        הורדת נתוני מניה בודדת
        
        Args:
            symbol: סימול המניה
            start_date: תאריך התחלה (ברירת מחדל: 2012-01-01)
            end_date: תאריך סיום (ברירת מחדל: היום)
            use_cache: האם להשתמש בקאש
            force_download: האם לכפות הורדה מחדש (True = הורד בכל מקרה, False = השתמש בקאש אם קיים)
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_file = os.path.join(self.cache_dir, f"{symbol}_{start_date}_{end_date}.pkl")
        
        # בדוק קאש - אם לא כפינו הורדה ויש קאש, תמיד השתמש בו
        if use_cache and not force_download and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    df = pickle.load(f)
                print(f"✅ {symbol}: נטען מקאש")
                return df
            except Exception as e:
                print(f"⚠️ {symbol}: שגיאה בטעינה מקאש ({e}), מוריד מחדש...")
                # אם נכשל, נוריד מחדש
        
        # הורדה מ-Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                # בדיקה אם המניה הוסרה מהמסחר
                info = ticker.info
                if 'longName' not in info or info.get('quoteType') == 'DELISTED':
                    print(f"⚠️ {symbol}: מניה הוסרה מהמסחר (delisted)")
                else:
                    print(f"⚠️ {symbol}: אין נתונים זמינים")
                return None
            
            # בדיקה שיש לפחות כמה שורות נתונים
            if len(df) < 10:
                print(f"⚠️ {symbol}: נתונים מועטים מדי ({len(df)} ימים)")
                return None
            
            # שמירה בקאש
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            
            return df
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'delisted' in error_msg or 'no timezone' in error_msg or 'no price data' in error_msg:
                print(f"⚠️ {symbol}: מניה הוסרה מהמסחר או אין נתונים")
            else:
                print(f"⚠️ שגיאה בהורדת {symbol}: {e}")
            return None
    
    def download_multiple_stocks(self,
                                symbols: List[str],
                                start_date: str = "2012-01-01",
                                end_date: str = None,
                                use_cache: bool = True,
                                force_download: bool = False,
                                max_workers: int = 10) -> pd.DataFrame:
        """
        הורדת נתונים של מספר מניות
        
        מוריד מ-Yahoo Finance את כל הנתונים, אבל שומר רק:
        - Close: מחיר סגירה
        - Adj Close: מחיר סגירה מותאם (מותאם לפיצולי מניות ודיבידנדים)
        - Volume: נפח מסחר
        
        Args:
            force_download: אם True, יוריד מחדש גם אם יש קאש. אם False, ישתמש בקאש אם קיים.
        
        Returns:
            DataFrame עם MultiIndex: (symbol, field) - Close, Adj Close ו-Volume
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"מוריד נתונים עבור {len(symbols)} מניות...")
        print(f"תקופה: {start_date} עד {end_date}")
        if use_cache and not force_download:
            print("💾 משתמש בקאש - לא יוריד נתונים שכבר קיימים")
        elif force_download:
            print("🔄 כופה הורדה מחדש - מתעלם מקאש")
        
        all_data = {}
        failed_symbols = []
        
        for i, symbol in enumerate(symbols):
            if (i + 1) % 50 == 0:
                print(f"התקדמות: {i+1}/{len(symbols)}")
            
            df = self.download_stock_data(symbol, start_date, end_date, use_cache, force_download)
            
            if df is not None and not df.empty:
                # בדוק אילו עמודות זמינות
                available_columns = df.columns.tolist()
                
                # נרמול שמות עמודות (הסרת רווחים מיותרים, המרה ל-lowercase לבדיקה)
                normalized_columns = {col.strip(): col for col in available_columns}
                normalized_lower = {col.strip().lower(): col for col in available_columns}
                
                # מיפוי שמות עמודות אפשריים (yfinance יכול להחזיר שמות שונים)
                column_mapping = {
                    'Close': ['Close', 'close', 'CLOSE'],
                    'Adj Close': ['Adj Close', 'AdjClose', 'Adj_Close', 'adj close', 'ADJ CLOSE', 'AdjClose'],
                    'Volume': ['Volume', 'volume', 'VOLUME', 'vol']
                }
                
                # פונקציה עזר למציאת עמודה
                def find_column(possible_names):
                    # נסה מציאת מדויקת
                    for col_name in possible_names:
                        if col_name in available_columns:
                            return col_name
                        # נסה עם נרמול
                        if col_name.strip() in normalized_columns:
                            return normalized_columns[col_name.strip()]
                        # נסה case-insensitive
                        if col_name.strip().lower() in normalized_lower:
                            return normalized_lower[col_name.strip().lower()]
                    return None
                
                # בדיקה ראשונית - אם אין Close, המניה לא תקינה
                close_col = find_column(column_mapping['Close'])
                close_found = close_col is not None
                
                if not close_found:
                    print(f"⚠️ {symbol}: אין עמודת 'Close' - מדלג על מניה זו")
                    print(f"   עמודות זמינות: {available_columns}")
                    failed_symbols.append(symbol)
                    continue
                
                # דיבוג: הדפס עמודות עבור מניות ראשונות (למקרה של בעיות)
                if i < 3 and len(failed_symbols) == 0:
                    print(f"   {symbol}: עמודות זמינות: {available_columns}")
                
                # שמור רק את השדות הנדרשים לניתוח:
                # - Close: מחיר סגירה (לחישוב קורלציות מחיר)
                # - Adj Close: מחיר סגירה מותאם (מותאם לפיצולי מניות ודיבידנדים)
                # - Volume: נפח מסחר (לחישוב קורלציות נפח)
                for field, possible_names in column_mapping.items():
                    found_column = find_column(possible_names)
                    
                    if found_column:
                        all_data[(symbol, field)] = df[found_column]
                    else:
                        # אם לא נמצאה העמודה, נדפיס אזהרה ונשתמש בעמודה חלופית
                        if field == 'Adj Close':
                            # אם אין Adj Close, נשתמש ב-Close
                            if close_col:
                                if i < 5:  # הדפס רק עבור 5 מניות ראשונות כדי לא להציף
                                    print(f"⚠️ {symbol}: אין עמודת 'Adj Close', משתמש ב-'Close'")
                                all_data[(symbol, field)] = df[close_col]
                            else:
                                # זה לא אמור לקרות כי בדקנו קודם
                                failed_symbols.append(symbol)
                                break
                        elif field == 'Volume':
                            # Volume הוא אופציונלי יותר, נשתמש ב-0 אם אין
                            if i < 5:  # הדפס רק עבור 5 מניות ראשונות
                                print(f"⚠️ {symbol}: אין עמודת 'Volume', משתמש ב-0")
                            all_data[(symbol, field)] = pd.Series(0, index=df.index)
            else:
                failed_symbols.append(symbol)
            
            # השהייה קלה כדי לא להעמיס על השרת
            if not use_cache:
                time.sleep(0.1)
        
        if failed_symbols:
            print(f"\n⚠️ נכשלו {len(failed_symbols)} מניות (הוסרו מהמסחר או אין נתונים)")
            if len(failed_symbols) <= 20:
                print(f"   מניות שנכשלו: {', '.join(failed_symbols)}")
            else:
                print(f"   מניות שנכשלו (20 ראשונות): {', '.join(failed_symbols[:20])}")
        
        # יצירת DataFrame אחד גדול
        combined_df = pd.DataFrame(all_data)
        
        if combined_df.empty:
            print("\n❌ לא הורדו נתונים עבור אף מניה")
            return None
        
        successful_count = len(combined_df.columns) // 3  # Close, Adj Close, Volume
        print(f"\n✅ הושלמה הורדה של {successful_count} מניות מתוך {len(symbols)}")
        print(f"   תקופה: {combined_df.index.min()} עד {combined_df.index.max()}")
        print(f"   מספר ימים: {len(combined_df)}")
        
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

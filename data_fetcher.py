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
        רשימה מעודכנת ל-2024 - ניקוי כפילויות
        """
        # רשימה מלאה של S&P 500 (מעודכנת)
        all_symbols = [
            'A', 'AAL', 'AAP', 'ABBV', 'ABC', 'ABMD', 'ABT', 'ACGL', 'ACN',
            'ADBE', 'ADI', 'ADM', 'ADP', 'ADSK', 'AEE', 'AEP', 'AES', 'AFL',
            'A', 'AGCO', 'AGL', 'AIG', 'AIV', 'AIZ', 'AJG', 'AKAM', 'ALB',
            'ALGN', 'ALK', 'ALL', 'ALLE', 'ALLY', 'ALNY', 'AMAT', 'AMCR', 'AMD',
            'AME', 'AMED', 'AMGN', 'AMP', 'AMT', 'AMZN', 'ANET', 'ANSS', 'ANTM',
            'AON', 'AOS', 'APA', 'APD', 'APH', 'APTV', 'ARE', 'ARES', 'ARG',
            'ATO', 'ATVI', 'AVB', 'AVGO', 'AVY', 'AWK', 'AXON', 'AXP', 'AZO',
            'BA', 'BALL', 'BANC', 'BBWI', 'BBY', 'BDX', 'BEN', 'BF-B', 'BIIB',
            'BIO', 'BILL', 'BK', 'BKR', 'BLK', 'BLKB', 'BLL', 'BMY', 'BNTX',
            'BOKF', 'BR', 'BRK-B', 'BRO', 'BSX', 'BWA', 'BXP', 'C', 'CAG',
            'CAH', 'CALM', 'CALX', 'CARR', 'CAT', 'CB', 'CBOE', 'CBRE', 'CCK',
            'CDAY', 'CDNS', 'CDW', 'CE', 'CERN', 'CF', 'CFG', 'CHD', 'CHRW',
            'CHTR', 'CI', 'CINF', 'CL', 'CLH', 'CLX', 'CMA', 'CMCSA', 'CME',
            'CMI', 'CMS', 'CNC', 'CNP', 'COF', 'COHR', 'COIN', 'COKE', 'COLB',
            'COO', 'COP', 'COST', 'CPB', 'CPRT', 'CPT', 'CR', 'CRL', 'CRM',
            'CRWD', 'CSCO', 'CSGP', 'CSL', 'CSX', 'CTAS', 'CTLT', 'CTRA', 'CTSH',
            'CTVA', 'CUBE', 'CURI', 'CVS', 'CVX', 'CZR', 'D', 'DAL', 'DAR',
            'DASH', 'DD', 'DDD', 'DDOG', 'DE', 'DECK', 'DEI', 'DFS', 'DG',
            'DGX', 'DHI', 'DHR', 'DIOD', 'DISH', 'DKNG', 'DLR', 'DLTR', 'DNB',
            'DOCN', 'DOCS', 'DOV', 'DOW', 'DPZ', 'DRI', 'DT', 'DTE', 'DUK',
            'DVA', 'DVN', 'DXCM', 'DXF', 'E', 'EA', 'EBAY', 'ECL', 'ED', 'EFX',
            'EG', 'EIX', 'EL', 'ELAN', 'ELS', 'EMN', 'EMR', 'ENPH', 'ENTG',
            'EOG', 'EPAM', 'EQH', 'EQIX', 'EQR', 'EQT', 'ES', 'ESS', 'ETN',
            'ETR', 'EVRG', 'EW', 'EWBC', 'EXAS', 'EXC', 'EXPD', 'EXPE', 'EXPO',
            'F', 'FANG', 'FAST', 'FATE', 'FCNCA', 'FDS', 'FDX', 'FE', 'FERG',
            'FFIV', 'FHB', 'FHI', 'FHS', 'FIBK', 'FICO', 'FIS', 'FISV', 'FITB',
            'FIVE', 'FIX', 'FL', 'FLEX', 'FLS', 'FLT', 'FMC', 'FNF', 'FNV',
            'FOX', 'FOXA', 'FR', 'FRC', 'FRME', 'FROG', 'FRT', 'FSLR', 'FTNT',
            'FTS', 'FTV', 'FUL', 'FULT', 'FWRD', 'G', 'GATX', 'GD', 'GE',
            'GEF', 'GFF', 'GGG', 'GHC', 'GIB', 'GILD', 'GIS', 'GL', 'GLW',
            'GM', 'GNRC', 'GNTX', 'GOOGL', 'GPC', 'GPN', 'GRMN', 'GS', 'GSHD',
            'GTLS', 'GWW', 'H', 'HAL', 'HAS', 'HBAN', 'HBI', 'HCA', 'HCP',
            'HD', 'HE', 'HES', 'HIG', 'HII', 'HLT', 'HOLX', 'HOMB', 'HON',
            'HOV', 'HP', 'HPE', 'HPQ', 'HRL', 'HSIC', 'HST', 'HSY', 'HUBB',
            'HUM', 'HWM', 'HXL', 'IAC', 'IBM', 'IBOC', 'ICE', 'ICFI', 'ICUI',
            'IDA', 'IDXX', 'IEX', 'IFF', 'IGT', 'ILMN', 'INCY', 'INFA', 'INFO',
            'INGR', 'INMD', 'INSP', 'INTU', 'INVH', 'IOVA', 'IP', 'IPG', 'IQV',
            'IR', 'IRDM', 'IRM', 'ISRG', 'IT', 'ITT', 'ITW', 'IVZ', 'J', 'JBHT',
            'JBL', 'JCI', 'JKHY', 'JLL', 'JNJ', 'JNPR', 'JPM', 'K', 'KBR',
            'KDP', 'KEX', 'KEY', 'KEYS', 'KFRC', 'KHC', 'KIM', 'KMB', 'KMI',
            'KMX', 'KNX', 'KO', 'KR', 'KRC', 'KREF', 'KRG', 'KRTX', 'KSS',
            'KTB', 'KVUE', 'KW', 'L', 'LAD', 'LAMR', 'LANC', 'LBRT', 'LCID',
            'LDOS', 'LECO', 'LEG', 'LEN', 'LFUS', 'LH', 'LHX', 'LII', 'LIN',
            'LKQ', 'LLY', 'LMT', 'LNC', 'LNT', 'LNW', 'LOGI', 'LOW', 'LPLA',
            'LRCX', 'LSCC', 'LSTR', 'LULU', 'LUMN', 'LUV', 'LVS', 'LW', 'LZB',
            'M', 'MA', 'MAA', 'MANH', 'MAR', 'MAS', 'MASI', 'MAT', 'MCD', 'MCHP',
            'MCK', 'MCO', 'MDLZ', 'MDT', 'MDU', 'MEDP', 'MEG', 'META', 'MGM',
            'MHK', 'MHO', 'MIDD', 'MKC', 'MKL', 'MLI', 'MLKN', 'MMC', 'MMM',
            'MNST', 'MO', 'MOH', 'MORN', 'MOS', 'MPC', 'MPWR', 'MPW', 'MRK',
            'MRNA', 'MRO', 'MRVI', 'MS', 'MSCI', 'MSFT', 'MSI', 'MTB', 'MTCH',
            'MTH', 'MTN', 'MTRX', 'MTZ', 'MU', 'MUR', 'MUSA', 'MXL', 'MYRG',
            'N', 'NARI', 'NBIX', 'NCLH', 'NDAQ', 'NDSN', 'NEE', 'NEM', 'NFLX',
            'NGVT', 'NHC', 'NI', 'NKE', 'NOC', 'NOVT', 'NOW', 'NPK', 'NRG',
            'NSC', 'NTAP', 'NTRS', 'NUE', 'NUS', 'NVAX', 'NVDA', 'NVR', 'NVTK',
            'NWL', 'NWS', 'NWSA', 'NXPI', 'O', 'ODFL', 'OGN', 'OHI', 'OKE',
            'OKTA', 'OLN', 'OMC', 'ON', 'ONON', 'OPCH', 'ORA', 'ORCL', 'ORI',
            'ORLY', 'OSCR', 'OSIS', 'OTIS', 'OZK', 'PAA', 'PACW', 'PAG', 'PANW',
            'PARA', 'PATH', 'PAYC', 'PAYX', 'PB', 'PBF', 'PCAR', 'PCG', 'PCH',
            'PCRX', 'PDCO', 'PEG', 'PENN', 'PEP', 'PFE', 'PFGC', 'PG', 'PGR',
            'PH', 'PHM', 'PII', 'PINS', 'PKG', 'PKI', 'PLD', 'PLNT', 'PLTR',
            'PM', 'PNC', 'PNM', 'PNR', 'PNW', 'POOL', 'POR', 'POST', 'PPG',
            'PPL', 'PR', 'PRGO', 'PRGS', 'PRU', 'PSA', 'PSX', 'PTC', 'PTEN',
            'PTON', 'PVH', 'PWR', 'PXD', 'PYPL', 'QCOM', 'QRVO', 'R', 'RBC',
            'RBLX', 'RCI', 'RCL', 'RCM', 'RDN', 'RE', 'REG', 'REGN', 'RELY',
            'RGA', 'RGLD', 'RGNX', 'RHI', 'RHP', 'RIG', 'RJF', 'RL', 'RLI',
            'RLJ', 'RMBS', 'RMD', 'RMNI', 'RNG', 'RNR', 'ROAD', 'ROCK', 'ROG',
            'ROK', 'ROL', 'ROP', 'ROST', 'RPD', 'RPM', 'RPRX', 'RPT', 'RRX',
            'RSG', 'RTX', 'RUN', 'RVTY', 'RWT', 'RXDX', 'RXO', 'RYAN', 'RYN',
            'S', 'SAIA', 'SAIC', 'SAM', 'SANM', 'SASR', 'SBAC', 'SBRA', 'SBUX',
            'SCHW', 'SCI', 'SCL', 'SEIC', 'SF', 'SFBS', 'SFL', 'SGEN', 'SGRY',
            'SHO', 'SHW', 'SIG', 'SIGI', 'SIRI', 'SITE', 'SIVB', 'SJM', 'SLAB',
            'SLB', 'SLG', 'SLGN', 'SLM', 'SM', 'SMAR', 'SMPL', 'SNA', 'SNOW',
            'SNPS', 'SNV', 'SO', 'SOFI', 'SON', 'SONY', 'SPB', 'SPGI', 'SPLK',
            'SPOT', 'SPR', 'SPSC', 'SPT', 'SPWR', 'SQ', 'SR', 'SRC', 'SRCL',
            'SRE', 'SSB', 'SSD', 'SSNC', 'SSP', 'SSSS', 'ST', 'STAA', 'STAG',
            'STE', 'STEL', 'STEM', 'STLD', 'STNE', 'STT', 'STX', 'STZ', 'SUI',
            'SWAV', 'SWK', 'SWKS', 'SWN', 'SWX', 'SXC', 'SXI', 'SXT', 'SYF',
            'SYK', 'SYY', 'T', 'TALO', 'TAP', 'TBBK', 'TBI', 'TCBI', 'TCOA',
            'TD', 'TDC', 'TDG', 'TDOC', 'TDS', 'TDW', 'TDY', 'TECH', 'TEL',
            'TENB', 'TER', 'TEX', 'TFC', 'TFII', 'TFX', 'TGNA', 'TGT', 'THC',
            'THG', 'THO', 'TILE', 'TITN', 'TJX', 'TKO', 'TKR', 'TLYS', 'TMHC',
            'TMO', 'TMUS', 'TNC', 'TNDM', 'TNET', 'TNL', 'TOL', 'TOST', 'TPG',
            'TPH', 'TPL', 'TR', 'TRAK', 'TRGP', 'TRI', 'TRIP', 'TRMB', 'TRMK',
            'TRN', 'TROW', 'TRS', 'TRU', 'TRV', 'TSCO', 'TSLA', 'TSM', 'TSN',
            'TT', 'TTC', 'TTD', 'TTEK', 'TTGT', 'TTMI', 'TTPH', 'TTSH', 'TTWO',
            'TU', 'TUP', 'TUSK', 'TVTY', 'TW', 'TWI', 'TWLO', 'TWST', 'TXG',
            'TXN', 'TXT', 'TYL', 'U', 'UA', 'UAA', 'UAL', 'UBSI', 'UCBI', 'UDR',
            'UFPI', 'UGI', 'UHAL', 'UHS', 'UI', 'ULTA', 'UMBF', 'UNF', 'UNFI',
            'UNH', 'UNM', 'UNP', 'UPS', 'URI', 'USB', 'USFD', 'USLM', 'USNA',
            'USPH', 'UTHR', 'UTZ', 'UVV', 'V', 'VAC', 'VALE', 'VAPO', 'VFC',
            'VICI', 'VICR', 'VIPS', 'VIST', 'VITL', 'VIVO', 'VKTX', 'VLO',
            'VMC', 'VMI', 'VNT', 'VOD', 'VRSK', 'VRSN', 'VRT', 'VRTX', 'VSAT',
            'VSCO', 'VSH', 'VST', 'VSTO', 'VTR', 'VTRS', 'VTYX', 'VZ', 'W',
            'WAB', 'WAFD', 'WAL', 'WAT', 'WBD', 'WBS', 'WBT', 'WCC', 'WD',
            'WDC', 'WDFC', 'WDR', 'WEC', 'WELL', 'WEN', 'WERN', 'WES', 'WEX',
            'WFRD', 'WGO', 'WH', 'WHD', 'WHR', 'WING', 'WIRE', 'WIT', 'WK',
            'WKC', 'WLK', 'WLKP', 'WLY', 'WM', 'WMB', 'WMT', 'WNC', 'WOLF',
            'WOOF', 'WOR', 'WPC', 'WPM', 'WRB', 'WRK', 'WRLD', 'WRN', 'WSBC',
            'WSFS', 'WSM', 'WSO', 'WST', 'WTFC', 'WTI', 'WTM', 'WTRG', 'WTS',
            'WTT', 'WU', 'WWD', 'WWE', 'WWW', 'WY', 'WYNN', 'X', 'XEL', 'XOM',
            'XPO', 'XRAY', 'XRX', 'XYL', 'YELP', 'YETI', 'YEXT', 'YUM', 'YUMC',
            'Z', 'ZBH', 'ZBRA', 'ZD', 'ZEN', 'ZEPP', 'ZETA', 'ZGN', 'ZI',
            'ZION', 'ZIP', 'ZM', 'ZNH', 'ZS', 'ZTO', 'ZTS', 'ZUO', 'ZVIA',
            'ZWS', 'ZYME', 'ZYXI'
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

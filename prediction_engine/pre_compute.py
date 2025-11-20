"""
Pre-Computation Engine - חישוב כל הקורלציות ההיסטוריות + תוצאות עתידיות
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pickle
import logging
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import time

# הוספת נתיב למודולים
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher import DataFetcher
from correlation_engine import CorrelationEngine
from .config import COMPUTATION_PARAMS, MULTIPROCESSING_CONFIG, PATHS
from .db_client import SupabaseClient
from .utils import (
    classify_movement,
    calculate_correlation_for_date,
    calculate_future_return,
    create_pattern_signature
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PreComputeEngine:
    """
    מנוע Pre-Computation לחישוב כל הקורלציות ההיסטוריות
    """
    
    def __init__(self):
        """אתחול"""
        self.data_fetcher = DataFetcher(cache_dir=PATHS['data_cache'])
        self.db_client = SupabaseClient()
        self.params = COMPUTATION_PARAMS
        
    def load_stock_data(self, symbols: List[str], start_date: str = "2012-01-01") -> pd.DataFrame:
        """
        טעינת נתוני מניות מ-cache
        
        Args:
            symbols: רשימת סימולים
            start_date: תאריך התחלה
            
        Returns:
            DataFrame עם MultiIndex (symbol, field)
        """
        logger.info(f"📂 טוען נתונים עבור {len(symbols)} מניות...")
        
        all_data = {}
        failed = []
        
        for symbol in tqdm(symbols, desc="טעינת נתונים"):
            cache_file = os.path.join(PATHS['data_cache'], f"{symbol}_{start_date}_None.pkl")
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'rb') as f:
                        df = pickle.load(f)
                    
                    if df is not None and not df.empty:
                        # שמירת רק שדות רלוונטיים
                        for field in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
                            if field in df.columns:
                                all_data[(symbol, field)] = df[field]
                except Exception as e:
                    logger.warning(f"⚠️ שגיאה בטעינת {symbol}: {e}")
                    failed.append(symbol)
            else:
                failed.append(symbol)
        
        if failed:
            logger.warning(f"⚠️ {len(failed)} מניות לא נטענו: {failed[:10]}...")
        
        if not all_data:
            raise ValueError("לא נמצאו נתונים!")
        
        # יצירת DataFrame
        stock_data = pd.DataFrame(all_data)
        stock_data.index = pd.to_datetime(stock_data.index)
        stock_data = stock_data.sort_index()
        
        logger.info(f"✅ נטענו נתונים עבור {len(symbols) - len(failed)} מניות")
        logger.info(f"📅 טווח תאריכים: {stock_data.index[0]} עד {stock_data.index[-1]}")
        
        return stock_data
    
    def compute_snapshots_for_stock(self, 
                                    stock_data: pd.DataFrame,
                                    stock: str,
                                    dates: List[datetime],
                                    all_symbols: List[str],
                                    lookback_days: int,
                                    forward_days: int,
                                    correlation_threshold: float) -> List[Dict[str, Any]]:
        """
        חישוב snapshots למניה אחת
        
        Args:
            stock_data: DataFrame עם כל הנתונים
            stock: סימול המניה
            dates: רשימת תאריכים לחישוב
            all_symbols: רשימת כל הסימולים
            lookback_days: ימים אחורה
            forward_days: ימים קדימה
            correlation_threshold: סף קורלציה
            
        Returns:
            רשימת snapshots
        """
        snapshots = []
        
        for date in dates:
            try:
                # חישוב קורלציות עם כל המניות האחרות
                matched_stocks = []
                
                for other_stock in all_symbols:
                    if other_stock == stock:
                        continue
                    
                    # קורלציית מחיר
                    corr_price = calculate_correlation_for_date(
                        stock_data, stock, other_stock, date,
                        lookback_days, 'Adj Close'
                    )
                    
                    # קורלציית נפח
                    corr_volume = calculate_correlation_for_date(
                        stock_data, stock, other_stock, date,
                        lookback_days, 'Volume'
                    )
                    
                    # בדיקה אם עובר את הסף
                    if corr_price and corr_price >= correlation_threshold:
                        matched_stocks.append({
                            'symbol': other_stock,
                            'corr_price': corr_price,
                            'corr_volume': corr_volume or 0.0
                        })
                    elif corr_volume and corr_volume >= correlation_threshold:
                        matched_stocks.append({
                            'symbol': other_stock,
                            'corr_price': corr_price or 0.0,
                            'corr_volume': corr_volume
                        })
                
                # חישוב תנועה עתידית
                future_return = calculate_future_return(
                    stock_data, stock, date, forward_days, 'Adj Close'
                )
                
                movement_type = None
                if future_return is not None:
                    movement_type = classify_movement(
                        future_return,
                        self.params['movement_thresholds']
                    )
                
                # יצירת snapshot
                snapshot = {
                    'snapshot_date': date.strftime('%Y-%m-%d'),
                    'stock_symbol': stock,
                    'matched_stocks': matched_stocks,
                    'num_matches': len(matched_stocks),
                    'future_return_pct': future_return,
                    'movement_type': movement_type,
                    'lookback_days': lookback_days,
                    'forward_days': forward_days,
                    'correlation_threshold': correlation_threshold
                }
                
                snapshots.append(snapshot)
                
            except Exception as e:
                logger.warning(f"⚠️ שגיאה בחישוב snapshot עבור {stock} ב-{date}: {e}")
                continue
        
        return snapshots
    
    def compute_all_snapshots(self,
                            stock_data: pd.DataFrame,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            lookback_days: Optional[int] = None,
                            forward_days: Optional[int] = None,
                            correlation_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        חישוב כל ה-snapshots
        
        Args:
            stock_data: DataFrame עם כל הנתונים
            start_date: תאריך התחלה (ברירת מחדל: יום 16)
            end_date: תאריך סיום (ברירת מחדל: היום)
            lookback_days: ימים אחורה
            forward_days: ימים קדימה
            correlation_threshold: סף קורלציה
            
        Returns:
            רשימת כל ה-snapshots
        """
        # פרמטרים
        lookback_days = lookback_days or self.params['lookback_days']
        forward_days = forward_days or self.params['forward_days']
        correlation_threshold = correlation_threshold or self.params['correlation_threshold']
        
        # תאריכים
        all_dates = stock_data.index.tolist()
        
        if start_date:
            start_date = pd.to_datetime(start_date)
        else:
            # יום 16 (צריך lookback_days נתונים)
            start_date = all_dates[lookback_days - 1] if len(all_dates) > lookback_days else all_dates[0]
        
        if end_date:
            end_date = pd.to_datetime(end_date)
        else:
            end_date = all_dates[-1]
        
        # סינון תאריכים
        dates = [d for d in all_dates if start_date <= d <= end_date]
        
        # צריך לפחות forward_days אחרי התאריך האחרון
        if len(all_dates) > 0:
            last_available_date = all_dates[-1]
            max_date = last_available_date - timedelta(days=forward_days)
            dates = [d for d in dates if d <= max_date]
        
        logger.info(f"📅 מחשב snapshots עבור {len(dates)} תאריכים")
        logger.info(f"   מ-{dates[0]} עד {dates[-1]}")
        
        # מניות
        symbols = stock_data.columns.get_level_values(0).unique().tolist()
        logger.info(f"📊 מחשב עבור {len(symbols)} מניות")
        
        # חישוב
        all_snapshots = []
        
        # Multiprocessing
        max_workers = MULTIPROCESSING_CONFIG['max_workers']
        chunk_size = MULTIPROCESSING_CONFIG['chunk_size']
        
        # חלוקה ל-chunks
        stock_chunks = [symbols[i:i + chunk_size] for i in range(0, len(symbols), chunk_size)]
        
        logger.info(f"⚙️ משתמש ב-{max_workers} workers, {len(stock_chunks)} chunks")
        
        for chunk_idx, stock_chunk in enumerate(stock_chunks):
            logger.info(f"📦 מעבד chunk {chunk_idx + 1}/{len(stock_chunks)} ({len(stock_chunk)} מניות)")
            
            chunk_snapshots = []
            
            for stock in tqdm(stock_chunk, desc=f"Chunk {chunk_idx + 1}"):
                snapshots = self.compute_snapshots_for_stock(
                    stock_data, stock, dates, symbols,
                    lookback_days, forward_days, correlation_threshold
                )
                chunk_snapshots.extend(snapshots)
            
            # שמירה ל-DB
            if chunk_snapshots:
                logger.info(f"💾 שומר {len(chunk_snapshots)} snapshots ל-DB...")
                self.db_client.insert_correlation_snapshots(chunk_snapshots)
                all_snapshots.extend(chunk_snapshots)
        
        logger.info(f"✅ הושלם! נוצרו {len(all_snapshots)} snapshots")
        
        return all_snapshots
    
    def run(self, 
           symbols: Optional[List[str]] = None,
           start_date: Optional[str] = None,
           end_date: Optional[str] = None,
           test_mode: bool = False):
        """
        הרצת Pre-Computation מלא
        
        Args:
            symbols: רשימת מניות (אם None, טוען מ-DB)
            start_date: תאריך התחלה
            end_date: תאריך סיום
            test_mode: אם True, רץ רק על 10 מניות לבדיקה
        """
        logger.info("🚀 מתחיל Pre-Computation Engine...")
        
        # קבלת רשימת מניות
        if symbols is None:
            stocks_from_db = self.db_client.get_stock_list(active_only=True)
            if stocks_from_db:
                symbols = [s['symbol'] for s in stocks_from_db]
            else:
                # Fallback ל-DataFetcher
                logger.warning("⚠️ לא נמצאו מניות ב-DB, משתמש ב-DataFetcher...")
                symbols = self.data_fetcher.get_sp500_symbols()
        
        if test_mode:
            symbols = symbols[:10]
            logger.info(f"🧪 מצב בדיקה: מעבד רק {len(symbols)} מניות")
        
        # טעינת נתונים
        stock_data = self.load_stock_data(symbols, start_date or "2012-01-01")
        
        # חישוב snapshots
        snapshots = self.compute_all_snapshots(
            stock_data,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"✅ Pre-Computation הושלם בהצלחה!")
        logger.info(f"   📊 {len(snapshots)} snapshots נשמרו ב-DB")
        
        return snapshots


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeltaMix 2.0 Pre-Computation Engine')
    parser.add_argument('--test', action='store_true', help='מצב בדיקה (10 מניות)')
    parser.add_argument('--start-date', type=str, help='תאריך התחלה (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='תאריך סיום (YYYY-MM-DD)')
    parser.add_argument('--symbols', nargs='+', help='רשימת מניות ספציפית')
    
    args = parser.parse_args()
    
    engine = PreComputeEngine()
    engine.run(
        symbols=args.symbols,
        start_date=args.start_date,
        end_date=args.end_date,
        test_mode=args.test
    )


if __name__ == '__main__':
    main()


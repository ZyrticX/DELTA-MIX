"""
Daily Update System - עדכון יומי אוטומטי של נתונים וקורלציות
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import pickle

# הוספת נתיב למודולים
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher import DataFetcher
from .config import COMPUTATION_PARAMS, PATHS, CACHE_CONFIG
from .db_client import SupabaseClient
from .pre_compute import PreComputeEngine
from .utils import calculate_correlation_for_date, calculate_future_return, classify_movement

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyUpdateEngine:
    """
    מנוע עדכון יומי
    """
    
    def __init__(self):
        """אתחול"""
        self.data_fetcher = DataFetcher(cache_dir=PATHS['data_cache'])
        self.db_client = SupabaseClient()
        self.pre_compute = PreComputeEngine()
        self.params = COMPUTATION_PARAMS
    
    def update_stock_data(self, symbols: List[str]) -> Dict[str, Any]:
        """
        עדכון נתוני מניות ליום האחרון
        
        Args:
            symbols: רשימת מניות לעדכון
            
        Returns:
            Dict עם סטטיסטיקות
        """
        logger.info(f"📥 מעדכן נתונים עבור {len(symbols)} מניות...")
        
        updated = 0
        failed = []
        
        # תאריכים
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")  # 5 ימים אחורה (למקרה שיש gaps)
        
        for symbol in symbols:
            try:
                # הורדת נתונים (עם force_download=False כדי להשתמש בקאש אם אפשר)
                df = self.data_fetcher.download_stock_data(
                    symbol,
                    start_date=start_date,
                    end_date=end_date,
                    use_cache=True,
                    force_download=False  # לא כופה הורדה - משתמש בקאש אם קיים ועדכני
                )
                
                if df is not None and not df.empty:
                    # בדיקה אם יש נתונים חדשים
                    cache_file = os.path.join(PATHS['data_cache'], f"{symbol}_{start_date}_{end_date}.pkl")
                    
                    if os.path.exists(cache_file):
                        # טעינת קאש ישן
                        with open(cache_file, 'rb') as f:
                            old_df = pickle.load(f)
                        
                        # השוואה
                        if len(df) > len(old_df):
                            updated += 1
                            logger.debug(f"✅ {symbol}: עודכן ({len(old_df)} → {len(df)} שורות)")
                        else:
                            logger.debug(f"ℹ️ {symbol}: אין עדכונים")
                    else:
                        updated += 1
                        logger.debug(f"✅ {symbol}: נוצר קאש חדש")
                else:
                    failed.append(symbol)
                    
            except Exception as e:
                logger.warning(f"⚠️ שגיאה בעדכון {symbol}: {e}")
                failed.append(symbol)
        
        logger.info(f"✅ עדכון הושלם: {updated} עודכנו, {len(failed)} נכשלו")
        
        return {
            'updated': updated,
            'failed': failed,
            'total': len(symbols)
        }
    
    def compute_today_snapshots(self) -> int:
        """
        חישוב snapshots ליום האחרון בלבד
        
        Returns:
            מספר snapshots שנוצרו
        """
        logger.info("📊 מחשב snapshots ליום האחרון...")
        
        # קבלת רשימת מניות
        stocks_from_db = self.db_client.get_stock_list(active_only=True)
        if not stocks_from_db:
            logger.error("❌ לא נמצאו מניות ב-DB!")
            return 0
        
        symbols = [s['symbol'] for s in stocks_from_db]
        
        # טעינת נתונים
        try:
            stock_data = self.pre_compute.load_stock_data(symbols)
        except Exception as e:
            logger.error(f"❌ שגיאה בטעינת נתונים: {e}")
            return 0
        
        # תאריך היום
        today = datetime.now().date()
        today_datetime = pd.to_datetime(today)
        
        # בדיקה שיש מספיק נתונים
        if today_datetime not in stock_data.index:
            logger.warning("⚠️ אין נתונים ליום הנוכחי, משתמש ביום האחרון...")
            today_datetime = stock_data.index[-1]
        
        # בדיקה שיש lookback_days נתונים
        lookback_days = self.params['lookback_days']
        date_idx = stock_data.index.get_indexer([today_datetime], method='nearest')[0]
        
        if date_idx < lookback_days - 1:
            logger.error(f"❌ אין מספיק נתונים (צריך {lookback_days} ימים)")
            return 0
        
        # חישוב snapshots
        dates = [today_datetime]
        snapshots = []
        
        for stock in symbols:
            try:
                stock_snapshots = self.pre_compute.compute_snapshots_for_stock(
                    stock_data, stock, dates, symbols,
                    lookback_days,
                    self.params['forward_days'],
                    self.params['correlation_threshold']
                )
                snapshots.extend(stock_snapshots)
            except Exception as e:
                logger.warning(f"⚠️ שגיאה בחישוב snapshot עבור {stock}: {e}")
                continue
        
        # שמירה ל-DB
        if snapshots:
            logger.info(f"💾 שומר {len(snapshots)} snapshots ל-DB...")
            self.db_client.insert_correlation_snapshots(snapshots)
        
        logger.info(f"✅ נוצרו {len(snapshots)} snapshots")
        
        return len(snapshots)
    
    def update_pattern_statistics(self):
        """
        עדכון pattern statistics
        """
        logger.info("📈 מעדכן pattern statistics...")
        
        # קבלת רשימת מניות
        stocks_from_db = self.db_client.get_stock_list(active_only=True)
        if not stocks_from_db:
            return
        
        symbols = [s['symbol'] for s in stocks_from_db]
        
        # TODO: יישום חישוב pattern statistics
        # זה דורש אגרגציה של snapshots לפי pattern signature
        logger.info("⚠️ עדכון pattern statistics עדיין לא מיושם")
    
    def clean_old_cache(self):
        """
        ניקוי קאש ישן
        """
        logger.info("🧹 מנקה קאש ישן...")
        
        ttl_days = CACHE_CONFIG['daily_analysis_ttl_days']
        cutoff_date = datetime.now() - timedelta(days=ttl_days)
        
        try:
            # מחיקת cache entries ישנים
            self.db_client.client.table('daily_analysis_cache')\
                .delete()\
                .lt('expires_at', cutoff_date.isoformat())\
                .execute()
            
            logger.info(f"✅ נוקה קאש ישן מ-{cutoff_date.date()}")
        except Exception as e:
            logger.warning(f"⚠️ שגיאה בניקוי קאש: {e}")
    
    def run(self):
        """
        הרצת עדכון יומי מלא
        """
        logger.info("🚀 מתחיל עדכון יומי...")
        start_time = datetime.now()
        
        # 1. עדכון נתוני מניות
        stocks_from_db = self.db_client.get_stock_list(active_only=True)
        if not stocks_from_db:
            logger.error("❌ לא נמצאו מניות ב-DB! הרץ Apify scraper קודם.")
            return
        
        symbols = [s['symbol'] for s in stocks_from_db]
        update_result = self.update_stock_data(symbols)
        
        # 2. חישוב snapshots ליום האחרון
        snapshots_count = self.compute_today_snapshots()
        
        # 3. עדכון pattern statistics
        self.update_pattern_statistics()
        
        # 4. ניקוי קאש ישן
        self.clean_old_cache()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ עדכון יומי הושלם ב-{elapsed:.1f} שניות")
        logger.info(f"   📊 {snapshots_count} snapshots נוצרו")
        logger.info(f"   📥 {update_result['updated']} מניות עודכנו")


def main():
    """Main function"""
    engine = DailyUpdateEngine()
    engine.run()


if __name__ == '__main__':
    main()


"""
סקריפט לעדכון אוטומטי יומי
להפעלה עם cron/task scheduler
"""

import sys
import os
from datetime import datetime
import json
import logging

from data_fetcher import DataFetcher
from correlation_engine import CorrelationEngine

# הגדרת logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DailyUpdater:
    """
    מחלקה לניהול עדכון יומי אוטומטי
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        אתחול
        
        Args:
            config_file: קובץ הגדרות
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.fetcher = DataFetcher()
        
    def load_config(self) -> dict:
        """
        טעינת קובץ הגדרות
        """
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # הגדרות ברירת מחדל
            default_config = {
                'block_length': 15,
                'significance': 0.7,
                'calc_mode': 3,
                'ma_length': 10,
                'threshold': 0.01,
                'start_date': '2012-01-01',
                'reference_symbol': 'SPY',
                'num_stocks': 500,
                'notification_email': None,
                'min_opportunities_alert': 5
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: dict):
        """
        שמירת קובץ הגדרות
        """
        with open(self.config_file, 'w') as f:
            json.dump(config, indent=2, fp=f)
    
    def run_daily_update(self):
        """
        הפעלת עדכון יומי מלא
        """
        logger.info("="*50)
        logger.info("מתחיל עדכון יומי")
        logger.info(f"תאריך: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*50)
        
        try:
            # שלב 1: קבלת רשימת מניות
            logger.info("שלב 1: מקבל רשימת מניות S&P 500...")
            symbols = self.fetcher.get_sp500_symbols()
            symbols = symbols[:self.config['num_stocks']]
            logger.info(f"נמצאו {len(symbols)} מניות")
            
            # שלב 2: עדכון נתונים
            logger.info("שלב 2: מעדכן נתוני מניות...")
            stock_data = self.fetcher.download_multiple_stocks(
                symbols,
                start_date=self.config['start_date'],
                end_date=datetime.now().strftime("%Y-%m-%d"),
                use_cache=True
            )
            
            if stock_data is None or stock_data.empty:
                logger.error("נכשל בהורדת נתוני מניות")
                return False
            
            logger.info(f"נטענו נתונים: {len(stock_data)} ימים, {len(stock_data.columns)//3} מניות")  # Close, Adj Close, Volume
            
            # שלב 3: הרצת ניתוח (כולל הורדת מניית ייחוס)
            logger.info("שלב 3: מריץ ניתוח קורלציה...")
            
            # הורדת מניית ייחוס רק עבור הניתוח
            logger.info(f"מוריד נתוני מניית ייחוס ({self.config['reference_symbol']})...")
            reference_data = self.fetcher.get_reference_stock_data(
                self.config['reference_symbol'],
                start_date=self.config['start_date'],
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            if reference_data is None:
                logger.error(f"נכשל בהורדת נתוני {self.config['reference_symbol']}")
                return False
            
            engine = CorrelationEngine(self.config)
            results = engine.run_full_analysis(
                stock_data,
                reference_data['price'],
                reference_data['volume']
            )
            
            # שלב 4: זיהוי הזדמנויות
            logger.info("שלב 4: מזהה הזדמנויות...")
            opportunities = engine.find_today_opportunities(results)
            
            logger.info(f"נמצאו {len(opportunities)} הזדמנויות!")
            
            # שלב 5: שמירת תוצאות
            logger.info("שלב 5: שומר תוצאות...")
            self.save_daily_results(opportunities, results)
            
            # שלב 6: התראות
            if opportunities:
                self.send_notifications(opportunities)
            
            logger.info("="*50)
            logger.info("עדכון יומי הושלם בהצלחה!")
            logger.info("="*50)
            
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון יומי: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def save_daily_results(self, opportunities: list, results: dict):
        """
        שמירת תוצאות יומיות
        """
        date_str = datetime.now().strftime("%Y%m%d")
        
        # יצירת תיקיית תוצאות
        results_dir = "daily_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # שמירת הזדמנויות
        opportunities_file = os.path.join(results_dir, f"opportunities_{date_str}.json")
        with open(opportunities_file, 'w') as f:
            json.dump([
                {
                    'symbol': opp['symbol'],
                    'correlation': float(opp['correlation']),
                    'volume_ratio': float(opp['volume_ratio']),
                    'date': opp['date'].strftime('%Y-%m-%d')
                }
                for opp in opportunities
            ], f, indent=2)
        
        logger.info(f"הזדמנויות נשמרו ב-{opportunities_file}")
        
        # שמירת סטטיסטיקה
        import pandas as pd
        stats_df = pd.DataFrame(results['statistics']).T
        stats_file = os.path.join(results_dir, f"statistics_{date_str}.csv")
        stats_df.to_csv(stats_file)
        
        logger.info(f"סטטיסטיקה נשמרה ב-{stats_file}")
    
    def send_notifications(self, opportunities: list):
        """
        שליחת התראות על הזדמנויות
        """
        # סינון להזדמנויות משמעותיות
        significant_opps = [
            opp for opp in opportunities 
            if opp['correlation'] >= self.config.get('min_opportunities_alert', 5)
        ]
        
        if not significant_opps:
            logger.info("אין הזדמנויות משמעותיות להתראה")
            return
        
        logger.info(f"נמצאו {len(significant_opps)} הזדמנויות משמעותיות")
        
        # הדפסה לקובץ log
        logger.info("\n" + "="*50)
        logger.info("🎯 הזדמנויות מומלצות להיום:")
        logger.info("="*50)
        
        for i, opp in enumerate(significant_opps[:10], 1):
            logger.info(f"{i}. {opp['symbol']:6s} - קורלציה: {opp['correlation']:.3f}, יחס נפח: {opp['volume_ratio']:.3f}")
        
        logger.info("="*50 + "\n")
        
        # אם מוגדר email - שלח התראה
        if self.config.get('notification_email'):
            self.send_email_notification(significant_opps)
    
    def send_email_notification(self, opportunities: list):
        """
        שליחת התראת אימייל
        
        Note: דורש הגדרת SMTP
        """
        # להוספה בעתיד
        logger.info("שליחת אימייל (לא מוגדר)")
        pass


def main():
    """
    פונקציה ראשית
    """
    updater = DailyUpdater()
    
    # הפעלת עדכון
    success = updater.run_daily_update()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

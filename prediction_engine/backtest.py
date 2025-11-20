"""
Backtesting Engine - בדיקת דיוק המערכת על נתונים היסטוריים
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import logging

# הוספת נתיב למודולים
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .db_client import SupabaseClient
from .config import COMPUTATION_PARAMS
from .utils import calculate_similarity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    מנוע Backtesting לבדיקת דיוק המערכת
    """
    
    def __init__(self):
        """אתחול"""
        self.db_client = SupabaseClient()
        self.params = COMPUTATION_PARAMS
    
    def get_prediction_for_date(self,
                                stock_symbol: str,
                                date: datetime,
                                lookback_days: int = 15,
                                correlation_threshold: float = 0.85) -> Dict[str, Any]:
        """
        קבלת חיזוי לתאריך ספציפי
        
        Args:
            stock_symbol: סימול המניה
            date: תאריך לחיזוי
            lookback_days: ימים אחורה
            correlation_threshold: סף קורלציה
            
        Returns:
            Dict עם חיזוי או None
        """
        try:
            # שליפת snapshot נוכחי
            date_str = date.strftime('%Y-%m-%d')
            snapshots = self.db_client.get_correlation_snapshots(
                stock_symbol=stock_symbol,
                start_date=date_str,
                end_date=date_str,
                limit=1
            )
            
            if not snapshots:
                return None
            
            current_snapshot = snapshots[0]
            current_matches = current_snapshot.get('matched_stocks', [])
            
            if not current_matches:
                return None
            
            # חיפוש snapshots דומים מהעבר
            historical_snapshots = self.db_client.get_correlation_snapshots(
                stock_symbol=stock_symbol,
                end_date=date_str,
                limit=1000
            )
            
            # חישוב דמיון
            similar_cases = []
            for hist_snapshot in historical_snapshots:
                if hist_snapshot['snapshot_date'] >= date_str:
                    continue
                
                hist_matches = hist_snapshot.get('matched_stocks', [])
                similarity = calculate_similarity(current_matches, hist_matches)
                
                if similarity > 0.7 and hist_snapshot.get('future_return_pct') is not None:
                    similar_cases.append({
                        'similarity': similarity,
                        'future_return': hist_snapshot['future_return_pct'],
                        'date': hist_snapshot['snapshot_date']
                    })
            
            if not similar_cases:
                return None
            
            # חישוב חיזוי
            returns = [c['future_return'] for c in similar_cases]
            avg_return = sum(returns) / len(returns)
            up_count = sum(1 for r in returns if r > 0)
            confidence = max(up_count, len(returns) - up_count) / len(returns) * 100
            
            direction = 'up' if avg_return > 0 else 'down' if avg_return < 0 else 'neutral'
            
            return {
                'predicted_direction': direction,
                'predicted_return': avg_return,
                'confidence': confidence,
                'similar_cases': len(similar_cases)
            }
            
        except Exception as e:
            logger.error(f"❌ שגיאה בחישוב חיזוי עבור {stock_symbol} ב-{date}: {e}")
            return None
    
    def get_actual_outcome(self,
                          stock_symbol: str,
                          date: datetime,
                          forward_days: int = 15) -> Dict[str, Any]:
        """
        קבלת תוצאה בפועל
        
        Args:
            stock_symbol: סימול המניה
            date: תאריך התחלה
            forward_days: ימים קדימה
            
        Returns:
            Dict עם תוצאה בפועל
        """
        try:
            future_date = (date + timedelta(days=forward_days)).strftime('%Y-%m-%d')
            
            snapshots = self.db_client.get_correlation_snapshots(
                stock_symbol=stock_symbol,
                start_date=date.strftime('%Y-%m-%d'),
                end_date=date.strftime('%Y-%m-%d'),
                limit=1
            )
            
            if not snapshots:
                return None
            
            snapshot = snapshots[0]
            future_return = snapshot.get('future_return_pct')
            
            if future_return is None:
                return None
            
            direction = 'up' if future_return > 0 else 'down' if future_return < 0 else 'neutral'
            
            return {
                'actual_direction': direction,
                'actual_return': future_return
            }
            
        except Exception as e:
            logger.error(f"❌ שגיאה בשליפת תוצאה בפועל עבור {stock_symbol} ב-{date}: {e}")
            return None
    
    def is_correct(self, prediction: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """
        בדיקה אם החיזוי נכון
        
        Args:
            prediction: חיזוי
            actual: תוצאה בפועל
            
        Returns:
            True אם נכון
        """
        if not prediction or not actual:
            return False
        
        pred_dir = prediction.get('predicted_direction')
        actual_dir = actual.get('actual_direction')
        
        return pred_dir == actual_dir
    
    def run_backtest(self,
                    stock_symbols: List[str],
                    start_date: str,
                    end_date: str,
                    lookback_days: int = 15,
                    correlation_threshold: float = 0.85,
                    forward_days: int = 15) -> Dict[str, Any]:
        """
        הרצת Backtest
        
        Args:
            stock_symbols: רשימת מניות
            start_date: תאריך התחלה
            end_date: תאריך סיום
            lookback_days: ימים אחורה
            correlation_threshold: סף קורלציה
            forward_days: ימים קדימה
            
        Returns:
            Dict עם תוצאות Backtest
        """
        logger.info(f"🧪 מתחיל Backtest עבור {len(stock_symbols)} מניות")
        logger.info(f"   מ-{start_date} עד {end_date}")
        
        results = []
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # יצירת רשימת תאריכים (כל יום)
        current = start
        dates = []
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        logger.info(f"   {len(dates)} תאריכים לבדיקה")
        
        for stock_symbol in stock_symbols:
            logger.info(f"📊 בודק {stock_symbol}...")
            
            for date in dates:
                try:
                    # חיזוי
                    prediction = self.get_prediction_for_date(
                        stock_symbol, date, lookback_days, correlation_threshold
                    )
                    
                    if not prediction:
                        continue
                    
                    # תוצאה בפועל
                    actual = self.get_actual_outcome(stock_symbol, date, forward_days)
                    
                    if not actual:
                        continue
                    
                    # בדיקה
                    is_correct = self.is_correct(prediction, actual)
                    
                    results.append({
                        'stock_symbol': stock_symbol,
                        'date': date.strftime('%Y-%m-%d'),
                        'predicted_direction': prediction['predicted_direction'],
                        'predicted_return': prediction['predicted_return'],
                        'actual_direction': actual['actual_direction'],
                        'actual_return': actual['actual_return'],
                        'confidence': prediction['confidence'],
                        'correct': is_correct
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ שגיאה בבדיקה עבור {stock_symbol} ב-{date}: {e}")
                    continue
        
        # חישוב metrics
        total = len(results)
        correct = sum(1 for r in results if r['correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Precision: מתוך חיזויים "למעלה", כמה אכן עלו
        up_predictions = [r for r in results if r['predicted_direction'] == 'up']
        up_correct = sum(1 for r in up_predictions if r['actual_direction'] == 'up')
        precision = (up_correct / len(up_predictions) * 100) if up_predictions else 0
        
        # Recall: מתוך עליות בפועל, כמה זיהינו
        actual_ups = [r for r in results if r['actual_direction'] == 'up']
        up_recalled = sum(1 for r in actual_ups if r['predicted_direction'] == 'up')
        recall = (up_recalled / len(actual_ups) * 100) if actual_ups else 0
        
        # F1 Score
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
        
        logger.info(f"✅ Backtest הושלם!")
        logger.info(f"   📊 {total} בדיקות")
        logger.info(f"   ✅ {correct} נכונות ({accuracy:.2f}%)")
        logger.info(f"   📈 Precision: {precision:.2f}%")
        logger.info(f"   📉 Recall: {recall:.2f}%")
        logger.info(f"   🎯 F1 Score: {f1:.2f}%")
        
        return {
            'total_tests': total,
            'correct': correct,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'results': results
        }


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeltaMix 2.0 Backtesting Engine')
    parser.add_argument('--stocks', nargs='+', help='רשימת מניות (אם לא מוגדר, משתמש בכל המניות)')
    parser.add_argument('--start-date', type=str, required=True, help='תאריך התחלה (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True, help='תאריך סיום (YYYY-MM-DD)')
    parser.add_argument('--lookback-days', type=int, default=15, help='ימים אחורה')
    parser.add_argument('--correlation-threshold', type=float, default=0.85, help='סף קורלציה')
    parser.add_argument('--forward-days', type=int, default=15, help='ימים קדימה')
    
    args = parser.parse_args()
    
    engine = BacktestEngine()
    
    # קבלת רשימת מניות
    if args.stocks:
        stock_symbols = args.stocks
    else:
        stocks_from_db = engine.db_client.get_stock_list(active_only=True)
        stock_symbols = [s['symbol'] for s in stocks_from_db]
    
    # הרצת Backtest
    results = engine.run_backtest(
        stock_symbols,
        args.start_date,
        args.end_date,
        args.lookback_days,
        args.correlation_threshold,
        args.forward_days
    )
    
    print("\n" + "="*50)
    print("תוצאות Backtest:")
    print("="*50)
    print(f"סה\"כ בדיקות: {results['total_tests']}")
    print(f"נכונות: {results['correct']} ({results['accuracy']:.2f}%)")
    print(f"Precision: {results['precision']:.2f}%")
    print(f"Recall: {results['recall']:.2f}%")
    print(f"F1 Score: {results['f1_score']:.2f}%")


if __name__ == '__main__':
    main()


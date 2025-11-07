"""
מנוע חישוב קורלציה - משכפל בדיוק את הנוסחאות מהאקסל
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class CorrelationEngine:
    """
    מנוע חישוב קורלציות - משכפל בדיוק את הלוגיקה של האקסל
    """
    
    def __init__(self, params: Dict):
        """
        אתחול המנוע עם פרמטרים
        
        Args:
            params: מילון פרמטרים:
                - block_length: אורך בלוק לחישוב קורלציה (15)
                - significance: סף מובהקות (0.7)
                - calc_mode: סוג חישוב (1=שער, 2=מחזור, 3=מכפלה)
                - ma_length: אורך ממוצע נע (10)
                - threshold: סף מהותיות (0.01)
                - price_field: שדה מחיר לניתוח ('Close' או 'Adj Close')
        """
        self.block_length = params.get('block_length', 15)
        self.significance = params.get('significance', 0.7)
        self.calc_mode = params.get('calc_mode', 3)
        self.ma_length = params.get('ma_length', 10)
        self.threshold = params.get('threshold', 0.01)
        self.price_field = params.get('price_field', 'Close')  # Close או Adj Close
        
    def calculate_rolling_correlation(self, 
                                     series: pd.Series, 
                                     reference: pd.Series,
                                     window: int) -> pd.Series:
        """
        חישוב קורלציה גלילית - בדיוק כמו CORREL+OFFSET באקסל
        
        משכפל את הנוסחה:
        =CORREL(OFFSET(D2,0,0,פרמטרים!$E$2,1),
                OFFSET(פרמטרים!$C$2,0,0,פרמטרים!$E$2,1))
        
        🔬 חישוב על מחירים גולמיים (לא תשואות!) - בדיוק כמו באקסל
        
        Args:
            series: סדרת נתונים של המניה (מחירים או נפחים)
            reference: סדרת נתונים של מניית הייחוס
            window: אורך החלון לחישוב קורלציה (ברירת מחדל: 15)
        
        Returns:
            pd.Series: קורלציות גלילית לכל תאריך
        """
        correlations = []
        
        for i in range(len(series)):
            if i < window - 1:
                # אין מספיק נתונים - החזר 0 (כמו IF($A2>1230,0,...) באקסל)
                correlations.append(0)
            else:
                # קח window ערכים אחורה (כולל הערך הנוכחי)
                # זה בדיוק כמו OFFSET(D2,0,0,15,1) באקסל
                stock_window = series.iloc[i-window+1:i+1]
                ref_window = reference.iloc[i-window+1:i+1]
                
                # חישוב קורלציה (CORREL באקסל = קורלציית פירסון)
                if len(stock_window) == window and len(ref_window) == window:
                    # בדוק שאין NaN
                    if stock_window.notna().all() and ref_window.notna().all():
                        corr = stock_window.corr(ref_window)
                        correlations.append(corr if not np.isnan(corr) else 0)
                    else:
                        correlations.append(0)
                else:
                    correlations.append(0)
                    
        return pd.Series(correlations, index=series.index)
    
    def calculate_sheet_correlations(self, 
                                    stock_data: pd.DataFrame,
                                    reference_price: pd.Series,
                                    reference_volume: pd.Series) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        חישוב קורלציות עבור גיליונות "שער" ו"מחזור"
        
        Returns:
            (price_corr_df, volume_corr_df)
        """
        price_correlations = {}
        volume_correlations = {}
        
        for symbol in stock_data.columns.get_level_values(0).unique():
            # קורלציית מחיר - משתמש בשדה שנבחר (Close או Adj Close)
            if (symbol, self.price_field) not in stock_data.columns:
                # אם השדה לא קיים, נסה Close
                price_field = 'Close'
            else:
                price_field = self.price_field
            
            stock_prices = stock_data[(symbol, price_field)]
            price_corr = self.calculate_rolling_correlation(
                stock_prices, 
                reference_price, 
                self.block_length
            )
            price_correlations[symbol] = price_corr
            
            # קורלציית מחזור
            stock_volumes = stock_data[(symbol, 'Volume')]
            volume_corr = self.calculate_rolling_correlation(
                stock_volumes,
                reference_volume,
                self.block_length
            )
            volume_correlations[symbol] = volume_corr
        
        price_df = pd.DataFrame(price_correlations)
        volume_df = pd.DataFrame(volume_correlations)
        
        return price_df, volume_df
    
    def combine_correlations(self,
                           price_corr: pd.DataFrame,
                           volume_corr: pd.DataFrame) -> pd.DataFrame:
        """
        שילוב קורלציות לפי סוג החישוב
        
        משכפל את הנוסחה:
        =IF(פרמטרים!$G$2=1,שער!M2,
           IF(פרמטרים!$G$2=2,מחזור!M2,
              IF(פרמטרים!$G$2=3,
                 (IF(OR(שער!M2<0,מחזור!M2<0),0,שער!M2*מחזור!M2)),
                 0)))
        """
        combined = pd.DataFrame(index=price_corr.index)
        
        for col in price_corr.columns:
            if self.calc_mode == 1:
                # רק קורלציית שער
                combined[col] = price_corr[col]
            elif self.calc_mode == 2:
                # רק קורלציית מחזור
                combined[col] = volume_corr[col]
            elif self.calc_mode == 3:
                # מכפלה - רק אם שניהם חיוביים
                combined[col] = np.where(
                    (price_corr[col] < 0) | (volume_corr[col] < 0),
                    0,
                    price_corr[col] * volume_corr[col]
                )
        
        return combined
    
    def calculate_volume_ratio(self,
                              volumes: pd.DataFrame,
                              combined_corr: pd.DataFrame) -> pd.DataFrame:
        """
        חישוב יחס מחזור לממוצע נע
        
        משכפל את הנוסחה:
        =IF($A2<פרמטרים!$H$2+1,0,
           IF(C2<פרמטרים!$F$2,0,
              AVERAGE(OFFSET(M2,-פרמטרים!$H$2,0,פרמטרים!$H$2,1))/M2))
        """
        ratio_df = pd.DataFrame(index=volumes.index)
        
        for col in volumes.columns:
            ratios = []
            
            for i in range(len(volumes)):
                # תנאי 1: יש מספיק נתונים היסטוריים
                if i < self.ma_length:
                    ratios.append(0)
                    continue
                
                # תנאי 2: הקורלציה עוברת את סף המובהקות
                if combined_corr[col].iloc[i] < self.significance:
                    ratios.append(0)
                    continue
                
                # חישוב הממוצע
                volume_window = volumes[col].iloc[i-self.ma_length:i]
                avg_volume = volume_window.mean()
                current_volume = volumes[col].iloc[i]
                
                if current_volume > 0:
                    ratio = avg_volume / current_volume
                    ratios.append(ratio)
                else:
                    ratios.append(0)
            
            ratio_df[col] = ratios
        
        return ratio_df
    
    def filter_opportunities(self, ratio_df: pd.DataFrame) -> pd.DataFrame:
        """
        סינון הזדמנויות - ימים שבהם היחס עובר את הסף
        
        משכפל את:
        =COUNTIF(W$2:W$1259,">"&1+פרמטרים!$I$2)
        """
        threshold_value = 1 + self.threshold
        
        # ספירה לכל מניה
        opportunities = {}
        
        for col in ratio_df.columns:
            # כמה ימים היחס עובר את הסף
            count = (ratio_df[col] > threshold_value).sum()
            opportunities[col] = count
        
        return pd.Series(opportunities)
    
    def calculate_statistics(self, 
                            ratio_df: pd.DataFrame) -> Dict:
        """
        חישוב סטטיסטיקה מסכמת (שורות 2-4 באקסל)
        """
        threshold_value = 1 + self.threshold
        
        stats = {}
        
        for col in ratio_df.columns:
            # UP: ימים שעוברים את הסף
            up_count = (ratio_df[col] > threshold_value).sum()
            
            # TOTAL: כל הימים עם קורלציה מובהקת (ratio > 0)
            total_count = (ratio_df[col] > 0).sum()
            
            # DOWN: ימים עם קורלציה מובהקת שלא עוברים את הסף
            down_count = total_count - up_count
            
            stats[col] = {
                'UP': up_count,
                'DOWN': down_count,
                'TOTAL': total_count,
                'UP_PCT': up_count / total_count if total_count > 0 else 0,
                'DOWN_PCT': down_count / total_count if total_count > 0 else 0
            }
        
        return stats
    
    def run_full_analysis(self,
                         stock_data: pd.DataFrame,
                         reference_price: pd.Series,
                         reference_volume: pd.Series) -> Dict:
        """
        הרצה מלאה של כל הניתוח
        
        Returns:
            Dict עם כל התוצאות:
            - price_correlations
            - volume_correlations
            - combined_correlations
            - volume_ratios
            - statistics
            - opportunities (למניות בודדות)
        """
        print("שלב 1: חישוב קורלציות שער ומחזור...")
        price_corr, volume_corr = self.calculate_sheet_correlations(
            stock_data, reference_price, reference_volume
        )
        
        print("שלב 2: שילוב קורלציות...")
        combined = self.combine_correlations(price_corr, volume_corr)
        
        print("שלב 3: חישוב יחסי מחזור...")
        # צריך להפיק את נפחי המסחר
        volumes = pd.DataFrame({
            col: stock_data[(col, 'Volume')] 
            for col in stock_data.columns.get_level_values(0).unique()
        })
        
        volume_ratios = self.calculate_volume_ratio(volumes, combined)
        
        print("שלב 4: חישוב סטטיסטיקה...")
        stats = self.calculate_statistics(volume_ratios)
        
        print("ניתוח הושלם!")
        
        return {
            'price_correlations': price_corr,
            'volume_correlations': volume_corr,
            'combined_correlations': combined,
            'volume_ratios': volume_ratios,
            'volumes': volumes,
            'statistics': stats
        }
    
    def find_today_opportunities(self, results: Dict) -> List[Dict]:
        """
        מציאת ההזדמנויות להיום (היום האחרון בנתונים)
        """
        volume_ratios = results['volume_ratios']
        combined_corr = results['combined_correlations']
        
        last_idx = volume_ratios.index[-1]
        threshold_value = 1 + self.threshold
        
        opportunities = []
        
        for col in volume_ratios.columns:
            ratio = volume_ratios[col].iloc[-1]
            corr = combined_corr[col].iloc[-1]
            
            # בדוק אם זו הזדמנות
            if ratio > threshold_value and corr >= self.significance:
                opportunities.append({
                    'symbol': col,
                    'correlation': corr,
                    'volume_ratio': ratio,
                    'date': last_idx
                })
        
        # מיון לפי correlation (הגבוה ביותר קודם)
        opportunities.sort(key=lambda x: x['correlation'], reverse=True)
        
        return opportunities
    
    def validate_correlations(self, results: Dict) -> Dict:
        """
        בדיקת איכות הקורלציות - זיהוי ערכים חשודים
        
        Returns:
            Dict עם מידע על איכות הקורלציות:
            - suspicious_high: מניות עם קורלציה מעל 0.95
            - average_correlation: ממוצע כל הקורלציות
            - median_correlation: חציון הקורלציות
            - distribution: התפלגות הקורלציות
        """
        validation = {
            'suspicious_high': [],  # קורלציות מעל 0.95
            'average_correlation': 0,
            'median_correlation': 0,
            'distribution': {
                'low': 0,      # 0-0.3
                'medium': 0,   # 0.3-0.7
                'high': 0,     # 0.7-0.9
                'very_high': 0 # 0.9-1.0
            }
        }
        
        combined = results['combined_correlations']
        
        # חישוב סטטיסטיקות כלליות
        all_corr_values = []
        for col in combined.columns:
            # קח רק ערכים תקינים (לא NaN ולא 0)
            col_values = combined[col].values
            valid_values = col_values[(~np.isnan(col_values)) & (col_values > 0)]
            all_corr_values.extend(valid_values.tolist())
        
        if all_corr_values:
            all_corr_array = np.array(all_corr_values)
            validation['average_correlation'] = float(np.mean(all_corr_array))
            validation['median_correlation'] = float(np.median(all_corr_array))
            
            # התפלגות
            validation['distribution']['low'] = int(np.sum((all_corr_array > 0) & (all_corr_array < 0.3)))
            validation['distribution']['medium'] = int(np.sum((all_corr_array >= 0.3) & (all_corr_array < 0.7)))
            validation['distribution']['high'] = int(np.sum((all_corr_array >= 0.7) & (all_corr_array < 0.9)))
            validation['distribution']['very_high'] = int(np.sum(all_corr_array >= 0.9))
        
        # מניות עם קורלציה גבוהה מדי
        for col in combined.columns:
            max_corr = combined[col].max()
            if not np.isnan(max_corr) and max_corr > 0.95:
                validation['suspicious_high'].append({
                    'symbol': col,
                    'max_correlation': float(max_corr)
                })
        
        return validation
    
    def calculate_full_correlation_matrix(self,
                                        stock_data: pd.DataFrame,
                                        field: str = 'Close') -> pd.DataFrame:
        """
        חישוב מטריצת קורלציה מלאה בין כל המניות
        
        Args:
            stock_data: DataFrame עם MultiIndex (symbol, field)
            field: השדה לחישוב קורלציה ('Close', 'Adj Close', 'Volume')
        
        Returns:
            DataFrame עם מטריצת קורלציה - כל מניה מול כל מניה
        """
        # חילוץ כל המניות
        symbols = stock_data.columns.get_level_values(0).unique()
        
        # יצירת DataFrame של השדה הנבחר לכל המניות
        data_dict = {}
        for symbol in symbols:
            # נסה את השדה המבוקש
            if (symbol, field) in stock_data.columns:
                data_dict[symbol] = stock_data[(symbol, field)]
            elif (symbol, 'Close') in stock_data.columns:
                # נפילה ל-Close אם השדה המבוקש לא קיים
                data_dict[symbol] = stock_data[(symbol, 'Close')]
            else:
                # דלג על מניות ללא נתונים
                continue
        
        if not data_dict:
            return pd.DataFrame()
        
        # יצירת DataFrame
        data_df = pd.DataFrame(data_dict)
        
        # חישוב מטריצת קורלציה
        correlation_matrix = data_df.corr()
        
        return correlation_matrix
    
    def calculate_rolling_correlation_matrix(self,
                                          stock_data: pd.DataFrame,
                                          field: str = 'Close',
                                          window: int = 15) -> pd.DataFrame:
        """
        חישוב מטריצת קורלציה גלילית - קורלציה על חלון זמן מסוים
        
        Args:
            stock_data: DataFrame עם MultiIndex (symbol, field)
            field: השדה לחישוב קורלציה
            window: גודל החלון לחישוב קורלציה
        
        Returns:
            DataFrame עם מטריצת קורלציה ממוצעת על כל התקופה
        """
        # חילוץ כל המניות
        symbols = stock_data.columns.get_level_values(0).unique()
        
        # יצירת DataFrame של השדה הנבחר
        data_dict = {}
        for symbol in symbols:
            if (symbol, field) in stock_data.columns:
                data_dict[symbol] = stock_data[(symbol, field)]
            elif (symbol, 'Close') in stock_data.columns:
                data_dict[symbol] = stock_data[(symbol, 'Close')]
            else:
                continue
        
        if not data_dict:
            return pd.DataFrame()
        
        data_df = pd.DataFrame(data_dict)
        
        # חישוב קורלציות גליליות ואז ממוצע
        correlations_list = []
        
        for i in range(window - 1, len(data_df)):
            window_data = data_df.iloc[i-window+1:i+1]
            # בדוק שיש מספיק נתונים תקינים
            valid_data = window_data.dropna()
            if len(valid_data) >= window * 0.8:  # לפחות 80% מהנתונים תקינים
                corr_matrix = valid_data.corr()
                correlations_list.append(corr_matrix)
        
        if not correlations_list:
            # אם אין מספיק נתונים, נחזיר קורלציה רגילה
            return data_df.corr()
        
        # ממוצע של כל המטריצות
        # נשתמש ב-numpy כדי לחשב ממוצע
        corr_arrays = [corr.values for corr in correlations_list]
        avg_corr_array = np.nanmean(corr_arrays, axis=0)
        avg_correlation = pd.DataFrame(
            avg_corr_array,
            index=correlations_list[0].index,
            columns=correlations_list[0].columns
        )
        
        return avg_correlation
    
    def find_top_correlations(self,
                            correlation_matrix: pd.DataFrame,
                            top_n: int = 50) -> pd.DataFrame:
        """
        מציאת הקורלציות הגבוהות ביותר
        
        Args:
            correlation_matrix: מטריצת קורלציה
            top_n: מספר הקורלציות הגבוהות ביותר להחזיר
        
        Returns:
            DataFrame עם הקורלציות הגבוהות ביותר
        """
        # המרה לרשימת tuples (stock1, stock2, correlation)
        correlations = []
        
        for i, stock1 in enumerate(correlation_matrix.index):
            for j, stock2 in enumerate(correlation_matrix.columns):
                if i < j:  # רק חצי מהמטריצה (למנוע כפילויות)
                    corr_value = correlation_matrix.iloc[i, j]
                    if not np.isnan(corr_value):
                        correlations.append({
                            'מניה 1': stock1,
                            'מניה 2': stock2,
                            'קורלציה': corr_value
                        })
        
        # המרה ל-DataFrame ומיון
        corr_df = pd.DataFrame(correlations)
        corr_df = corr_df.sort_values('קורלציה', ascending=False)
        
        return corr_df.head(top_n)


def test_engine():
    """
    בדיקה בסיסית של המנוע
    """
    # יצירת נתונים דמה
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    
    stock1 = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
    stock2 = pd.Series(np.random.randn(100).cumsum() + 50, index=dates)
    reference = pd.Series(np.random.randn(100).cumsum() + 200, index=dates)
    
    # יצירת DataFrame מתוקן
    stock_data = pd.DataFrame({
        ('STOCK1', 'Close'): stock1,
        ('STOCK1', 'Volume'): np.random.randint(1000000, 10000000, 100),
        ('STOCK2', 'Close'): stock2,
        ('STOCK2', 'Volume'): np.random.randint(1000000, 10000000, 100)
    })
    
    ref_price = reference
    ref_volume = pd.Series(np.random.randint(1000000, 10000000, 100), index=dates)
    
    # פרמטרים
    params = {
        'block_length': 15,
        'significance': 0.7,
        'calc_mode': 3,
        'ma_length': 10,
        'threshold': 0.01
    }
    
    # הרצה
    engine = CorrelationEngine(params)
    results = engine.run_full_analysis(stock_data, ref_price, ref_volume)
    
    print("\n=== תוצאות בדיקה ===")
    print(f"מספר ימים: {len(results['combined_correlations'])}")
    print(f"מספר מניות: {len(results['statistics'])}")
    
    for symbol, stat in results['statistics'].items():
        print(f"\n{symbol}:")
        print(f"  UP: {stat['UP']} ({stat['UP_PCT']:.1%})")
        print(f"  DOWN: {stat['DOWN']} ({stat['DOWN_PCT']:.1%})")
        print(f"  TOTAL: {stat['TOTAL']}")


if __name__ == '__main__':
    test_engine()

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
    
    def calculate_rolling_correlation_over_time(self,
                                               stock_data: pd.DataFrame,
                                               field: str = 'Close',
                                               window: int = 30) -> Dict:
        """
        חישוב קורלציות גליליות לאורך זמן - לכל תאריך
        
        Args:
            stock_data: DataFrame עם MultiIndex (symbol, field)
            field: השדה לחישוב קורלציה
            window: גודל החלון לחישוב קורלציה
        
        Returns:
            Dict: {stock1: DataFrame שבו עמודות הן המניות האחרות ושורות הן תאריכים}
        """
        # חילוץ כל המניות
        symbols = stock_data.columns.get_level_values(0).unique().tolist()
        
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
            return {}
        
        data_df = pd.DataFrame(data_dict)
        
        # יצירת מבנה נתונים לאחסון קורלציות לאורך זמן
        # לכל מניה נשמור DataFrame שבו העמודות הן מניות אחרות והשורות הן תאריכים
        result = {}
        
        for stock1 in symbols:
            if stock1 not in data_df.columns:
                continue
            
            stock1_correlations = {}
            
            for stock2 in symbols:
                if stock2 not in data_df.columns or stock1 == stock2:
                    continue
                
                # חישוב rolling correlation בין stock1 ל-stock2
                rolling_corr = data_df[stock1].rolling(window).corr(data_df[stock2])
                stock1_correlations[stock2] = rolling_corr
            
            if stock1_correlations:
                result[stock1] = pd.DataFrame(stock1_correlations)
        
        return result
    
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
    
    def calculate_returns(self, stock_data: pd.DataFrame) -> Dict:
        """
        חישוב תשואות למניות
        
        Args:
            stock_data: DataFrame עם MultiIndex (symbol, field)
        
        Returns:
            Dict עם:
            - daily_returns: DataFrame של תשואות יומיות (%)
            - cumulative_returns: DataFrame של תשואות מצטברות (%)
            - annualized_returns: Series של תשואות שנתיות ממוצעות (%)
        """
        symbols = stock_data.columns.get_level_values(0).unique()
        
        results = {
            'daily_returns': {},
            'cumulative_returns': {},
            'annualized_returns': {}
        }
        
        for symbol in symbols:
            # קבלת מחירים - השתמש ב-price_field שהוגדר
            if (symbol, self.price_field) in stock_data.columns:
                prices = stock_data[(symbol, self.price_field)]
            elif (symbol, 'Adj Close') in stock_data.columns:
                prices = stock_data[(symbol, 'Adj Close')]
            elif (symbol, 'Close') in stock_data.columns:
                prices = stock_data[(symbol, 'Close')]
            else:
                continue
            
            # תשואה יומית: (price_today - price_yesterday) / price_yesterday * 100
            daily_ret = prices.pct_change() * 100
            results['daily_returns'][symbol] = daily_ret
            
            # תשואה מצטברת: ((price_today - price_first) / price_first) * 100
            first_price = prices.iloc[0]
            cumulative_ret = ((prices - first_price) / first_price) * 100
            results['cumulative_returns'][symbol] = cumulative_ret
            
            # תשואה שנתית ממוצעת
            num_years = len(prices) / 252  # 252 ימי מסחר בשנה
            if num_years > 0 and not pd.isna(cumulative_ret.iloc[-1]):
                total_return = cumulative_ret.iloc[-1]
                annual_ret = total_return / num_years
                results['annualized_returns'][symbol] = annual_ret
            else:
                results['annualized_returns'][symbol] = 0
        
        return {
            'daily_returns': pd.DataFrame(results['daily_returns']),
            'cumulative_returns': pd.DataFrame(results['cumulative_returns']),
            'annualized_returns': pd.Series(results['annualized_returns'])
        }


if __name__ == '__main__':
    print("correlation_engine.py - מנוע חישוב קורלציות")

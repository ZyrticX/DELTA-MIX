"""
פונקציות עזר למערכת DeltaMix 2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import hashlib
import json


def classify_movement(future_return: float, thresholds: Dict[str, float]) -> str:
    """
    סיווג תנועה עתידית לפי thresholds
    
    Args:
        future_return: תשואה עתידית באחוזים
        thresholds: מילון עם thresholds
        
    Returns:
        'strong_up', 'moderate_up', 'neutral', 'moderate_down', 'strong_down'
    """
    if future_return >= thresholds['strong_up']:
        return 'strong_up'
    elif future_return >= thresholds['moderate_up']:
        return 'moderate_up'
    elif future_return >= thresholds['neutral_lower'] and future_return <= thresholds['neutral_upper']:
        return 'neutral'
    elif future_return >= thresholds['moderate_down']:
        return 'moderate_down'
    else:
        return 'strong_down'


def calculate_correlation_for_date(stock_data: pd.DataFrame,
                                   stock1: str,
                                   stock2: str,
                                   date: datetime,
                                   lookback_days: int,
                                   field: str = 'Adj Close') -> Optional[float]:
    """
    חישוב קורלציה בין שתי מניות לתאריך ספציפי
    
    Args:
        stock_data: DataFrame עם MultiIndex (symbol, field)
        stock1: סימול מניה ראשונה
        stock2: סימול מניה שנייה
        date: תאריך לחישוב
        lookback_days: מספר ימים אחורה
        field: שדה לחישוב ('Adj Close' או 'Volume')
        
    Returns:
        קורלציה או None אם אין מספיק נתונים
    """
    try:
        # קבלת נתונים למניה 1
        if (stock1, field) in stock_data.columns:
            series1 = stock_data[(stock1, field)]
        else:
            return None
        
        # קבלת נתונים למניה 2
        if (stock2, field) in stock_data.columns:
            series2 = stock_data[(stock2, field)]
        else:
            return None
        
        # מציאת אינדקס התאריך
        date_idx = series1.index.get_indexer([date], method='nearest')[0]
        if date_idx < 0 or date_idx < lookback_days - 1:
            return None
        
        # חלון נתונים
        start_idx = date_idx - lookback_days + 1
        window1 = series1.iloc[start_idx:date_idx + 1]
        window2 = series2.iloc[start_idx:date_idx + 1]
        
        # בדיקת תקינות
        if len(window1) < lookback_days or len(window2) < lookback_days:
            return None
        
        # הסרת NaN
        valid_mask = window1.notna() & window2.notna()
        if valid_mask.sum() < lookback_days * 0.8:  # לפחות 80% מהנתונים תקינים
            return None
        
        window1_clean = window1[valid_mask]
        window2_clean = window2[valid_mask]
        
        if len(window1_clean) < 10:  # מינימום 10 נקודות
            return None
        
        # חישוב קורלציה
        corr = window1_clean.corr(window2_clean)
        
        if pd.isna(corr):
            return None
        
        return float(corr)
        
    except Exception:
        return None


def calculate_future_return(stock_data: pd.DataFrame,
                            stock: str,
                            date: datetime,
                            forward_days: int,
                            field: str = 'Adj Close') -> Optional[float]:
    """
    חישוב תשואה עתידית
    
    Args:
        stock_data: DataFrame עם MultiIndex
        stock: סימול המניה
        date: תאריך התחלה
        forward_days: מספר ימים קדימה
        field: שדה מחיר
        
    Returns:
        תשואה באחוזים או None
    """
    try:
        if (stock, field) not in stock_data.columns:
            return None
        
        prices = stock_data[(stock, field)]
        
        # מציאת אינדקסים
        date_idx = prices.index.get_indexer([date], method='nearest')[0]
        if date_idx < 0:
            return None
        
        future_idx = date_idx + forward_days
        if future_idx >= len(prices):
            return None
        
        # מחירים
        price_start = prices.iloc[date_idx]
        price_end = prices.iloc[future_idx]
        
        if pd.isna(price_start) or pd.isna(price_end) or price_start == 0:
            return None
        
        # תשואה באחוזים
        return ((price_end - price_start) / price_start) * 100
        
    except Exception:
        return None


def create_pattern_signature(matched_stocks: List[Dict[str, float]], threshold: float) -> str:
    """
    יצירת pattern signature ממילון matched stocks
    
    Args:
        matched_stocks: רשימת מניות בקורלציה [{symbol, corr_price, corr_volume}]
        threshold: סף קורלציה
        
    Returns:
        String signature (למשל: "MSFT+GOOGL+NVDA:0.85")
    """
    symbols = sorted([m['symbol'] for m in matched_stocks])
    return f"{'+'.join(symbols)}:{threshold:.2f}"


def calculate_similarity(pattern1: List[Dict[str, float]], 
                       pattern2: List[Dict[str, float]]) -> float:
    """
    חישוב דמיון בין שתי תמונות קורלציה
    
    Args:
        pattern1: רשימת מניות בקורלציה ראשונה
        pattern2: רשימת מניות בקורלציה שנייה
        
    Returns:
        ציון דמיון (0-1)
    """
    if not pattern1 or not pattern2:
        return 0.0
    
    # יצירת sets של symbols
    symbols1 = {m['symbol'] for m in pattern1}
    symbols2 = {m['symbol'] for m in pattern2}
    
    # Jaccard similarity
    intersection = len(symbols1 & symbols2)
    union = len(symbols1 | symbols2)
    
    if union == 0:
        return 0.0
    
    base_similarity = intersection / union
    
    # התחשבות גם בערכי הקורלציה
    if intersection > 0:
        corr_similarity = 0.0
        count = 0
        
        # יצירת מילון של קורלציות
        corr1 = {m['symbol']: m.get('corr_price', 0) for m in pattern1}
        corr2 = {m['symbol']: m.get('corr_price', 0) for m in pattern2}
        
        for symbol in symbols1 & symbols2:
            if symbol in corr1 and symbol in corr2:
                # דמיון לפי קרבה בערכי קורלציה
                diff = abs(corr1[symbol] - corr2[symbol])
                corr_similarity += 1.0 - min(diff, 1.0)
                count += 1
        
        if count > 0:
            corr_similarity = corr_similarity / count
        
        # ממוצע משוקלל
        return (base_similarity * 0.6 + corr_similarity * 0.4)
    
    return base_similarity


def hash_params(lookback_days: int,
                forward_days: int,
                correlation_threshold: float,
                window_type: str) -> str:
    """
    יצירת hash מפרמטרים לקאש
    
    Args:
        lookback_days: ימים אחורה
        forward_days: ימים קדימה
        correlation_threshold: סף קורלציה
        window_type: סוג חלון
        
    Returns:
        MD5 hash string
    """
    params_str = json.dumps({
        'lookback_days': lookback_days,
        'forward_days': forward_days,
        'correlation_threshold': correlation_threshold,
        'window_type': window_type
    }, sort_keys=True)
    
    return hashlib.md5(params_str.encode()).hexdigest()


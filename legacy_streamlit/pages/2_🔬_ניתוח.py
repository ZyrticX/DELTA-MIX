"""
עמוד ניתוח קורלציה
"""

import streamlit as st
import pandas as pd
import os
import pickle
import time
from datetime import datetime
from correlation_engine import CorrelationEngine
from data_fetcher import DataFetcher
from utils import load_css, initialize_session_state

# טעינת CSS
load_css()

# אתחול session state
initialize_session_state()

# כותרת עמוד
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h1 style='color: #0066CC; margin-bottom: 2rem;'>🔬 ניתוח קורלציה</h1>
</div>
""", unsafe_allow_html=True)

def get_cached_stocks():
    """קבלת רשימת כל המניות שנמצאות בקאש"""
    cache_dir = "data_cache"
    stocks = []
    
    if not os.path.exists(cache_dir):
        return []
    
    for filename in os.listdir(cache_dir):
        if filename.endswith('.pkl') and not filename.startswith('SPY'):
            # חילוץ שם המניה מהקובץ (פורמט: SYMBOL_startdate_enddate.pkl)
            symbol = filename.split('_')[0]
            if symbol not in stocks:
                stocks.append(symbol)
    
    return sorted(stocks)

def load_data_from_cache():
    """טעינת נתונים מהקאש"""
    cache_dir = "data_cache"
    
    if not os.path.exists(cache_dir):
        return None, []
    
    # קבלת כל המניות בקאש
    symbols = get_cached_stocks()
    
    if not symbols:
        return None, []
    
    # ארגון קבצים לפי symbol - נקח את הקובץ האחרון לכל symbol
    symbol_files = {}
    for symbol in symbols:
        symbol_files[symbol] = []
        for filename in os.listdir(cache_dir):
            if filename.startswith(f"{symbol}_") and filename.endswith('.pkl'):
                filepath = os.path.join(cache_dir, filename)
                file_mtime = os.path.getmtime(filepath)
                symbol_files[symbol].append((filename, filepath, file_mtime))
        
        # מיון לפי תאריך עדכון - הקובץ האחרון ראשון
        symbol_files[symbol].sort(key=lambda x: x[2], reverse=True)
    
    if not any(symbol_files.values()):
        return None, []
    
    # טעינת נתונים - נקח את הקובץ האחרון לכל symbol
    all_data = {}
    loaded_symbols = []
    
    for symbol, files_list in symbol_files.items():
        if not files_list:
            continue
        
        # נקח את הקובץ האחרון
        filename, filepath, _ = files_list[0]
        
        try:
            with open(filepath, 'rb') as f:
                df = pickle.load(f)
            
            if df is not None and not df.empty:
                # בדיקת עמודות זמינות
                available_columns = df.columns.tolist()
                
                # מיפוי שמות עמודות
                column_mapping = {
                    'Close': ['Close', 'close', 'CLOSE'],
                    'Adj Close': ['Adj Close', 'AdjClose', 'Adj_Close', 'adj close', 'ADJ CLOSE'],
                    'Volume': ['Volume', 'volume', 'VOLUME', 'vol']
                }
                
                def find_column(possible_names):
                    for col_name in possible_names:
                        if col_name in available_columns:
                            return col_name
                    return None
                
                # טעינת Close
                close_col = find_column(column_mapping['Close'])
                if close_col:
                    all_data[(symbol, 'Close')] = df[close_col]
                    
                    # טעינת Adj Close (או Close אם אין)
                    adj_close_col = find_column(column_mapping['Adj Close'])
                    if adj_close_col:
                        all_data[(symbol, 'Adj Close')] = df[adj_close_col]
                    else:
                        all_data[(symbol, 'Adj Close')] = df[close_col]
                    
                    # טעינת Volume (או 0 אם אין)
                    volume_col = find_column(column_mapping['Volume'])
                    if volume_col:
                        all_data[(symbol, 'Volume')] = df[volume_col]
                    else:
                        all_data[(symbol, 'Volume')] = pd.Series(0, index=df.index)
                    
                    loaded_symbols.append(symbol)
        except Exception as e:
            continue
    
    if not all_data:
        return None, []
    
    # יצירת DataFrame משולב
    combined_df = pd.DataFrame(all_data)
    return combined_df, loaded_symbols

# בדיקת נתונים
if not st.session_state.data_loaded:
    # נסה לטעון מהקאש
    st.info("🔍 בודק נתונים בקאש...")
    
    stock_data, symbols = load_data_from_cache()
    
    if stock_data is not None and not stock_data.empty:
        # עדכון session state
        st.session_state.stock_data = stock_data
        st.session_state.data_loaded = True
        st.session_state.symbols = symbols
        
        st.success(f"""
        ✅ **הנתונים נטענו מהקאש בהצלחה!**
        - {len(symbols)} מניות
        - {len(stock_data)} ימי מסחר
        - תקופה: {stock_data.index.min().strftime('%Y-%m-%d')} עד {stock_data.index.max().strftime('%Y-%m-%d')}
        """)
        st.rerun()
    else:
        st.warning("⚠️ לא נמצאו נתונים בקאש")
        st.info("עבור לעמוד 'נתונים' כדי לטעון את הנתונים הנדרשים לניתוח.")
        st.stop()

# הגדרת פרמטרים
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>⚙️ פרמטרי ניתוח</h2>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h3 style='color: #0066CC; margin-bottom: 1rem;'>פרמטרי חישוב</h3>
    </div>
    """, unsafe_allow_html=True)
    
    block_length = st.slider(
        "אורך בלוק קורלציה (ימים)",
        min_value=5,
        max_value=30,
        value=15,
        help="מספר ימי המסחר לחישוב קורלציה גלילית"
    )
    
    significance = st.slider(
        "סף מובהקות",
        min_value=0.1,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="סף הקורלציה המינימלי (ערכים: 0-1)"
    )
    
    calc_mode = st.selectbox(
        "סוג חישוב",
        options=[1, 2, 3],
        index=2,
        format_func=lambda x: {
            1: "1 - קורלציית שער בלבד",
            2: "2 - קורלציית מחזור בלבד",
            3: "3 - מכפלת קורלציות (שער × מחזור)"
        }[x],
        help="שיטת חישוב הקורלציה"
    )

with col2:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h3 style='color: #0066CC; margin-bottom: 1rem;'>פרמטרים נוספים</h3>
    </div>
    """, unsafe_allow_html=True)
    
    ma_length = st.slider(
        "אורך ממוצע נע (ימים)",
        min_value=3,
        max_value=20,
        value=10,
        help="מספר ימים לחישוב ממוצע נע של נפח המסחר"
    )
    
    threshold = st.slider(
        "סף מהותיות (%)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
        help="סף אחוז מינימלי לזיהוי שינוי מהותי"
    ) / 100
    
    price_field = st.selectbox(
        "שדה מחיר לניתוח",
        options=['Close', 'Adj Close'],
        index=0,
        format_func=lambda x: {
            'Close': 'Close - מחיר סגירה',
            'Adj Close': 'Adj Close - מחיר סגירה מותאם'
        }[x],
        help="בחר איזה שדה מחיר להשתמש לחישוב קורלציות מחיר"
    )

st.markdown("---")

# אופציה לחישוב קורלציות לאורך זמן
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h3 style='color: #0066CC; margin-top: 1rem;'>⏱️ קורלציות לאורך זמן</h3>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    calculate_over_time = st.checkbox(
        "חשב קורלציות לאורך זמן (Rolling Correlation)",
        value=False,
        help="חישוב קורלציות גלילית לכל תאריך - מראה איך הקורלציות משתנות לאורך זמן"
    )

with col2:
    if calculate_over_time:
        rolling_window = st.number_input(
            "גודל חלון (ימים)",
            min_value=10,
            max_value=100,
            value=30,
            help="מספר ימים לחישוב הקורלציה הגלילית"
        )
    else:
        rolling_window = None

if calculate_over_time:
    st.info("""
    💡 **חישוב קורלציות לאורך זמן:**
    - לכל תאריך, המערכת תחשב קורלציה בין כל זוג מניות על בסיס החלון הנבחר
    - זה מאפשר לראות איך הקורלציות משתנות לאורך זמן
    - **שימו לב:** חישוב זה לוקח זמן רב יותר
    """)

# פרמטרים
params = {
    'block_length': block_length,
    'significance': significance,
    'calc_mode': calc_mode,
    'ma_length': ma_length,
    'threshold': threshold,
    'price_field': price_field,  # Close או Adj Close
    'start_date': datetime(2012, 1, 1).strftime("%Y-%m-%d"),
    'end_date': datetime.now().strftime("%Y-%m-%d"),
    'reference_symbol': 'SPY',
    'num_stocks': len(st.session_state.symbols) if st.session_state.symbols else 500
}

# הצגת סיכום פרמטרים
st.markdown("---")
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📋 סיכום פרמטרים</h2>
</div>
""", unsafe_allow_html=True)

st.info(f"""
⚙️ **פרמטרי ניתוח:**
- אורך בלוק: {params['block_length']} ימים
- סף מובהקות: {params['significance']}
- סוג חישוב: {params['calc_mode']}
- ממוצע נע: {params['ma_length']} ימים
- סף מהותיות: {params['threshold']*100:.1f}%
- שדה מחיר: {params['price_field']}

📊 **נתונים:**
- מספר מניות: {len(st.session_state.symbols) if st.session_state.symbols else 'לא נטען'}
- תקופה: {st.session_state.stock_data.index.min().strftime('%Y-%m-%d') if st.session_state.stock_data is not None else 'לא זמין'} עד {st.session_state.stock_data.index.max().strftime('%Y-%m-%d') if st.session_state.stock_data is not None else 'לא זמין'}
""")


# כפתור הרצת ניתוח 500×500
st.markdown("---")
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>🚀 הרצת ניתוח קורלציה 500×500</h2>
</div>
""", unsafe_allow_html=True)

st.info("""
💡 **המערכת תחשב קורלציות בין כל המניות**

📊 סה"כ חישובים: מספר מניות × מספר מניות

⏱️ זמן משוער: 5-10 דקות (תלוי במחשב ובמספר המניות)
""")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("▶️ הרץ ניתוח 500×500", use_container_width=True, type="primary"):
        # בדיקת נתונים
        if st.session_state.stock_data is None or st.session_state.stock_data.empty:
            st.error("❌ אין נתונים נטענים. יש לטעון נתונים קודם בעמוד 'נתונים'.")
            st.stop()
        
        # הכנות
        num_stocks = len(st.session_state.symbols)
        total_correlations = num_stocks * num_stocks
        
        st.markdown("---")
        st.markdown(f"""
        <div style='direction: rtl; text-align: right;'>
            <h3 style='color: #0066CC;'>🔄 מריץ חישוב...</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress Bar מספרי
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            counter_text = st.empty()
        
        time_start = time.time()
        
        try:
            # יצירת מנוע
            engine = CorrelationEngine(params)
            
            # חישוב מטריצות 500×500
            status_text.text("📊 שלב 1/3: מחשב קורלציות מחיר (Adj Close)...")
            counter_text.markdown(f"**חישובים: 0 / {total_correlations:,}**")
            progress_bar.progress(0)
            
            # חישוב קורלציות מחיר
            price_matrix_start = time.time()
            price_matrix = engine.calculate_full_correlation_matrix(
                st.session_state.stock_data,
                field='Adj Close'
            )
            price_matrix_time = time.time() - price_matrix_start
            
            # עדכון
            progress_bar.progress(33)
            counter_text.markdown(f"**חישובים: {total_correlations // 3:,} / {total_correlations:,}** ✅")
            
            # חישוב קורלציות נפח
            status_text.text("📊 שלב 2/3: מחשב קורלציות נפח (Volume)...")
            volume_matrix_start = time.time()
            volume_matrix = engine.calculate_full_correlation_matrix(
                st.session_state.stock_data,
                field='Volume'
            )
            volume_matrix_time = time.time() - volume_matrix_start
            
            # עדכון
            progress_bar.progress(66)
            counter_text.markdown(f"**חישובים: {total_correlations * 2 // 3:,} / {total_correlations:,}** ✅")
            
            # שילוב קורלציות
            status_text.text("📊 שלב 3/3: משלב קורלציות...")
            combine_start = time.time()
            
            # יצירת מטריצה משולבת לפי calc_mode
            if params['calc_mode'] == 1:
                # רק מחיר
                combined_matrix = price_matrix.copy()
            elif params['calc_mode'] == 2:
                # רק נפח
                combined_matrix = volume_matrix.copy()
            elif params['calc_mode'] == 3:
                # משולב - מכפלה רק אם שתיהן חיוביות
                combined_matrix = pd.DataFrame(
                    index=price_matrix.index,
                    columns=price_matrix.columns
                )
                
                for i in price_matrix.index:
                    for j in price_matrix.columns:
                        price_corr = price_matrix.loc[i, j]
                        volume_corr = volume_matrix.loc[i, j]
                        
                        if price_corr > 0 and volume_corr > 0:
                            combined_matrix.loc[i, j] = price_corr * volume_corr
                        else:
                            combined_matrix.loc[i, j] = 0
            
            combine_time = time.time() - combine_start
            
            # מציאת קורלציות גבוהות
            status_text.text("🔍 מוצא קורלציות גבוהות...")
            top_correlations = engine.find_top_correlations(combined_matrix, top_n=100)
            
            # חישוב קורלציות לאורך זמן (אם מסומן)
            if calculate_over_time:
                progress_bar.progress(70)
                status_text.text("⏱️ שלב 4/4: מחשב קורלציות לאורך זמן...")
                counter_text.markdown(f"**מחשב rolling correlations עם חלון של {rolling_window} ימים...**")
                
                rolling_start = time.time()
                
                # חישוב rolling correlations למחיר
                price_rolling = engine.calculate_rolling_correlation_over_time(
                    st.session_state.stock_data,
                    field='Adj Close',
                    window=rolling_window
                )
                
                # חישוב rolling correlations לנפח
                volume_rolling = engine.calculate_rolling_correlation_over_time(
                    st.session_state.stock_data,
                    field='Volume',
                    window=rolling_window
                )
                
                rolling_time = time.time() - rolling_start
                
                # שמירה
                st.session_state.price_rolling_correlations = price_rolling
                st.session_state.volume_rolling_correlations = volume_rolling
                st.session_state.rolling_window = rolling_window
            else:
                rolling_time = 0
                st.session_state.price_rolling_correlations = None
                st.session_state.volume_rolling_correlations = None
            
            # סיום
            total_time = time.time() - time_start
            progress_bar.progress(100)
            counter_text.markdown(f"**חישובים: {total_correlations:,} / {total_correlations:,}** ✅✅✅")
            status_text.text("✅ החישוב הושלם!")
            
            # שמירת תוצאות ב-session_state
            st.session_state.price_correlation_matrix = price_matrix
            st.session_state.volume_correlation_matrix = volume_matrix
            st.session_state.combined_correlation_matrix = combined_matrix
            st.session_state.top_correlations = top_correlations
            st.session_state.analysis_done = True
            st.session_state.engine = engine
            st.session_state.analysis_params = params.copy()
            st.session_state.analysis_timestamp = datetime.now()
            
            # הצגת סיכום
            summary_text = f"""
            ✅ **ניתוח 500×500 הושלם בהצלחה!**
            
            📊 **סטטיסטיקות:**
            - מטריצת קורלציות: {num_stocks} × {num_stocks} = {total_correlations:,} חישובים
            - אופציית ניתוח: {['', 'מחיר בלבד', 'נפח בלבד', 'משולב'][params['calc_mode']]}
            - שדה מחיר: {params['price_field']}
            """
            
            if calculate_over_time:
                summary_text += f"\n- קורלציות לאורך זמן: חלון של {rolling_window} ימים ✅"
            
            summary_text += f"""
            
            ⏱️ **זמני חישוב:**
            - קורלציות מחיר: {price_matrix_time:.2f} שניות
            - קורלציות נפח: {volume_matrix_time:.2f} שניות
            - שילוב: {combine_time:.2f} שניות
            """
            
            if calculate_over_time:
                summary_text += f"\n- קורלציות לאורך זמן: {rolling_time:.2f} שניות ({rolling_time/60:.2f} דקות)"
            
            summary_text += f"""
            - **סה"כ: {total_time:.2f} שניות ({total_time/60:.2f} דקות)**
            
            💾 **כל הנתונים נשמרו ב-session state**
            
            ➡️ **עבור לעמוד 'תוצאות' לצפייה בניתוח המלא**
            """
            
            st.success(summary_text)
            
            st.balloons()
            
            # כפתור מעבר לתוצאות
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("➡️ עבור לעמוד תוצאות", type="primary", use_container_width=True):
                    st.switch_page("pages/3_📈_תוצאות.py")
        
        except Exception as e:
            st.error(f"❌ שגיאה בחישוב: {str(e)}")
            import traceback
            with st.expander("פרטי שגיאה"):
                st.code(traceback.format_exc())


"""
עמוד ניתוח קורלציה
"""

import streamlit as st
import pandas as pd
import os
import pickle
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

# הגדרת מניית ייחוס
st.markdown("---")
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📊 מניית ייחוס</h2>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    reference_symbol = st.text_input(
        "סימול מניית ייחוס",
        value="SPY",
        help="מניית ייחוס לחישוב קורלציות (ברירת מחדל: SPY = S&P 500 ETF)"
    )
    
    reference_start_date = st.date_input(
        "תאריך התחלה למניית ייחוס",
        value=datetime(2012, 1, 1),
        min_value=datetime(2000, 1, 1),
        max_value=datetime.now(),
        help="תאריך התחלה להורדת נתוני מניית הייחוס"
    )

with col2:
    st.info("""
    **מניית ייחוס** משמשת כבסיס לחישוב הקורלציות.
    
    המניות יושוו למניית הייחוס כדי לזהות תנועות דומות.
    """)

# סקציה חדשה: ניתוח קורלציה מלא בין כל המניות
st.markdown("---")
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>🔗 ניתוח קורלציה מלא (כל המניות מול כל המניות)</h2>
</div>
""", unsafe_allow_html=True)

st.info("""
💡 **ניתוח קורלציה מלא** מחשב את הקורלציה בין כל המניות לבין כל המניות האחרות.
זה מאפשר לזהות מניות שתנועותיהן קשורות זו לזו, גם ללא מניית ייחוס.

**שימו לב:** חישוב זה יכול לקחת זמן עבור 500 מניות (250,000 קורלציות).
""")

col1, col2 = st.columns([2, 1])

with col1:
    full_analysis_field = st.selectbox(
        "שדה לניתוח קורלציה מלא",
        options=['Close', 'Adj Close', 'Volume'],
        index=0,
        format_func=lambda x: {
            'Close': 'Close - מחיר סגירה',
            'Adj Close': 'Adj Close - מחיר סגירה מותאם',
            'Volume': 'Volume - נפח מסחר'
        }[x],
        help="בחר איזה שדה להשתמש לחישוב הקורלציות"
    )
    
    use_rolling = st.checkbox(
        "השתמש בקורלציה גלילית",
        value=False,
        help="אם מסומן, יחושב ממוצע של קורלציות גליליות על חלון זמן"
    )
    
    if use_rolling:
        rolling_window = st.slider(
            "גודל חלון לקורלציה גלילית",
            min_value=5,
            max_value=30,
            value=15,
            help="מספר ימים לחלון הקורלציה הגלילית"
        )
    else:
        rolling_window = None
    
    top_n_correlations = st.number_input(
        "מספר הקורלציות הגבוהות ביותר להצגה",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        help="כמה מהקורלציות הגבוהות ביותר להציג בטבלה"
    )

with col2:
    st.markdown("""
    <div style='direction: rtl; text-align: right; margin-top: 2rem;'>
        <h4 style='color: #0066CC; margin-bottom: 1rem;'>פרמטרים</h4>
        <p style='color: #666; font-size: 0.9rem;'>
            בחר את השדה לניתוח ואת מספר הקורלציות הגבוהות ביותר שתרצה לראות.
        </p>
    </div>
    """, unsafe_allow_html=True)

if st.button("🔗 הרץ ניתוח קורלציה מלא", use_container_width=True, type="primary", key="run_full_correlation"):
    if st.session_state.stock_data is None or st.session_state.stock_data.empty:
        st.error("❌ אין נתונים נטענים. יש לטעון נתונים קודם.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # יצירת מנוע
            engine = CorrelationEngine(params)
            
            # חישוב מטריצת קורלציה
            status_text.text("🔗 מחשב מטריצת קורלציה מלאה...")
            progress_bar.progress(20)
            
            if use_rolling and rolling_window:
                correlation_matrix = engine.calculate_rolling_correlation_matrix(
                    st.session_state.stock_data,
                    field=full_analysis_field,
                    window=rolling_window
                )
            else:
                correlation_matrix = engine.calculate_full_correlation_matrix(
                    st.session_state.stock_data,
                    field=full_analysis_field
                )
            
            if correlation_matrix.empty:
                st.error("❌ לא ניתן לחשב מטריצת קורלציה")
            else:
                progress_bar.progress(60)
                status_text.text("🔍 מוצא קורלציות גבוהות...")
                
                # מציאת הקורלציות הגבוהות ביותר
                top_correlations = engine.find_top_correlations(
                    correlation_matrix,
                    top_n=top_n_correlations
                )
                
                progress_bar.progress(80)
                status_text.text("📊 מציג תוצאות...")
                
                # שמירה ב-session state
                st.session_state.full_correlation_matrix = correlation_matrix
                st.session_state.top_correlations = top_correlations
                st.session_state.full_analysis_field = full_analysis_field
                
                progress_bar.progress(100)
                status_text.text("✅ ניתוח קורלציה מלא הושלם!")
                
                # הצגת תוצאות
                st.markdown("---")
                st.markdown("""
                <div style='direction: rtl; text-align: right;'>
                    <h3 style='color: #0066CC; margin-top: 1rem; margin-bottom: 1rem;'>📊 תוצאות ניתוח קורלציה מלא</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.success(f"""
                ✅ **ניתוח הושלם בהצלחה!**
                - מטריצת קורלציה: {len(correlation_matrix)} × {len(correlation_matrix)} מניות
                - סה"כ קורלציות: {len(correlation_matrix) * (len(correlation_matrix) - 1) // 2}
                - שדה נותח: {full_analysis_field}
                """)
                
                # הצגת הקורלציות הגבוהות ביותר
                st.markdown("""
                <div style='direction: rtl; text-align: right;'>
                    <h4 style='color: #0066CC; margin-top: 1rem; margin-bottom: 1rem;'>🏆 הקורלציות הגבוהות ביותר</h4>
                </div>
                """, unsafe_allow_html=True)
                
                st.dataframe(top_correlations, use_container_width=True, height=400)
                
                # הורדת תוצאות
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    # הורדת טבלת קורלציות גבוהות
                    csv_top = top_correlations.to_csv(index=False)
                    st.download_button(
                        "📥 הורד קורלציות גבוהות (CSV)",
                        csv_top,
                        f"top_correlations_{full_analysis_field}_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    # הורדת מטריצת קורלציה מלאה
                    csv_matrix = correlation_matrix.to_csv()
                    st.download_button(
                        "📥 הורד מטריצת קורלציה מלאה (CSV)",
                        csv_matrix,
                        f"correlation_matrix_{full_analysis_field}_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                
                # הצגת heatmap (אם יש plotly)
                try:
                    import plotly.graph_objects as go
                    import plotly.express as px
                    
                    st.markdown("""
                    <div style='direction: rtl; text-align: right;'>
                        <h4 style='color: #0066CC; margin-top: 1rem; margin-bottom: 1rem;'>📈 Heatmap של מטריצת קורלציה</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # יצירת heatmap
                    fig = px.imshow(
                        correlation_matrix.values,
                        labels=dict(x="מניה", y="מניה", color="קורלציה"),
                        x=correlation_matrix.columns,
                        y=correlation_matrix.index,
                        color_continuous_scale="RdBu",
                        aspect="auto"
                    )
                    
                    fig.update_layout(
                        title=f"מטריצת קורלציה - {full_analysis_field}",
                        height=800,
                        width=1000
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.info("💡 Heatmap זמין רק עם plotly מותקן")
        
        except Exception as e:
            st.error(f"❌ שגיאה בניתוח קורלציה מלא: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# כפתור הרצת ניתוח רגיל
st.markdown("---")
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📊 ניתוח רגיל (מול מניית ייחוס)</h2>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("▶️ הרץ ניתוח", use_container_width=True, type="primary", key="run_analysis"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # שלב 1: הורדת מניית ייחוס
            status_text.text(f"📥 מוריד נתוני מניית ייחוס ({reference_symbol})...")
            progress_bar.progress(10)
            
            fetcher = DataFetcher()
            reference_data = fetcher.get_reference_stock_data(
                reference_symbol,
                start_date=reference_start_date.strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            if reference_data is None:
                st.error(f"❌ לא ניתן להוריד נתוני מניית ייחוס ({reference_symbol})")
                st.stop()
            
            # שמירת reference_data ב-session state
            st.session_state.reference_data = reference_data
            st.session_state.reference_symbol = reference_symbol
            
            # שלב 2: יצירת המנוע
            status_text.text("🔧 מאתחל מנוע חישוב...")
            progress_bar.progress(30)
            
            engine = CorrelationEngine(params)
            
            # שלב 3: הרצת הניתוח
            status_text.text("🔬 מריץ ניתוח מלא...")
            progress_bar.progress(50)
            
            results = engine.run_full_analysis(
                st.session_state.stock_data,
                reference_data['price'],
                reference_data['volume']
            )
            
            # שמירת תוצאות
            st.session_state.results = results
            st.session_state.analysis_done = True
            st.session_state.engine = engine
            
            progress_bar.progress(100)
            status_text.text("✅ הניתוח הושלם!")
            
            st.success("✅ הניתוח הושלם בהצלחה! עבור לעמוד 'תוצאות' כדי לראות את התוצאות.")
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ שגיאה בניתוח: {str(e)}")
            import traceback
            with st.expander("פרטי שגיאה"):
                st.code(traceback.format_exc())

# הצגת סטטוס
if st.session_state.analysis_done:
    st.markdown("---")
    st.success("✅ ניתוח הושלם בהצלחה! עבור לעמוד 'תוצאות' כדי לראות את התוצאות המפורטות.")


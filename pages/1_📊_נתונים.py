"""
עמוד ניהול נתונים
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pickle
from data_fetcher import DataFetcher
from utils import load_css, initialize_session_state

# טעינת CSS
load_css()

# אתחול session state
initialize_session_state()

# כותרת עמוד
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h1 style='color: #0066CC; margin-bottom: 2rem;'>📊 ניהול נתונים</h1>
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

def get_stock_info(symbol):
    """קבלת מידע על מניה מהקאש"""
    cache_dir = "data_cache"
    info = {
        'symbol': symbol,
        'files': [],
        'date_range': None,
        'total_days': 0
    }
    
    if not os.path.exists(cache_dir):
        return info
    
    for filename in os.listdir(cache_dir):
        if filename.startswith(f"{symbol}_") and filename.endswith('.pkl'):
            filepath = os.path.join(cache_dir, filename)
            file_date = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            # חילוץ תאריכים מהשם
            parts = filename.replace('.pkl', '').split('_')
            if len(parts) >= 3:
                start_date = parts[1]
                end_date = parts[2]
                
                info['files'].append({
                    'filename': filename,
                    'start_date': start_date,
                    'end_date': end_date,
                    'modified': file_date,
                    'size': os.path.getsize(filepath)
                })
    
    if info['files']:
        # מציאת טווח התאריכים הכולל
        all_starts = [f['start_date'] for f in info['files']]
        all_ends = [f['end_date'] for f in info['files']]
        info['date_range'] = f"{min(all_starts)} עד {max(all_ends)}"
        
        # חישוב מספר ימים כולל
        try:
            with open(os.path.join(cache_dir, info['files'][0]['filename']), 'rb') as f:
                df = pickle.load(f)
                info['total_days'] = len(df)
        except:
            pass
    
    return info

# סקציה 1: רשימת מניות בקאש
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📋 מניות במאגר הנתונים</h2>
</div>
""", unsafe_allow_html=True)

cached_stocks = get_cached_stocks()

if cached_stocks:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"נמצאו **{len(cached_stocks)}** מניות במאגר הנתונים")
    
    with col2:
        if st.button("🔄 רענן רשימה", use_container_width=True):
            st.rerun()
    
    # חיפוש וסינון
    search_term = st.text_input("🔍 חפש מניה", "", key="search_data")
    
    if search_term:
        cached_stocks = [s for s in cached_stocks if search_term.upper() in s.upper()]
    
    # הצגת טבלה
    stocks_data = []
    for symbol in cached_stocks:
        info = get_stock_info(symbol)
        stocks_data.append({
            'מניה': symbol,
            'טווח תאריכים': info['date_range'] or 'לא זמין',
            'מספר ימים': info['total_days'],
            'מספר קבצים': len(info['files'])
        })
    
    if stocks_data:
        df_stocks = pd.DataFrame(stocks_data)
        st.dataframe(df_stocks, use_container_width=True, height=400)
        
        # הורדת רשימה
        csv = df_stocks.to_csv(index=False)
        st.download_button(
            "📥 הורד רשימת מניות (CSV)",
            csv,
            f"stocks_list_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
else:
    st.warning("⚠️ לא נמצאו מניות במאגר הנתונים. יש לטעון נתונים קודם.")

st.markdown("---")

# סקציה 2: טעינת נתונים
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📥 טעינת נתונים</h2>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h3 style='color: #0066CC; margin-bottom: 1rem;'>הגדרות טעינה</h3>
    </div>
    """, unsafe_allow_html=True)
    
    start_date = st.date_input(
        "תאריך התחלה",
        value=datetime(2012, 1, 1),
        min_value=datetime(2000, 1, 1),
        max_value=datetime.now()
    )
    
    end_date = st.date_input(
        "תאריך סיום",
        value=datetime.now(),
        min_value=datetime(2000, 1, 1),
        max_value=datetime.now()
    )
    
    reference_symbol = st.text_input(
        "מניית ייחוס",
        value="SPY",
        help="סימול מניית הייחוס (ברירת מחדל: SPY = S&P 500 ETF)"
    )
    
    num_stocks = st.number_input(
        "מספר מניות מ-S&P 500",
        min_value=10,
        max_value=500,
        value=500,
        step=10,
        help="מספר המניות להורדה"
    )

with col2:
    st.markdown("""
    <div style='direction: rtl; text-align: right; margin-top: 3rem;'>
        <h3 style='color: #0066CC; margin-bottom: 1rem;'>פעולות</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 טען נתונים", use_container_width=True, type="primary"):
        fetcher = DataFetcher()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # שלב 1: קבלת רשימת מניות
            status_text.text("🔍 מקבל רשימת מניות S&P 500...")
            progress_bar.progress(10)
            
            symbols = fetcher.get_sp500_symbols()
            symbols = symbols[:num_stocks]
            
            # שלב 2: הורדת נתוני מניות
            status_text.text(f"📥 מוריד נתונים עבור {len(symbols)} מניות...")
            progress_bar.progress(30)
            
            stock_data = fetcher.download_multiple_stocks(
                symbols,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            if stock_data is None or stock_data.empty:
                st.error("❌ כשלון בהורדת נתוני מניות")
            else:
                # שלב 3: הורדת מניית ייחוס
                status_text.text("📥 מוריד נתוני מניית ייחוס...")
                progress_bar.progress(70)
                
                reference_data = fetcher.get_reference_stock_data(
                    reference_symbol,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )
                
                if reference_data is None:
                    st.warning(f"⚠️ לא ניתן להוריד נתוני {reference_symbol}")
                else:
                    # שמירה ב-session state
                    st.session_state.stock_data = stock_data
                    st.session_state.reference_data = reference_data
                    st.session_state.data_loaded = True
                    st.session_state.symbols = symbols
                    
                    progress_bar.progress(100)
                    status_text.text("✅ הנתונים נטענו בהצלחה!")
                    
                    st.success(f"""
                    ✅ **הנתונים נטענו בהצלחה!**
                    - {len(symbols)} מניות
                    - {len(stock_data)} ימי מסחר
                    - תקופה: {stock_data.index.min().strftime('%Y-%m-%d')} עד {stock_data.index.max().strftime('%Y-%m-%d')}
                    """)
                    
                    st.rerun()
        
        except Exception as e:
            st.error(f"❌ שגיאה בטעינת נתונים: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

st.markdown("---")

# סקציה 3: עדכון נתונים
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>🔄 עדכון נתונים</h2>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.info("""
    עדכון נתונים יוריד את הנתונים החדשים ביותר עבור כל המניות שנמצאות בקאש.
    הנתונים הקיימים ישמרו ויתווספו אליהם הנתונים החדשים.
    """)
    
    update_days = st.number_input(
        "מספר ימים לעדכון",
        min_value=1,
        max_value=365,
        value=30,
        help="מספר הימים האחרונים לעדכון"
    )

with col2:
    if st.button("🔄 עדכן נתונים", use_container_width=True, type="primary"):
        cached_stocks = get_cached_stocks()
        
        if not cached_stocks:
            st.warning("⚠️ אין מניות לעדכון. יש לטעון נתונים קודם.")
        else:
            fetcher = DataFetcher()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                from datetime import timedelta
                end_date = datetime.now()
                start_date = datetime.now() - timedelta(days=update_days)
                
                status_text.text(f"🔄 מעדכן {len(cached_stocks)} מניות...")
                
                updated_count = 0
                for i, symbol in enumerate(cached_stocks):
                    progress_bar.progress((i + 1) / len(cached_stocks))
                    
                    try:
                        df = fetcher.download_stock_data(
                            symbol,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            use_cache=False
                        )
                        if df is not None and not df.empty:
                            updated_count += 1
                    except:
                        pass
                
                st.success(f"✅ עודכנו {updated_count} מתוך {len(cached_stocks)} מניות")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ שגיאה בעדכון: {str(e)}")

st.markdown("---")

# סקציה 4: עדכון מניות
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>➕ עדכון רשימת מניות</h2>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["הוסף מניות", "הסר מניות"])

with tab1:
    st.markdown("""
    <div style='direction: rtl; text-align: right; margin-bottom: 1rem;'>
        הוסף מניות חדשות למאגר הנתונים
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_symbols_input = st.text_area(
            "רשימת מניות (מופרדות בפסיק או שורה חדשה)",
            placeholder="AAPL, MSFT, GOOGL\nאו\nAAPL\nMSFT\nGOOGL",
            height=150
        )
        
        start_date_add = st.date_input(
            "תאריך התחלה",
            value=datetime(2012, 1, 1),
            key="add_start_date"
        )
        
        end_date_add = st.date_input(
            "תאריך סיום",
            value=datetime.now(),
            key="add_end_date"
        )
    
    with col2:
        if st.button("➕ הוסף מניות", use_container_width=True, type="primary"):
            if new_symbols_input:
                # פרסור רשימת מניות
                symbols_list = []
                for line in new_symbols_input.replace(',', '\n').split('\n'):
                    symbol = line.strip().upper()
                    if symbol:
                        symbols_list.append(symbol)
                
                if symbols_list:
                    fetcher = DataFetcher()
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        added_count = 0
                        for i, symbol in enumerate(symbols_list):
                            progress_bar.progress((i + 1) / len(symbols_list))
                            status_text.text(f"מוריד {symbol}...")
                            
                            try:
                                df = fetcher.download_stock_data(
                                    symbol,
                                    start_date=start_date_add.strftime("%Y-%m-%d"),
                                    end_date=end_date_add.strftime("%Y-%m-%d"),
                                    use_cache=False
                                )
                                if df is not None and not df.empty:
                                    added_count += 1
                            except Exception as e:
                                st.warning(f"⚠️ שגיאה בהורדת {symbol}: {str(e)}")
                        
                        st.success(f"✅ נוספו {added_count} מתוך {len(symbols_list)} מניות")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ שגיאה: {str(e)}")
                else:
                    st.warning("⚠️ לא נמצאו מניות תקינות")
            else:
                st.warning("⚠️ יש להזין רשימת מניות")

with tab2:
    st.markdown("""
    <div style='direction: rtl; text-align: right; margin-bottom: 1rem;'>
        הסר מניות מהמאגר הנתונים
    </div>
    """, unsafe_allow_html=True)
    
    cached_stocks = get_cached_stocks()
    
    if cached_stocks:
        selected_to_remove = st.multiselect(
            "בחר מניות להסרה",
            options=cached_stocks,
            help="בחר את המניות שברצונך להסיר מהמאגר"
        )
        
        if selected_to_remove:
            if st.button("🗑️ הסר מניות נבחרות", use_container_width=True, type="primary"):
                cache_dir = "data_cache"
                removed_count = 0
                
                if os.path.exists(cache_dir):
                    for symbol in selected_to_remove:
                        for filename in os.listdir(cache_dir):
                            if filename.startswith(f"{symbol}_") and filename.endswith('.pkl'):
                                try:
                                    os.remove(os.path.join(cache_dir, filename))
                                    removed_count += 1
                                except:
                                    pass
                
                st.success(f"✅ הוסרו {removed_count} קבצים עבור {len(selected_to_remove)} מניות")
                st.rerun()
    else:
        st.info("ℹ️ אין מניות במאגר להסרה")

st.markdown("---")

# סקציה 5: ניקוי קאש
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>🗑️ ניהול קאש</h2>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    cache_dir = "data_cache"
    if os.path.exists(cache_dir):
        try:
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.pkl')]
            st.metric("מספר קבצים", len(cache_files))
        except:
            st.metric("מספר קבצים", 0)
    else:
        st.metric("מספר קבצים", 0)

with col2:
    cache_dir = "data_cache"
    if os.path.exists(cache_dir):
        try:
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.pkl')]
            cache_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in cache_files) / (1024 * 1024)
            st.metric("גודל קאש", f"{cache_size:.2f} MB")
        except:
            st.metric("גודל קאש", "0 MB")
    else:
        st.metric("גודל קאש", "0 MB")

with col3:
    if st.button("🗑️ נקה כל הקאש", use_container_width=True):
        fetcher = DataFetcher()
        fetcher.clear_cache()
        st.success("✅ הקאש נוקה בהצלחה!")
        st.rerun()


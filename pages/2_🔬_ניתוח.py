"""
עמוד ניתוח קורלציה
"""

import streamlit as st
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

# בדיקת נתונים
if not st.session_state.data_loaded:
    st.warning("⚠️ יש לטעון נתונים קודם בעמוד 'נתונים'")
    st.info("עבור לעמוד נתונים כדי לטעון את הנתונים הנדרשים לניתוח.")
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

# פרמטרים
params = {
    'block_length': block_length,
    'significance': significance,
    'calc_mode': calc_mode,
    'ma_length': ma_length,
    'threshold': threshold,
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

📊 **נתונים:**
- מספר מניות: {len(st.session_state.symbols) if st.session_state.symbols else 'לא נטען'}
- תקופה: {st.session_state.stock_data.index.min().strftime('%Y-%m-%d') if st.session_state.stock_data is not None else 'לא זמין'} עד {st.session_state.stock_data.index.max().strftime('%Y-%m-%d') if st.session_state.stock_data is not None else 'לא זמין'}
""")

# כפתור הרצת ניתוח
st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("▶️ הרץ ניתוח", use_container_width=True, type="primary", key="run_analysis"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # יצירת המנוע
            status_text.text("🔧 מאתחל מנוע חישוב...")
            progress_bar.progress(10)
            
            engine = CorrelationEngine(params)
            
            # הרצת הניתוח
            status_text.text("🔬 מריץ ניתוח מלא...")
            progress_bar.progress(30)
            
            results = engine.run_full_analysis(
                st.session_state.stock_data,
                st.session_state.reference_data['price'],
                st.session_state.reference_data['volume']
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


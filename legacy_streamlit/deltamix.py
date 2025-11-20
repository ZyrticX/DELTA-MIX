"""
עמוד ראשי - DeltaMix
"""

import streamlit as st
from utils import load_css, initialize_session_state

# הגדרות עמוד ראשי
st.set_page_config(
    page_title="DeltaMix - CorrelationSystem",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "DeltaMix-CorrelationSystem - זיהוי הזדמנויות מסחר"
    }
)

# טעינת CSS
load_css()

# אתחול session state
initialize_session_state()

# כותרת ראשית
st.markdown("""
<div style='direction: rtl; text-align: right; margin-bottom: 2rem;'>
    <h1 style='color: #0066CC; font-size: 3rem; margin-bottom: 0.5rem;'>DeltaMix</h1>
    <h2 style='color: #0066CC; font-size: 1.8rem;'>מערכת ניתוח קורלציות S&P 500</h2>
</div>
""", unsafe_allow_html=True)

# תיאור המערכת
st.markdown("### ברוכים הבאים!")

st.write("""
**DeltaMix** היא מערכת מתקדמת לניתוח קורלציות בין מניות ל-S&P 500, זיהוי הזדמנויות מסחר, ועדכון אוטומטי יומי.
""")

st.markdown("---")

# סטטוס נוכחי
st.markdown("### 📊 סטטוס נוכחי")

col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.data_loaded:
        st.success("✅ נתונים נטענו")
        if st.session_state.symbols:
            st.info(f"📊 {len(st.session_state.symbols)} מניות")
    else:
        st.warning("⚠️ אין נתונים נטענים")

with col2:
    if st.session_state.analysis_done:
        st.success("✅ ניתוח הושלם")
        if st.session_state.results is not None:
            stats = st.session_state.results['statistics']
            st.info(f"📈 {len(stats)} מניות נותחו")
    else:
        st.info("ℹ️ ניתוח לא הושלם")

with col3:
    if st.session_state.data_loaded and st.session_state.analysis_done:
        st.success("🚀 מוכן לשימוש מלא")
    elif st.session_state.data_loaded:
        st.info("📥 מוכן לניתוח")
    else:
        st.info("📊 התחל בטעינת נתונים")

st.markdown("---")

# הפניות לכל העמודים
st.markdown("### 🗺️ ניווט במערכת")

st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h3 style='color: #0066CC; margin-top: 1.5rem; margin-bottom: 1rem;'>עמודים זמינים:</h3>
</div>
""", unsafe_allow_html=True)

# עמוד נתונים

with st.container():
    st.markdown("""
    <div style='direction: rtl; text-align: right; padding: 1rem; background-color: #F0F8FF; border-radius: 10px; border-right: 4px solid #0066CC; margin-bottom: 1rem;'>
        <h4 style='color: #0066CC; margin-bottom: 0.5rem;'>📊 נתונים</h4>
        <p style='margin: 0; color: #333;'>
            ניהול וטעינת נתוני מניות. כאן תוכל להוריד נתונים, לעדכן מניות קיימות, להוסיף או להסיר מניות מהמאגר.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_📊_נתונים.py", label="👉 עבור לעמוד נתונים", icon="📊")

# עמוד ניתוח
with st.container():
    st.markdown("""
    <div style='direction: rtl; text-align: right; padding: 1rem; background-color: #F0F8FF; border-radius: 10px; border-right: 4px solid #0066CC; margin-bottom: 1rem;'>
        <h4 style='color: #0066CC; margin-bottom: 0.5rem;'>🔬 ניתוח</h4>
        <p style='margin: 0; color: #333;'>
            הגדרת פרמטרי הניתוח והרצת ניתוח קורלציה. כאן תוכל לשנות את כל הפרמטרים ולהריץ את החישובים.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_🔬_ניתוח.py", label="👉 עבור לעמוד ניתוח", icon="🔬")

# עמוד תוצאות
with st.container():
    st.markdown("""
    <div style='direction: rtl; text-align: right; padding: 1rem; background-color: #F0F8FF; border-radius: 10px; border-right: 4px solid #0066CC; margin-bottom: 1rem;'>
        <h4 style='color: #0066CC; margin-bottom: 0.5rem;'>📈 תוצאות</h4>
        <p style='margin: 0; color: #333;'>
            צפייה בתוצאות הניתוח, גרפים והזדמנויות מסחר. כאן תראה את כל התוצאות המפורטות והורדות.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_📈_תוצאות.py", label="👉 עבור לעמוד תוצאות", icon="📈")

# עמוד טכני
with st.container():
    st.markdown("""
    <div style='direction: rtl; text-align: right; padding: 1rem; background-color: #F0F8FF; border-radius: 10px; border-right: 4px solid #0066CC; margin-bottom: 1rem;'>
        <h4 style='color: #0066CC; margin-bottom: 0.5rem;'>⚙️ מערך טכני</h4>
        <p style='margin: 0; color: #333;'>
            מידע טכני על המערכת - ארכיטקטורה, ספריות, פונקציות, אלגוריתמים וביצועים. מיועד למפתחים.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_⚙️_טכני.py", label="👉 עבור לעמוד טכני", icon="⚙️")

# עמוד עדכונים
with st.container():
    st.markdown("""
    <div style='direction: rtl; text-align: right; padding: 1rem; background-color: #F0F8FF; border-radius: 10px; border-right: 4px solid #0066CC; margin-bottom: 1rem;'>
        <h4 style='color: #0066CC; margin-bottom: 0.5rem;'>🔄 עדכונים</h4>
        <p style='margin: 0; color: #333;'>
            עדכונים על המערכת, שינויים בגרסאות ותכונות חדשות.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/5_🔄_עדכונים.py", label="👉 עבור לעמוד עדכונים", icon="🔄")

# עמוד אודות
with st.container():
    st.markdown("""
    <div style='direction: rtl; text-align: right; padding: 1rem; background-color: #F0F8FF; border-radius: 10px; border-right: 4px solid #0066CC; margin-bottom: 1rem;'>
        <h4 style='color: #0066CC; margin-bottom: 0.5rem;'>📖 אודות</h4>
        <p style='margin: 0; color: #333;'>
            הסבר מפורט על המערכת - מה היא עושה, איך היא עובדת, פרמטרים ותפעול. מומלץ למתחילים.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/6_📖_אודות.py", label="👉 עבור לעמוד אודות", icon="📖")

st.markdown("---")

# הוראות שימוש מהירות
st.markdown("### 🚀 התחלה מהירה")

st.write("""
1. **טען נתונים** - עבור לעמוד "📊 נתונים" וטען את הנתונים הנדרשים
2. **הגדר פרמטרים** - עבור לעמוד "🔬 ניתוח" והגדר את פרמטרי החישוב
3. **הרץ ניתוח** - לחץ על "▶️ הרץ ניתוח" והמתן לסיום החישובים
4. **צפה בתוצאות** - עבור לעמוד "📈 תוצאות" כדי לראות את כל התוצאות והגרפים
""")

st.markdown("---")

# כותרת תחתונה
st.markdown("""
<div style='text-align: center; color: #0066CC; padding: 1rem; direction: rtl;'>
    נבנתה ע"י SmartMindsAI - Ilya & Evgeniy
</div>
""", unsafe_allow_html=True)

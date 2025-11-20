"""
עמוד מבוא - Deltamix-CorrelationSystem
"""

import streamlit as st
from utils import load_css, initialize_session_state

# טעינת CSS
load_css()

# אתחול session state
initialize_session_state()

# כותרת ראשית
st.markdown("""
<div style='direction: rtl; text-align: right; margin-bottom: 2rem;'>
    <h1 style='color: #0066CC; font-size: 2.5rem; margin-bottom: 0.5rem;'>📊 מבוא</h1>
    <h2 style='color: #0066CC; font-size: 1.8rem;'>Deltamix-CorrelationSystem</h2>
</div>
""", unsafe_allow_html=True)

# תיאור המערכת
st.markdown("### ברוכים הבאים!")

st.write("""
מערכת מתקדמת לניתוח קורלציות בין מניות ל-S&P 500, זיהוי הזדמנויות מסחר, ועדכון אוטומטי יומי.
""")

st.markdown("**המערכת מחולקת לשלושה עמודים עיקריים:**")

st.markdown("""
- **📊 נתונים** - ניהול וטעינת נתוני מניות
- **🔬 ניתוח** - הרצת ניתוח קורלציה עם פרמטרים מותאמים  
- **📈 תוצאות** - צפייה בתוצאות הניתוח, גרפים והזדמנויות
""")

st.markdown("---")

# סטטוס נוכחי
st.markdown("### 📊 סטטוס נוכחי")

col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.data_loaded:
        st.success("✅ נתונים נטענו")
        if st.session_state.stock_data is not None:
            st.info(f"📊 {len(st.session_state.symbols) if st.session_state.symbols else 'N/A'} מניות")
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

# הוראות שימוש
st.markdown("### 🚀 התחלה מהירה")

st.markdown("""
1. **עבור לעמוד "📊 נתונים"** - טען את הנתונים הנדרשים או בדוק את המניות הקיימות במאגר
2. **עבור לעמוד "🔬 ניתוח"** - הגדר את פרמטרי הניתוח והרץ את הניתוח
3. **עבור לעמוד "📈 תוצאות"** - צפה בתוצאות המפורטות, גרפים והזדמנויות מסחר
""")

st.markdown("---")

# כותרת תחתונה
st.markdown("""
<div style='text-align: center; color: #0066CC; padding: 1rem; direction: rtl;'>
    נבנתה ע"י SmartMindsAI - Ilya & Evgeniy
</div>
""", unsafe_allow_html=True)


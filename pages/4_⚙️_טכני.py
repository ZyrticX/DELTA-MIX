"""
עמוד טכני - מערך טכני של המערכת
"""

import streamlit as st
from utils import load_css, initialize_session_state

# טעינת CSS
load_css()

# אתחול session state
initialize_session_state()

# כותרת עמוד
st.title("⚙️ מערך טכני")

# סקציה 1: ארכיטקטורה
st.header("🏗️ ארכיטקטורת המערכת")

st.write("""
המערכת בנויה במודולריות מלאה עם הפרדה ברורה בין שכבות:
- **ממשק משתמש (UI):** Streamlit - עמודים מרובים
- **שכבת נתונים:** DataFetcher - הורדה וניהול נתונים
- **שכבת חישוב:** CorrelationEngine - מנוע החישוב
- **שכבת עזר:** Utils - פונקציות משותפות
- **עדכון אוטומטי:** DailyUpdate - סקריפט עדכון יומי
""")

st.markdown("---")

# סקציה 2: ספריות וטכנולוגיות
st.header("📚 ספריות וטכנולוגיות")

col1, col2 = st.columns(2)

with col1:
    st.subheader("ספריות עיקריות")
    st.write("""
    - **yfinance:** הורדת נתונים מ-Yahoo Finance
    - **pandas:** ניהול וטיפול בנתונים
    - **numpy:** חישובים מתמטיים
    - **streamlit:** ממשק משתמש
    - **plotly:** גרפים אינטראקטיביים
    - **scipy:** חישובים סטטיסטיים
    """)

with col2:
    st.subheader("גרסאות מינימליות")
    st.write("""
    - yfinance >= 0.2.40
    - pandas >= 2.0.0
    - numpy >= 1.24.0
    - streamlit >= 1.30.0
    - plotly >= 5.18.0
    - scipy >= 1.11.0
    """)

st.markdown("---")

# סקציה 3: מבנה קבצים
st.header("📁 מבנה הקבצים")

st.code("""
project/
│
├── deltamix.py                 # קובץ ראשי - עמוד DeltaMix
├── correlation_engine.py      # מנוע החישוב
├── data_fetcher.py            # הורדת נתונים
├── daily_update.py            # עדכון אוטומטי יומי
├── utils.py                   # פונקציות עזר משותפות
├── requirements.txt           # רשימת חבילות
│
├── pages/                     # עמודי המערכת
│   ├── 0_📖_אודות.py         # עמוד הסבר
│   ├── 1_📊_נתונים.py        # ניהול נתונים
│   ├── 2_🔬_ניתוח.py         # הרצת ניתוח
│   ├── 3_📈_תוצאות.py        # תוצאות וגרפים
│   └── 4_⚙️_טכני.py          # מערך טכני
│
├── data_cache/                # קאש של נתונים
│   └── *.pkl                  # קבצי נתונים מוטמנים
│
└── daily_results/             # תוצאות יומיות
    ├── opportunities_*.json
    └── statistics_*.csv
""", language="text")

st.markdown("---")

# סקציה 4: פונקציות עיקריות
st.header("🔧 פונקציות עיקריות")

st.subheader("📥 DataFetcher (data_fetcher.py)")
st.write("""
- `get_sp500_symbols()` - קבלת רשימת מניות S&P 500 מוויקיפדיה
- `download_stock_data()` - הורדת נתוני מניה מ-Yahoo Finance
- `download_multiple_stocks()` - הורדת מספר מניות במקביל
- `get_reference_stock_data()` - הורדת מניית ייחוס (SPY)
- `clear_cache()` - ניקוי קאש
""")

st.subheader("🔬 CorrelationEngine (correlation_engine.py)")
st.write("""
- `calculate_rolling_correlation()` - חישוב קורלציה גלילית
- `calculate_sheet_correlations()` - חישוב קורלציות שער ומחזור
- `combine_correlations()` - שילוב קורלציות לפי מצב חישוב
- `calculate_volume_ratio()` - חישוב יחס מחזור לממוצע נע
- `filter_opportunities()` - סינון וזיהוי הזדמנויות
- `analyze()` - פונקציה ראשית להרצת כל הניתוח
""")

st.subheader("🛠️ Utils (utils.py)")
st.write("""
- `load_css()` - טעינת CSS משותף עם תמיכה ב-RTL
- `initialize_session_state()` - אתחול משתני session state
""")

st.markdown("---")

# סקציה 5: אלגוריתם החישוב
st.header("🧮 אלגוריתם החישוב")

st.write("""
**שלבי החישוב:**

1. **חישוב קורלציות גליליות:**
   עבור כל מניה, חישוב קורלציית Pearson בין 15 מחירים אחרונים של המניה 
   ל-15 מחירים אחרונים של SPY. אותו הדבר עבור נפחי המסחר.

2. **שילוב קורלציות:**
   לפי מצב החישוב (1/2/3) - שימוש בקורלציית שער, מחזור, או מכפלת שניהם.

3. **חישוב יחס מחזור:**
   עבור ימים שבהם הקורלציה > סף מובהקות, חישוב יחס בין ממוצע נע של 10 ימים 
   לנפח הנוכחי.

4. **זיהוי הזדמנויות:**
   ימים שבהם היחס > (1 + סף מהותיות) מסומנים כ-UP, 
   ימים אחרים עם קורלציה חיובית מסומנים כ-DOWN.

5. **סיכום סטטיסטי:**
   ספירת מספר ימי UP, DOWN, וסה"כ ימים כשירים לכל מניה.
""")

st.markdown("---")

# סקציה 6: ביצועים ואופטימיזציה
st.header("⚡ ביצועים ואופטימיזציה")

col1, col2 = st.columns(2)

with col1:
    st.subheader("מנגנוני אופטימיזציה")
    st.write("""
    - **קאש:** שמירת נתונים ב-pickle
    - **Parallel Processing:** הורדה מקבילית של מניות
    - **Vectorization:** שימוש ב-numpy/pandas
    - **Lazy Loading:** טעינת נתונים רק כשצריך
    """)

with col2:
    st.subheader("זמני ביצוע משוערים")
    st.write("""
    - **50 מניות:** ~2-3 דקות
    - **100 מניות:** ~5-7 דקות
    - **500 מניות:** ~20-30 דקות
    - **עם קאש:** פי 100 יותר מהיר
    """)

st.markdown("---")

# סקציה 7: אבטחה ופרטיות
st.header("🔐 אבטחה ופרטיות")

st.success("""
- ✅ הנתונים נשמרים **רק במחשב שלך**
- ✅ אין העברת מידע לשרתים חיצוניים
- ✅ Yahoo Finance API הוא ציבורי וחינמי
- ⚠️ אל תשתף את `config.json` אם יש בו פרטי email
""")

st.markdown("---")

# סקציה 8: הרחבות עתידיות
st.header("🚀 הרחבות עתידיות")

st.write("""
- תמיכה במסחר אוטומטי (API לברוקרים)
- למידת מכונה לחיזוי קורלציות
- אפליקציית מובייל
- התראות SMS/WhatsApp
- ניתוח sentiment מחדשות
- backtesting מתקדם
""")

st.markdown("---")

# כותרת תחתונה
st.markdown("""
<div style='text-align: center; color: #0066CC; padding: 1rem; direction: rtl;'>
    נבנתה ע"י SmartMindsAI - Ilya & Evgeniy
</div>
""", unsafe_allow_html=True)

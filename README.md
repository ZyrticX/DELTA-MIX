# DeltaMix 2.0 Prediction Engine

מערכת חיזוי מבוססת קורלציות היסטוריות שעונה על השאלה: **"כשמניה X נמצאת בקורלציה עם מניות Y,Z,W - מה הסבירות שהיא תעלה/תרד ב-N ימים הקדמה?"**

## 🚀 התחלה מהירה

```bash
# 1. התקנת dependencies
pip install -r requirements.txt
cd frontend && npm install

# 2. הגדרת משתני סביבה (ראה INSTALLATION.md)

# 3. Scraping רשימת מניות
python -m prediction_engine.apify_scraper

# 4. Pre-Computation (מצב בדיקה)
python -m prediction_engine.pre_compute --test

# 5. הרצת Frontend
cd frontend && npm run dev
```

## 📚 תיעוד

- **[README_DELTAMIX2.md](README_DELTAMIX2.md)** - תיעוד מפורט של המערכת
- **[INSTALLATION.md](INSTALLATION.md)** - הוראות התקנה מפורטות
- **[docs/](docs/)** - תיעוד נוסף

## 🏗️ ארכיטקטורה

המערכת בנויה מ-4 שכבות:

1. **Pre-Computation Engine (Python)** - חישוב כל הקורלציות ההיסטוריות
2. **Database Storage (Supabase)** - אחסון הנתונים
3. **API Layer (Next.js)** - שאילתות וניתוח
4. **Frontend Interface (Next.js + React)** - ממשק משתמש

## 📁 מבנה הפרויקט

```
correlation_system_1/
├── prediction_engine/     # Python Backend
│   ├── pre_compute.py     # מנוע Pre-Computation
│   ├── daily_update.py    # עדכון יומי
│   ├── apify_scraper.py  # Apify scraping
│   ├── db_client.py      # Supabase client
│   └── ...
├── frontend/              # Next.js Frontend
│   ├── app/              # Next.js App Router
│   ├── components/       # רכיבי UI
│   └── lib/              # Utilities
├── database/              # Database schemas
├── data_cache/            # קאש נתוני מניות
├── legacy_streamlit/      # המערכת הישנה (Streamlit)
└── docs/                  # תיעוד נוסף
```

## 🔄 המערכת הישנה

המערכת הישנה מבוססת Streamlit נשמרה ב-`legacy_streamlit/` למטרות היסטוריות.

**המערכת החדשה (DeltaMix 2.0) היא המומלצת לשימוש.**

## 📝 רישיון

MIT

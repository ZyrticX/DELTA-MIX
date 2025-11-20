# DeltaMix 2.0 Prediction Engine

מערכת חיזוי מבוססת קורלציות היסטוריות שעונה על השאלה: "כשמניה X נמצאת בקורלציה עם מניות Y,Z,W - מה הסבירות שהיא תעלה/תרד ב-N ימים הקדמה?"

## ארכיטקטורה

המערכת בנויה מ-4 שכבות עיקריות:

1. **Pre-Computation Engine (Python)** - חישוב כל הקורלציות ההיסטוריות + תוצאות עתידיות
2. **Database Storage (Supabase PostgreSQL)** - אחסון הנתונים
3. **API Layer (Next.js API Routes)** - שאילתות וניתוח
4. **Frontend Interface (Next.js + React)** - ממשק משתמש

## התקנה

### 1. Python Backend

```bash
pip install -r requirements.txt
```

### 2. Frontend

```bash
cd frontend
npm install
```

### 3. הגדרת משתני סביבה

צור קובץ `.env` עם:

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
APIFY_API_TOKEN=your_apify_token (אופציונלי)
```

## שימוש

### 1. Scraping רשימת מניות (Apify)

```bash
python -m prediction_engine.apify_scraper
```

או דרך Python:

```python
from prediction_engine.apify_scraper import ApifyScraper

scraper = ApifyScraper()
result = scraper.scrape_stock_list()
print(result)
```

### 2. Pre-Computation (חישוב כל הקורלציות)

```bash
# מצב בדיקה (10 מניות)
python -m prediction_engine.pre_compute --test

# הרצה מלאה
python -m prediction_engine.pre_compute

# עם פרמטרים מותאמים
python -m prediction_engine.pre_compute --start-date 2020-01-01 --end-date 2024-01-01
```

### 3. עדכון יומי

```bash
python -m prediction_engine.daily_update
```

מומלץ להגדיר Cron job להרצה יומית ב-7:00 AM.

### 4. הרצת Frontend

```bash
cd frontend
npm run dev
```

המערכת תהיה זמינה ב-`http://localhost:3000`

## מבנה קבצים

```
correlation_system_1/
├── prediction_engine/          # Python Backend
│   ├── pre_compute.py          # מנוע Pre-Computation
│   ├── daily_update.py         # עדכון יומי
│   ├── apify_scraper.py        # Apify scraping
│   ├── db_client.py            # Supabase client
│   ├── config.py               # הגדרות
│   └── utils.py                # פונקציות עזר
├── frontend/                    # Next.js Frontend
│   ├── app/                    # Next.js App Router
│   │   ├── api/                # API Routes
│   │   └── analysis/           # עמודי ניתוח
│   ├── components/             # רכיבי UI
│   └── lib/                    # Utilities
├── database/                    # Database schemas
└── data_cache/                  # קאש נתוני מניות
```

## API Endpoints

### `/api/analysis/current`
ניתוח מניה נוכחי

**Request:**
```json
{
  "stock_symbol": "AAPL",
  "lookback_days": 15,
  "correlation_threshold": 0.85,
  "forward_days": 15
}
```

**Response:**
```json
{
  "stock_symbol": "AAPL",
  "current_matches": [...],
  "historical_patterns": {
    "total_similar_occurrences": 47,
    "avg_future_return": -8.5,
    "prediction": {
      "direction": "down",
      "confidence": 68,
      "expected_return": -8.5
    },
    "distribution": {...}
  },
  "top_5_similar_dates": [...],
  "warnings": []
}
```

### `/api/stocks/list`
רשימת מניות

**Response:**
```json
{
  "stocks": [
    {"symbol": "AAPL", "company_name": "Apple Inc.", "sector": "Technology"},
    ...
  ],
  "count": 500
}
```

## מסכים

### מסך 1: הגדרות
- בחירת מניה
- הגדרת פרמטרים (ימים אחורה, סף קורלציה, ימים קדימה)
- כפתור "נתח מניה"

### מסך 2: תוצאות ניתוח
- מצב נוכחי (מניות בקורלציה, דוגמאות מהעבר)
- חיזוי (כיוון, גודל, ביטחון)
- התפלגות תוצאות
- 5 המקרים הדומים ביותר
- אזהרות

### מסך 3: סריקת שוק
- מסננים מהירים
- טבלת תוצאות
- ייצוא רשימה

## הערות

- המערכת דורשת Supabase project פעיל
- Pre-Computation יכול לקחת זמן רב (מספר שעות) עבור כל 500 המניות
- מומלץ להריץ Pre-Computation בלילה או על שרת חזק
- Daily update צריך לרוץ כל יום כדי לשמור על נתונים מעודכנים

## רישיון

MIT


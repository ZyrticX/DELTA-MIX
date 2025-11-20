# הוראות התקנה - DeltaMix 2.0

## דרישות מוקדמות

- Python 3.8+
- Node.js 18+
- Supabase account (חינמי)
- Apify account (אופציונלי, רק ל-scraping)

## שלב 1: התקנת Python Dependencies

```bash
pip install -r requirements.txt
```

## שלב 2: הגדרת Supabase

1. צור Supabase project חדש ב-https://supabase.com
2. העתק את ה-URL וה-API keys
3. ה-migrations כבר יושמו דרך MCP Supabase, אבל אפשר לבדוק:

```sql
-- בדיקה שהטבלאות קיימות
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('correlation_snapshots', 'pattern_statistics', 'daily_analysis_cache', 'stock_list');
```

## שלב 3: הגדרת משתני סביבה

צור קובץ `.env` בשורש הפרויקט:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Next.js (צריך גם ב-frontend/.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# Apify (אופציונלי)
APIFY_API_TOKEN=your_apify_token
APIFY_ACTOR_ID=your_actor_id
APIFY_INPUT_URL=https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
```

צור גם `frontend/.env.local` עם אותם משתנים (רק ה-NEXT_PUBLIC_*).

## שלב 4: Scraping רשימת מניות

### אופציה A: דרך Apify (מומלץ)

```bash
python -m prediction_engine.apify_scraper
```

### אופציה B: ידנית

```python
from prediction_engine.db_client import SupabaseClient

db = SupabaseClient()
# הוסף מניות ידנית דרך Supabase dashboard או SQL
```

## שלב 5: הורדת נתוני מניות

```bash
# הורדת כל המניות (יכול לקחת זמן)
python download_all_stocks.py
```

או דרך Python:

```python
from data_fetcher import DataFetcher

fetcher = DataFetcher()
symbols = fetcher.get_sp500_symbols()
fetcher.download_multiple_stocks(symbols)
```

## שלב 6: Pre-Computation

**⚠️ חשוב:** זה יכול לקחת מספר שעות!

```bash
# מצב בדיקה (10 מניות בלבד)
python -m prediction_engine.pre_compute --test

# הרצה מלאה (כל המניות)
python -m prediction_engine.pre_compute
```

## שלב 7: התקנת Frontend

```bash
cd frontend
npm install
```

## שלב 8: הרצת Frontend

```bash
cd frontend
npm run dev
```

פתח דפדפן ב-`http://localhost:3000`

## שלב 9: הגדרת עדכון יומי (אופציונלי)

### Windows (Task Scheduler)

1. פתח Task Scheduler
2. צור Task חדש
3. Trigger: Daily, 7:00 AM
4. Action: `python -m prediction_engine.daily_update`

### Linux/Mac (Cron)

```bash
crontab -e
```

הוסף:

```
0 7 * * * cd /path/to/correlation_system_1 && python -m prediction_engine.daily_update
```

## בדיקות

### בדיקת Database

```python
from prediction_engine.db_client import SupabaseClient

db = SupabaseClient()
stocks = db.get_stock_list()
print(f"נמצאו {len(stocks)} מניות")

snapshots = db.get_correlation_snapshots(limit=10)
print(f"נמצאו {len(snapshots)} snapshots")
```

### בדיקת API

```bash
# בדיקת רשימת מניות
curl http://localhost:3000/api/stocks/list

# בדיקת ניתוח
curl -X POST http://localhost:3000/api/analysis/current \
  -H "Content-Type: application/json" \
  -d '{"stock_symbol":"AAPL","lookback_days":15,"correlation_threshold":0.85,"forward_days":15}'
```

## פתרון בעיות

### שגיאת Supabase Connection

- ודא שה-URL וה-keys נכונים
- בדוק שה-Tables נוצרו (דרך Supabase dashboard)

### שגיאת Import

```bash
# ודא שאתה בתיקיית השורש
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Frontend לא מתחבר ל-Supabase

- ודא ש-`.env.local` קיים ב-`frontend/`
- ודא שה-matching keys (NEXT_PUBLIC_*)
- בדוק את ה-console בדפדפן

### Pre-Computation איטי מדי

- השתמש ב-`--test` לבדיקה
- הפעל על שרת חזק יותר
- בדוק את מספר ה-workers ב-`config.py`

## תמיכה

לשאלות ותמיכה, פתח issue ב-GitHub.


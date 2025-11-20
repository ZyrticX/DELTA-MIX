# מבנה הפרויקט - DeltaMix 2.0

## מבנה התיקיות

```
correlation_system_1/
│
├── prediction_engine/          # Python Backend - המערכת החדשה
│   ├── __init__.py
│   ├── config.py               # הגדרות גלובליות
│   ├── db_client.py            # Supabase client wrapper
│   ├── apify_scraper.py        # Apify scraping
│   ├── pre_compute.py          # מנוע Pre-Computation
│   ├── daily_update.py         # עדכון יומי
│   ├── backtest.py             # Backtesting engine
│   └── utils.py                # פונקציות עזר
│
├── frontend/                    # Next.js Frontend
│   ├── app/                    # Next.js App Router
│   │   ├── api/                # API Routes
│   │   │   ├── analysis/       # ניתוח
│   │   │   ├── stocks/         # מניות
│   │   │   └── admin/          # ניהול
│   │   ├── analysis/           # עמודי ניתוח
│   │   │   ├── single/         # ניתוח מניה בודדת
│   │   │   └── multiple/       # סריקת שוק
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/             # רכיבי UI
│   │   ├── ParametersPanel.tsx
│   │   ├── ConfidenceGauge.tsx
│   │   └── WarningBanner.tsx
│   ├── lib/                    # Utilities
│   │   ├── supabase.ts
│   │   ├── queries.ts
│   │   └── api.ts
│   └── package.json
│
├── database/                    # Database schemas
│   ├── migrations/             # Database migrations
│   └── README.md
│
├── data_cache/                  # קאש נתוני מניות (לא ב-Git)
│   └── *.pkl                   # קבצי pickle של נתוני מניות
│
├── legacy_streamlit/            # המערכת הישנה (Streamlit)
│   ├── deltamix.py
│   ├── pages/
│   ├── utils.py
│   └── daily_update.py
│
├── docs/                        # תיעוד נוסף
│   ├── DEPLOYMENT.md
│   ├── GIT_SETUP.md
│   └── ...
│
├── scripts/                     # סקריפטים שימושיים
│   ├── download_all_stocks.py
│   └── test_system.py
│
├── deployment/                  # קבצי deployment
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── Procfile
│   └── runtime.txt
│
├── correlation_engine.py        # מנוע קורלציות (משותף)
├── data_fetcher.py             # הורדת נתונים (משותף)
│
├── README.md                   # README ראשי
├── README_DELTAMIX2.md         # תיעוד מפורט
├── INSTALLATION.md             # הוראות התקנה
├── requirements.txt            # Python dependencies
└── .gitignore                  # Git ignore rules
```

## קבצים בשורש

### קבצים פעילים (בשימוש)
- `correlation_engine.py` - מנוע קורלציות (משותף למערכת הישנה והחדשה)
- `data_fetcher.py` - הורדת נתונים (משותף למערכת הישנה והחדשה)
- `requirements.txt` - Python dependencies
- `README.md` - README ראשי
- `README_DELTAMIX2.md` - תיעוד מפורט
- `INSTALLATION.md` - הוראות התקנה

### תיקיות
- `prediction_engine/` - המערכת החדשה (Python Backend)
- `frontend/` - Frontend (Next.js)
- `database/` - Database schemas
- `data_cache/` - קאש נתונים (לא ב-Git)
- `legacy_streamlit/` - המערכת הישנה
- `docs/` - תיעוד נוסף
- `scripts/` - סקריפטים
- `deployment/` - קבצי deployment

## הערות

- המערכת החדשה נמצאת ב-`prediction_engine/` ו-`frontend/`
- המערכת הישנה נשמרה ב-`legacy_streamlit/` למטרות היסטוריות
- `correlation_engine.py` ו-`data_fetcher.py` משותפים לשתי המערכות


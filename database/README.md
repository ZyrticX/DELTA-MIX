# Database Schemas

הטבלאות נוצרו דרך MCP Supabase. לפרטים על ה-schemas, ראה את הקוד ב-`prediction_engine/db_client.py`.

## טבלאות

- `correlation_snapshots` - snapshots יומיים של קורלציות
- `pattern_statistics` - סטטיסטיקות פטרנים
- `daily_analysis_cache` - קאש ניתוחים יומיים
- `stock_list` - רשימת מניות

## Migrations

ה-migrations נוצרו דרך `mcp_supabase_apply_migration`:
- `create_correlation_snapshots`
- `create_pattern_statistics`
- `create_daily_analysis_cache`
- `create_stock_list`


"""
הגדרות גלובליות למערכת DeltaMix 2.0 Prediction Engine
"""

import os
from typing import Dict

# פרמטרי חישוב
COMPUTATION_PARAMS = {
    'lookback_days': 15,  # גמיש: 5-30
    'forward_days': 15,   # גמיש: 5-30
    'correlation_threshold': 0.85,  # גמיש: 0.7-0.95
    'window_type': 'discrete',  # 'discrete' או 'rolling'
    
    # Movement classification thresholds
    'movement_thresholds': {
        'strong_up': 10.0,      # +10% ומעלה
        'moderate_up': 5.0,      # +5% עד +10%
        'neutral_upper': 5.0,    # -5% עד +5%
        'neutral_lower': -5.0,
        'moderate_down': -5.0,  # -5% עד -10%
        'strong_down': -10.0    # -10% ומטה
    }
}

# הגדרות Supabase
SUPABASE_CONFIG = {
    'url': os.getenv('SUPABASE_URL', ''),
    'anon_key': os.getenv('SUPABASE_ANON_KEY', ''),
    'service_role_key': os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''),
}

# הגדרות multiprocessing
MULTIPROCESSING_CONFIG = {
    'max_workers': min(16, os.cpu_count() or 8),
    'batch_size': 1000,  # גודל batch ל-Supabase inserts
    'chunk_size': 50,    # מספר מניות לכל worker
}

# הגדרות Apify
APIFY_CONFIG = {
    'api_token': os.getenv('APIFY_API_TOKEN', ''),
    'actor_id': os.getenv('APIFY_ACTOR_ID', ''),
    'input_url': os.getenv('APIFY_INPUT_URL', 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'),
}

# נתיבים
PATHS = {
    'data_cache': 'data_cache',
    'database_migrations': 'database/migrations',
}

# הגדרות קאש
CACHE_CONFIG = {
    'daily_analysis_ttl_days': 7,  # TTL לקאש ניתוחים יומיים
    'pattern_statistics_ttl_days': 30,  # TTL לסטטיסטיקות פטרנים
}


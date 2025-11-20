"""
Supabase Database Client Wrapper
"""

import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import time
import logging

from .config import SUPABASE_CONFIG, MULTIPROCESSING_CONFIG

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Wrapper ל-Supabase Python client עם:
    - Connection pooling
    - Batch inserts (1000 שורות)
    - Error handling
    - Retry logic (3 ניסיונות)
    """
    
    def __init__(self):
        """אתחול Supabase client"""
        url = SUPABASE_CONFIG['url']
        key = SUPABASE_CONFIG['service_role_key'] or SUPABASE_CONFIG['anon_key']
        
        if not url or not key:
            raise ValueError("Supabase URL ו-API key נדרשים. בדוק את משתני הסביבה.")
        
        self.client: Client = create_client(
            url,
            key,
            options=ClientOptions(
                postgrest_client_timeout=60,
                storage_client_timeout=60,
            )
        )
        self.batch_size = MULTIPROCESSING_CONFIG['batch_size']
    
    def insert_correlation_snapshots(self, snapshots: List[Dict[str, Any]]) -> bool:
        """
        הכנסת correlation snapshots ל-DB
        
        Args:
            snapshots: רשימת snapshots להכנסה
            
        Returns:
            True אם הצליח, False אחרת
        """
        if not snapshots:
            return True
        
        try:
            # Batch inserts
            for i in range(0, len(snapshots), self.batch_size):
                batch = snapshots[i:i + self.batch_size]
                self._retry_insert('correlation_snapshots', batch)
            
            logger.info(f"✅ הוכנסו {len(snapshots)} correlation snapshots בהצלחה")
            return True
        except Exception as e:
            logger.error(f"❌ שגיאה בהכנסת correlation snapshots: {e}")
            return False
    
    def insert_pattern_statistics(self, statistics: List[Dict[str, Any]]) -> bool:
        """
        הכנסת pattern statistics ל-DB
        
        Args:
            statistics: רשימת statistics להכנסה
            
        Returns:
            True אם הצליח, False אחרת
        """
        if not statistics:
            return True
        
        try:
            # Batch inserts
            for i in range(0, len(statistics), self.batch_size):
                batch = statistics[i:i + self.batch_size]
                self._retry_insert('pattern_statistics', batch, upsert=True)
            
            logger.info(f"✅ עודכנו {len(statistics)} pattern statistics בהצלחה")
            return True
        except Exception as e:
            logger.error(f"❌ שגיאה בהכנסת pattern statistics: {e}")
            return False
    
    def upsert_stock_list(self, stocks: List[Dict[str, Any]]) -> bool:
        """
        עדכון/הכנסת רשימת מניות
        
        Args:
            stocks: רשימת מניות (symbol, company_name, sector)
            
        Returns:
            True אם הצליח, False אחרת
        """
        if not stocks:
            return True
        
        try:
            # Upsert לפי symbol
            for i in range(0, len(stocks), self.batch_size):
                batch = stocks[i:i + self.batch_size]
                self._retry_insert('stock_list', batch, upsert=True)
            
            logger.info(f"✅ עודכנו {len(stocks)} מניות בהצלחה")
            return True
        except Exception as e:
            logger.error(f"❌ שגיאה בעדכון רשימת מניות: {e}")
            return False
    
    def get_stock_list(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        שליפת רשימת מניות
        
        Args:
            active_only: האם להחזיר רק מניות פעילות
            
        Returns:
            רשימת מניות
        """
        try:
            query = self.client.table('stock_list').select('*')
            if active_only:
                query = query.eq('is_active', True)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"❌ שגיאה בשליפת רשימת מניות: {e}")
            return []
    
    def get_correlation_snapshots(self, 
                                  stock_symbol: Optional[str] = None,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None,
                                  limit: int = 1000) -> List[Dict[str, Any]]:
        """
        שליפת correlation snapshots
        
        Args:
            stock_symbol: סינון לפי מניה ספציפית
            start_date: תאריך התחלה (YYYY-MM-DD)
            end_date: תאריך סיום (YYYY-MM-DD)
            limit: מספר שורות מקסימלי
            
        Returns:
            רשימת snapshots
        """
        try:
            query = self.client.table('correlation_snapshots').select('*')
            
            if stock_symbol:
                query = query.eq('stock_symbol', stock_symbol)
            if start_date:
                query = query.gte('snapshot_date', start_date)
            if end_date:
                query = query.lte('snapshot_date', end_date)
            
            query = query.order('snapshot_date', desc=True).limit(limit)
            response = query.execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"❌ שגיאה בשליפת correlation snapshots: {e}")
            return []
    
    def get_pattern_statistics(self, stock_symbol: str) -> Optional[Dict[str, Any]]:
        """
        שליפת pattern statistics למניה ספציפית
        
        Args:
            stock_symbol: סימול המניה
            
        Returns:
            Dictionary עם statistics או None
        """
        try:
            response = self.client.table('pattern_statistics')\
                .select('*')\
                .eq('stock_symbol', stock_symbol)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"❌ שגיאה בשליפת pattern statistics: {e}")
            return None
    
    def cache_analysis_result(self, 
                             analysis_date: str,
                             stock_symbol: str,
                             params_hash: str,
                             result: Dict[str, Any],
                             ttl_days: int = 7) -> bool:
        """
        שמירת תוצאת ניתוח בקאש
        
        Args:
            analysis_date: תאריך הניתוח
            stock_symbol: סימול המניה
            params_hash: hash של הפרמטרים
            result: תוצאת הניתוח
            ttl_days: מספר ימים עד תפוגה
            
        Returns:
            True אם הצליח
        """
        try:
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(days=ttl_days)
            
            data = {
                'analysis_date': analysis_date,
                'stock_symbol': stock_symbol,
                'params_hash': params_hash,
                'result': result,
                'expires_at': expires_at.isoformat()
            }
            
            self.client.table('daily_analysis_cache').upsert(data).execute()
            return True
        except Exception as e:
            logger.error(f"❌ שגיאה בשמירת קאש: {e}")
            return False
    
    def get_cached_analysis(self,
                           analysis_date: str,
                           stock_symbol: str,
                           params_hash: str) -> Optional[Dict[str, Any]]:
        """
        שליפת תוצאת ניתוח מקאש
        
        Args:
            analysis_date: תאריך הניתוח
            stock_symbol: סימול המניה
            params_hash: hash של הפרמטרים
            
        Returns:
            תוצאת הניתוח או None אם לא נמצא
        """
        try:
            from datetime import datetime
            
            response = self.client.table('daily_analysis_cache')\
                .select('*')\
                .eq('analysis_date', analysis_date)\
                .eq('stock_symbol', stock_symbol)\
                .eq('params_hash', params_hash)\
                .gt('expires_at', datetime.now().isoformat())\
                .execute()
            
            if response.data:
                return response.data[0]['result']
            return None
        except Exception as e:
            logger.error(f"❌ שגיאה בשליפת קאש: {e}")
            return None
    
    def _retry_insert(self, table: str, data: List[Dict], upsert: bool = False, max_retries: int = 3):
        """
        הכנסת נתונים עם retry logic
        
        Args:
            table: שם הטבלה
            data: נתונים להכנסה
            upsert: האם לבצע upsert במקום insert
            max_retries: מספר ניסיונות מקסימלי
        """
        for attempt in range(max_retries):
            try:
                if upsert:
                    self.client.table(table).upsert(data).execute()
                else:
                    self.client.table(table).insert(data).execute()
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"⚠️ ניסיון {attempt + 1} נכשל, מנסה שוב בעוד {wait_time} שניות...")
                time.sleep(wait_time)


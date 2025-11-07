"""
סקריפט להורדת כל 500 מניות S&P 500 מ-1.1.2012
"""

import sys
import os
import shutil
from datetime import datetime

# Fix Windows console encoding for Hebrew
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from data_fetcher import DataFetcher

def clear_all_data():
    """מחיקת כל הנתונים הקיימים"""
    print("="*70)
    print("🗑️  מחיקת כל הנתונים הקיימים...")
    print("="*70)
    
    cache_dir = "data_cache"
    
    if os.path.exists(cache_dir):
        # ספירת קבצים לפני מחיקה
        files = [f for f in os.listdir(cache_dir) if f.endswith('.pkl')]
        file_count = len(files)
        
        print(f"נמצאו {file_count} קבצי נתונים למחיקה")
        
        # מחיקת כל הקבצים
        for filename in files:
            filepath = os.path.join(cache_dir, filename)
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"⚠️  שגיאה במחיקת {filename}: {e}")
        
        print(f"✅ נמחקו {file_count} קבצים")
    else:
        print("ℹ️  אין תיקיית קאש קיימת")
    
    print()

def download_all_stocks(start_date="2012-01-01", symbols_file=None):
    """הורדת כל 500 מניות S&P 500"""
    print("="*70)
    print("📥 הורדת כל 500 מניות S&P 500")
    print("="*70)
    print(f"תאריך התחלה: {start_date}")
    print(f"תאריך סיום: {datetime.now().strftime('%Y-%m-%d')}")
    print()
    
    fetcher = DataFetcher()
    
    # שלב 1: קבלת רשימת כל המניות
    print("שלב 1: מקבל רשימת מניות S&P 500...")
    
    symbols = None
    
    # אם יש קובץ - טען ממנו
    if symbols_file and os.path.exists(symbols_file):
        print(f"טוען מניות מקובץ: {symbols_file}")
        symbols = fetcher.load_symbols_from_file(symbols_file)
    
    # אם לא - נסה להוריד מוויקיפדיה
    if not symbols:
        try:
            symbols = fetcher.get_sp500_symbols()
        except Exception as e:
            print(f"❌ שגיאה בקבלת רשימת מניות: {e}")
            print("נסה להריץ שוב או צרף קובץ עם רשימת מניות")
            return False
    
    if not symbols:
        print("❌ לא נמצאו מניות להורדה")
        return False
    
    print(f"✅ נמצאו {len(symbols)} מניות")
    print()
    
    # שלב 2: הורדת כל המניות
    print("שלב 2: מוריד נתונים עבור כל המניות...")
    print("⚠️  זה עשוי לקחת 20-30 דקות...")
    print()
    
    try:
        stock_data = fetcher.download_multiple_stocks(
            symbols,
            start_date=start_date,
            end_date=None,  # עד היום
            use_cache=False  # כפיה להורדה מחדש
        )
        
        if stock_data is None or stock_data.empty:
            print("❌ כשלון בהורדת נתונים")
            return False
        
        print()
        print("="*70)
        print("✅ הורדה הושלמה בהצלחה!")
        print("="*70)
        print(f"מספר מניות: {len(stock_data.columns)//2}")
        print(f"מספר ימים: {len(stock_data)}")
        print(f"תקופה: {stock_data.index.min().strftime('%Y-%m-%d')} עד {stock_data.index.max().strftime('%Y-%m-%d')}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בהורדת נתונים: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def download_reference_stock(start_date="2012-01-01"):
    """הורדת מניית ייחוס (SPY)"""
    print("שלב 3: מוריד נתוני מניית ייחוס (SPY)...")
    
    fetcher = DataFetcher()
    
    try:
        reference_data = fetcher.get_reference_stock_data(
            symbol="SPY",
            start_date=start_date,
            end_date=None
        )
        
        if reference_data is None:
            print("❌ כשלון בהורדת נתוני SPY")
            return False
        
        print(f"✅ נתוני SPY נטענו: {len(reference_data['price'])} ימים")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בהורדת SPY: {e}")
        return False

def main():
    """פונקציה ראשית"""
    import sys
    
    print("\n" + "="*70)
    print("🚀 מערכת הורדת נתונים - כל 500 מניות S&P 500")
    print("="*70)
    print()
    
    # בדיקת קובץ מניות
    symbols_file = None
    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            symbols_file = sys.argv[idx + 1]
    
    # בדיקה אם יש דגל --yes
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv
    
    if not skip_confirmation:
        # אימות עם המשתמש
        print("⚠️  זה ימחק את כל הנתונים הקיימים ויוריד מחדש את כל 500 המניות")
        print("   התהליך עשוי לקחת 20-30 דקות")
        print()
        
        try:
            response = input("האם להמשיך? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y', 'כן', '']:
                print("בוטל על ידי המשתמש")
                return
        except EOFError:
            # אם אין input זמין (כמו ב-automation), המשך אוטומטית
            print("ממשיך אוטומטית...")
    
    print()
    
    # שלב 1: מחיקת נתונים קיימים
    clear_all_data()
    
    # שלב 2: הורדת כל המניות
    success = download_all_stocks(start_date="2012-01-01", symbols_file=symbols_file)
    
    if not success:
        print("❌ ההורדה נכשלה")
        return
    
    # שלב 3: הורדת מניית ייחוס
    download_reference_stock(start_date="2012-01-01")
    
    print()
    print("="*70)
    print("✅ כל הנתונים הורדו בהצלחה!")
    print("="*70)
    print()
    print("📋 סיכום:")
    print("   ✅ כל הנתונים הקיימים נמחקו")
    print("   ✅ כל 500 מניות S&P 500 הורדו מ-1.1.2012")
    print("   ✅ מניית ייחוס SPY הורדה")
    print()
    print("🚀 המערכת מוכנה לשימוש!")
    print("   להפעלת הממשק הגרפי: streamlit run deltamix.py")
    print()

if __name__ == '__main__':
    main()


/**
 * API Route: /api/admin/scrape-stocks
 * Scraping רשימת מניות דרך Apify
 */

import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    // TODO: יישום Apify scraping
    // זה צריך לקרוא ל-Apify API ולעדכן את stock_list ב-Supabase
    
    // זמנית - מחזיר הודעת שגיאה
    return NextResponse.json(
      { 
        success: false,
        message: 'Apify scraping עדיין לא מיושם. יש להריץ את apify_scraper.py ישירות.',
        stocks_scraped: 0,
        stocks_added: 0,
        stocks_updated: 0,
      },
      { status: 501 }
    )
  } catch (error: any) {
    console.error('Error in /api/admin/scrape-stocks:', error)
    return NextResponse.json(
      { error: error.message || 'שגיאה ב-scraping' },
      { status: 500 }
    )
  }
}


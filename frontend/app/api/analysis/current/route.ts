/**
 * API Route: /api/analysis/current
 * ניתוח מניה נוכחי
 */

import { NextRequest, NextResponse } from 'next/server'
import { getCurrentCorrelations, getHistoricalPatterns, findSimilarPatterns } from '@/lib/queries'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const {
      stock_symbol,
      lookback_days = 15,
      correlation_threshold = 0.85,
      forward_days = 15,
      analysis_date,
    } = body

    if (!stock_symbol) {
      return NextResponse.json({ error: 'stock_symbol נדרש' }, { status: 400 })
    }

    const date = analysis_date || new Date().toISOString().split('T')[0]

    // שליפת קורלציות נוכחיות
    const currentMatches = await getCurrentCorrelations(stock_symbol, date)

    // חישוב פטרנים היסטוריים
    const historicalPatterns = await getHistoricalPatterns({
      stock_symbol,
      lookback_days,
      correlation_threshold,
      forward_days,
      analysis_date: date,
    })

    // מציאת מקרים דומים
    const topSimilarDates = await findSimilarPatterns(stock_symbol, currentMatches, 5)

    // אזהרות
    const warnings = []
    if (historicalPatterns) {
      if (historicalPatterns.total_similar_occurrences < 10) {
        warnings.push('few_examples')
      }
      if (historicalPatterns.prediction.confidence < 55) {
        warnings.push('low_confidence')
      }
      // בדיקת גיל הדוגמאות
      if (topSimilarDates.length > 0) {
        const oldestDate = new Date(topSimilarDates[topSimilarDates.length - 1].date)
        const yearsAgo = (new Date().getTime() - oldestDate.getTime()) / (1000 * 60 * 60 * 24 * 365)
        if (yearsAgo > 8) {
          warnings.push('old_examples')
        }
      }
      // בדיקת התפלגות מפוזרת
      const { distribution } = historicalPatterns
      const total = distribution.strong_up + distribution.moderate_up + distribution.neutral +
                    distribution.moderate_down + distribution.strong_down
      if (total > 0) {
        const upRatio = (distribution.strong_up + distribution.moderate_up) / total
        const downRatio = (distribution.strong_down + distribution.moderate_down) / total
        if (Math.abs(upRatio - downRatio) < 0.1) {
          warnings.push('scattered_distribution')
        }
      }
    }

    return NextResponse.json({
      stock_symbol,
      analysis_date: date,
      current_matches: currentMatches,
      historical_patterns: historicalPatterns,
      top_5_similar_dates: topSimilarDates,
      warnings,
    })
  } catch (error: any) {
    console.error('Error in /api/analysis/current:', error)
    return NextResponse.json(
      { error: error.message || 'שגיאה בניתוח' },
      { status: 500 }
    )
  }
}


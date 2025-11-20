/**
 * עמוד ניתוח מניה בודדת - מסך 2
 */

'use client'

import { useState } from 'react'
import ParametersPanel from '@/components/ParametersPanel'
import ConfidenceGauge from '@/components/ConfidenceGauge'
import WarningBanner from '@/components/WarningBanner'
import { analyzeStock } from '@/lib/api'

export default function SingleAnalysisPage() {
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async (params: any) => {
    setLoading(true)
    setError(null)
    try {
      const result = await analyzeStock(params)
      setAnalysisResult(result)
    } catch (err: any) {
      setError(err.message || 'שגיאה בניתוח')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">ניתוח מניה בודדת</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Panel הגדרות */}
          <div className="lg:col-span-1">
            <ParametersPanel onAnalyze={handleAnalyze} />
          </div>

          {/* תוצאות */}
          <div className="lg:col-span-2">
            {loading && (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4">מחשב...</p>
              </div>
            )}

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
                {error}
              </div>
            )}

            {analysisResult && (
              <div className="space-y-6">
                {/* Panel 1: מצב נוכחי */}
                <div className="p-6 border rounded-lg bg-white">
                  <h2 className="text-xl font-bold mb-4">מצב נוכחי</h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">מניות בקורלציה</div>
                      <div className="text-2xl font-bold">
                        {analysisResult.current_matches?.length || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">דוגמאות מהעבר</div>
                      <div className="text-2xl font-bold">
                        {analysisResult.historical_patterns?.total_similar_occurrences || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">ממוצע תנועה</div>
                      <div className={`text-2xl font-bold ${
                        (analysisResult.historical_patterns?.avg_future_return || 0) >= 0
                          ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {analysisResult.historical_patterns?.avg_future_return?.toFixed(2) || 0}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">ביטחון</div>
                      <ConfidenceGauge
                        confidence={analysisResult.historical_patterns?.prediction?.confidence || 0}
                        size="small"
                      />
                    </div>
                  </div>
                </div>

                {/* Panel 2: חיזוי */}
                {analysisResult.historical_patterns && (
                  <div className="p-6 border rounded-lg bg-white">
                    <h2 className="text-xl font-bold mb-4">חיזוי</h2>
                    <div className="flex items-center gap-6">
                      <ConfidenceGauge
                        confidence={analysisResult.historical_patterns.prediction.confidence}
                        size="large"
                      />
                      <div>
                        <div className="text-2xl font-bold">
                          {analysisResult.historical_patterns.prediction.direction === 'up' ? '⬆️' : '⬇️'}
                          {' '}
                          {analysisResult.historical_patterns.prediction.expected_return.toFixed(2)}%
                        </div>
                        <p className="text-gray-600 mt-2">
                          על סמך {analysisResult.historical_patterns.total_similar_occurrences} דוגמאות מהעבר,
                          במרבית המקרים ({analysisResult.historical_patterns.prediction.confidence.toFixed(0)}%)
                          המניה {analysisResult.historical_patterns.prediction.direction === 'up' ? 'עלתה' : 'ירדה'}
                          בממוצע {Math.abs(analysisResult.historical_patterns.prediction.expected_return).toFixed(2)}%
                          תוך {analysisResult.forward_days || 15} ימים.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* אזהרות */}
                {analysisResult.warnings && analysisResult.warnings.length > 0 && (
                  <div className="space-y-2">
                    {analysisResult.warnings.includes('few_examples') && (
                      <WarningBanner
                        type="warning"
                        message="יש מעט דוגמאות היסטוריות. החיזוי עשוי להיות פחות אמין."
                      />
                    )}
                    {analysisResult.warnings.includes('low_confidence') && (
                      <WarningBanner
                        type="warning"
                        message="רמת ביטחון נמוכה. אין מגמה ברורה בדוגמאות."
                      />
                    )}
                    {analysisResult.warnings.includes('old_examples') && (
                      <WarningBanner
                        type="info"
                        message="כל הדוגמאות מלפני 8+ שנים. השוק עשוי להשתנות."
                      />
                    )}
                    {analysisResult.warnings.includes('scattered_distribution') && (
                      <WarningBanner
                        type="warning"
                        message="התפלגות מפוזרת. אין מגמה ברורה."
                      />
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


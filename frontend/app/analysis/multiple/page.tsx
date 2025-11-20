/**
 * עמוד סריקת שוק - מסך 3
 */

'use client'

import { useState } from 'react'
import { getStocksList, analyzeStock } from '@/lib/api'

interface ScanResult {
  stock_symbol: string
  correlations: number
  prediction: number
  confidence: number
  examples: number
}

export default function MarketScannerPage() {
  const [results, setResults] = useState<ScanResult[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    strongPrediction: true,
    significantMovement: true,
    onlyUp: false,
    onlyDown: false,
  })

  const handleScan = async () => {
    setLoading(true)
    try {
      // שליפת רשימת מניות
      const stocksData = await getStocksList()
      const stocks = stocksData.stocks || []

      // סריקת כל המניות
      const scanResults: ScanResult[] = []
      
      for (const stock of stocks.slice(0, 50)) { // זמנית - רק 50 מניות לבדיקה
        try {
          const analysis = await analyzeStock({
            stock_symbol: stock.symbol,
            lookback_days: 15,
            correlation_threshold: 0.85,
            forward_days: 15,
          })

          if (analysis.historical_patterns) {
            const confidence = analysis.historical_patterns.prediction.confidence || 0
            const expectedReturn = analysis.historical_patterns.prediction.expected_return || 0

            // בדיקת מסננים
            if (filters.strongPrediction && confidence < 70) continue
            if (filters.significantMovement && Math.abs(expectedReturn) < 8) continue
            if (filters.onlyUp && expectedReturn < 0) continue
            if (filters.onlyDown && expectedReturn > 0) continue

            scanResults.push({
              stock_symbol: stock.symbol,
              correlations: analysis.current_matches?.length || 0,
              prediction: expectedReturn,
              confidence: confidence,
              examples: analysis.historical_patterns.total_similar_occurrences || 0,
            })
          }
        } catch (err) {
          console.error(`Error scanning ${stock.symbol}:`, err)
        }
      }

      setResults(scanResults)
    } catch (err: any) {
      console.error('Error scanning market:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">🔍 סריקת שוק - 500 מניות</h1>

        {/* מסננים */}
        <div className="p-6 border rounded-lg bg-white mb-6">
          <h2 className="text-xl font-bold mb-4">מסננים מהירים:</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={filters.strongPrediction}
                onChange={(e) => setFilters({ ...filters, strongPrediction: e.target.checked })}
                className="mr-2"
              />
              רק עם חיזוי חזק (ביטחון &gt;70%)
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={filters.significantMovement}
                onChange={(e) => setFilters({ ...filters, significantMovement: e.target.checked })}
                className="mr-2"
              />
              רק עם תנועה משמעותית (מעל 8%)
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={filters.onlyUp}
                onChange={(e) => setFilters({ ...filters, onlyUp: e.target.checked })}
                className="mr-2"
              />
              רק עליות
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={filters.onlyDown}
                onChange={(e) => setFilters({ ...filters, onlyDown: e.target.checked })}
                className="mr-2"
              />
              רק ירידות
            </label>
          </div>

          <button
            onClick={handleScan}
            disabled={loading}
            className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            🚀 סרוק שוק
          </button>
        </div>

        {/* תוצאות */}
        {loading && (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4">סורק שוק...</p>
          </div>
        )}

        {results.length > 0 && (
          <div>
            <p className="mb-4 text-lg">
              📊 תוצאות: נמצאו {results.length} מניות עם תבניות מעניינות
            </p>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 p-2">מניה</th>
                    <th className="border border-gray-300 p-2">קורלציות</th>
                    <th className="border border-gray-300 p-2">חיזוי</th>
                    <th className="border border-gray-300 p-2">ביטחון</th>
                    <th className="border border-gray-300 p-2">דוגמאות</th>
                    <th className="border border-gray-300 p-2">פעולה</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => (
                    <tr key={result.stock_symbol}>
                      <td className="border border-gray-300 p-2 font-semibold">
                        {result.stock_symbol}
                      </td>
                      <td className="border border-gray-300 p-2">{result.correlations}</td>
                      <td
                        className={`border border-gray-300 p-2 font-semibold ${
                          result.prediction >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {result.prediction >= 0 ? '⬆️' : '⬇️'} {result.prediction.toFixed(2)}%
                      </td>
                      <td className="border border-gray-300 p-2">{result.confidence.toFixed(0)}%</td>
                      <td className="border border-gray-300 p-2">{result.examples}</td>
                      <td className="border border-gray-300 p-2">
                        <a
                          href={`/analysis/single?symbol=${result.stock_symbol}`}
                          className="text-blue-600 hover:underline"
                        >
                          פרטים
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


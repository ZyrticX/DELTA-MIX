/**
 * Parameters Panel - מסך הגדרות
 */

'use client'

import { useState, useEffect } from 'react'
import { getStocksList } from '@/lib/api'

interface ParametersPanelProps {
  onAnalyze: (params: {
    stock_symbol: string
    lookback_days: number
    correlation_threshold: number
    forward_days: number
    window_type: 'discrete' | 'rolling'
  }) => void
}

export default function ParametersPanel({ onAnalyze }: ParametersPanelProps) {
  const [stockSymbol, setStockSymbol] = useState('')
  const [lookbackDays, setLookbackDays] = useState(15)
  const [correlationThreshold, setCorrelationThreshold] = useState(0.85)
  const [forwardDays, setForwardDays] = useState(15)
  const [windowType, setWindowType] = useState<'discrete' | 'rolling'>('discrete')
  const [stocks, setStocks] = useState<Array<{ symbol: string; company_name?: string }>>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // טעינת רשימת מניות
    getStocksList().then((data) => {
      setStocks(data.stocks || [])
    })
  }, [])

  const handleAnalyze = () => {
    if (!stockSymbol) {
      alert('אנא בחר מניה')
      return
    }
    onAnalyze({
      stock_symbol: stockSymbol,
      lookback_days: lookbackDays,
      correlation_threshold: correlationThreshold,
      forward_days: forwardDays,
      window_type: windowType,
    })
  }

  return (
    <div className="p-6 border rounded-lg bg-white">
      <h2 className="text-2xl font-bold mb-4">📊 בחר מניה לניתוח</h2>
      
      <div className="mb-4">
        <label className="block mb-2">מניה:</label>
        <select
          value={stockSymbol}
          onChange={(e) => setStockSymbol(e.target.value)}
          className="w-full p-2 border rounded"
        >
          <option value="">בחר מניה...</option>
          {stocks.map((stock) => (
            <option key={stock.symbol} value={stock.symbol}>
              {stock.symbol} {stock.company_name ? `- ${stock.company_name}` : ''}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block mb-2">
            כמה ימים אחורה לבדוק? ({lookbackDays} ימים)
          </label>
          <input
            type="range"
            min={5}
            max={30}
            value={lookbackDays}
            onChange={(e) => setLookbackDays(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block mb-2">
            רמת דמיון מינימלית? ({correlationThreshold.toFixed(2)})
          </label>
          <input
            type="range"
            min={0.7}
            max={0.95}
            step={0.01}
            value={correlationThreshold}
            onChange={(e) => setCorrelationThreshold(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block mb-2">
            כמה ימים קדימה לחזות? ({forwardDays} ימים)
          </label>
          <input
            type="range"
            min={5}
            max={30}
            value={forwardDays}
            onChange={(e) => setForwardDays(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block mb-2">סוג חלון:</label>
          <div className="flex gap-4">
            <label>
              <input
                type="radio"
                value="discrete"
                checked={windowType === 'discrete'}
                onChange={() => setWindowType('discrete')}
                className="mr-2"
              />
              Discrete
            </label>
            <label>
              <input
                type="radio"
                value="rolling"
                checked={windowType === 'rolling'}
                onChange={() => setWindowType('rolling')}
                className="mr-2"
              />
              Rolling
            </label>
          </div>
        </div>
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading || !stockSymbol}
        className="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
      >
        🚀 נתח מניה
      </button>
    </div>
  )
}

async function getStocksList() {
  const res = await fetch('/api/stocks/list')
  return res.json()
}


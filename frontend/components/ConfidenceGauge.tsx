/**
 * Confidence Gauge - מד ביטחון
 */

interface ConfidenceGaugeProps {
  confidence: number // 0-100
  size?: 'small' | 'medium' | 'large'
}

export default function ConfidenceGauge({ confidence, size = 'medium' }: ConfidenceGaugeProps) {
  const sizeClasses = {
    small: 'w-16 h-16',
    medium: 'w-24 h-24',
    large: 'w-32 h-32',
  }

  const getColor = () => {
    if (confidence >= 70) return 'text-green-600'
    if (confidence >= 55) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className={`${sizeClasses[size]} relative flex items-center justify-center`}>
      <svg className="w-full h-full transform -rotate-90">
        <circle
          cx="50%"
          cy="50%"
          r="45%"
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          className="text-gray-200"
        />
        <circle
          cx="50%"
          cy="50%"
          r="45%"
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          strokeDasharray={`${confidence * 2.827} 282.7`}
          className={getColor()}
        />
      </svg>
      <div className="absolute text-center">
        <div className={`text-2xl font-bold ${getColor()}`}>{confidence.toFixed(0)}%</div>
      </div>
    </div>
  )
}


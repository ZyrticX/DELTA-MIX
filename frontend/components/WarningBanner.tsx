/**
 * Warning Banner - אזהרות
 */

interface WarningBannerProps {
  type: 'warning' | 'info' | 'error'
  message: string
}

export default function WarningBanner({ type, message }: WarningBannerProps) {
  const styles = {
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  }

  const icons = {
    warning: '⚠️',
    info: 'ℹ️',
    error: '❌',
  }

  return (
    <div className={`p-4 border rounded-lg ${styles[type]}`}>
      <div className="flex items-start">
        <span className="text-xl mr-2">{icons[type]}</span>
        <p>{message}</p>
      </div>
    </div>
  )
}


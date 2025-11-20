import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DeltaMix 2.0 - Prediction Engine',
  description: 'מערכת חיזוי מבוססת קורלציות היסטוריות',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="he" dir="rtl">
      <body>{children}</body>
    </html>
  )
}


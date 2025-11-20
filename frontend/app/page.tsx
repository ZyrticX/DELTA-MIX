/**
 * דף בית
 */

import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">
          DeltaMix 2.0 - Prediction Engine
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          <Link
            href="/analysis/single"
            className="p-6 border rounded-lg hover:bg-gray-50 transition"
          >
            <h2 className="text-2xl font-semibold mb-2">ניתוח מניה בודדת</h2>
            <p className="text-gray-600">בחר מניה וקבל חיזוי מבוסס קורלציות היסטוריות</p>
          </Link>
          
          <Link
            href="/analysis/multiple"
            className="p-6 border rounded-lg hover:bg-gray-50 transition"
          >
            <h2 className="text-2xl font-semibold mb-2">סריקת שוק</h2>
            <p className="text-gray-600">סרוק את כל השוק למציאת הזדמנויות</p>
          </Link>
        </div>
      </div>
    </main>
  )
}


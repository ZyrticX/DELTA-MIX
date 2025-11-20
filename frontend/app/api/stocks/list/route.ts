/**
 * API Route: /api/stocks/list
 * רשימת מניות
 */

import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const activeOnly = searchParams.get('active_only') !== 'false'

    const { data, error } = await supabase
      .from('stock_list')
      .select('*')
      .eq('is_active', activeOnly)
      .order('symbol', { ascending: true })

    if (error) throw error

    return NextResponse.json({
      stocks: data || [],
      count: data?.length || 0,
    })
  } catch (error: any) {
    console.error('Error in /api/stocks/list:', error)
    return NextResponse.json(
      { error: error.message || 'שגיאה בשליפת מניות' },
      { status: 500 }
    )
  }
}


import { NextRequest, NextResponse } from 'next/server'
import { getLatestOdds } from '@/lib/db/queries'
import { detectArbitrage } from '@/lib/engines/arbitrage'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const minProfit = parseFloat(searchParams.get('minProfit') ?? '0')

    const snapshots = await getLatestOdds()
    const opportunities = detectArbitrage(snapshots).filter(
      (arb) => arb.profit_pct >= minProfit
    )

    return NextResponse.json({ data: opportunities, count: opportunities.length })
  } catch (error) {
    console.error('[api/arbitrage]', error)
    return NextResponse.json({ error: 'Failed to fetch opportunities' }, { status: 500 })
  }
}

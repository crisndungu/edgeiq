import { NextResponse } from 'next/server'
import { getLatestOdds } from '@/lib/db/queries'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const eventId = searchParams.get('event_id') ?? undefined
    const data = await getLatestOdds(eventId)
    return NextResponse.json({ data })
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch odds' }, { status: 500 })
  }
}

// Single source of truth for all database types
// Mirrors the Supabase table definitions exactly

export type OddsSnapshot = {
  id: string
  bookmaker: string
  event_id: string
  market: string
  home_odds: number
  draw_odds: number | null
  away_odds: number
  timestamp: string
}

export type Event = {
  id: string
  name: string
  sport: string
  start_time: string
  home_team: string
  away_team: string
  created_at: string
}

export type ArbitrageOpportunity = {
  id: string
  event_id: string
  profit_pct: number
  bookmakers: string[]
  stakes: Record<string, number>
  odds: Record<string, number>
  found_at: string
}

export type ValueBet = {
  id: string
  event_id: string
  bookmaker: string
  market: string
  ai_prob: number
  book_prob: number
  edge_pct: number
  found_at: string
}

export type UserProfile = {
  id: string           // matches auth.users.id
  email: string
  phone: string | null
  tier: 'free' | 'premium' | 'vip'
  bankroll: number     // stored in KES cents
  telegram_chat_id: string | null
  created_at: string
}

export type Alert = {
  id: string
  user_id: string
  type: 'arbitrage' | 'value_bet' | 'odds_movement'
  threshold: number    // e.g. 1.0 = 1% profit for arb, 5.0 = 5% edge for value
  active: boolean
  created_at: string
}

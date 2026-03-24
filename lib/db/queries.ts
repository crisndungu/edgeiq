import { supabase, createServiceClient } from '../supabase'
import type {
  OddsSnapshot,
  Event,
  ArbitrageOpportunity,
  ValueBet,
  UserProfile,
  Alert,
} from './schema'

// ─── Odds Snapshots ───────────────────────────────────────────────────────────

export async function getLatestOdds(eventId?: string): Promise<OddsSnapshot[]> {
  let query = supabase
    .from('odds_snapshots')
    .select('*')
    .order('timestamp', { ascending: false })
    .limit(200)

  if (eventId) query = query.eq('event_id', eventId)

  const { data, error } = await query
  if (error) throw error
  return data ?? []
}

export async function getOddsHistory(eventId: string, hours = 24): Promise<OddsSnapshot[]> {
  const since = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString()
  const { data, error } = await supabase
    .from('odds_snapshots')
    .select('*')
    .eq('event_id', eventId)
    .gte('timestamp', since)
    .order('timestamp', { ascending: true })

  if (error) throw error
  return data ?? []
}

// ─── Events ───────────────────────────────────────────────────────────────────

export async function getUpcomingEvents(sport?: string): Promise<Event[]> {
  let query = supabase
    .from('events')
    .select('*')
    .gte('start_time', new Date().toISOString())
    .order('start_time', { ascending: true })
    .limit(100)

  if (sport) query = query.eq('sport', sport)

  const { data, error } = await query
  if (error) throw error
  return data ?? []
}

export async function upsertEvent(event: Omit<Event, 'created_at'>): Promise<void> {
  const { error } = await createServiceClient()
    .from('events')
    .upsert(event, { onConflict: 'id' })
  if (error) throw error
}

// ─── Arbitrage Opportunities ──────────────────────────────────────────────────

export async function getArbitrageOpportunities(minProfit = 0): Promise<ArbitrageOpportunity[]> {
  const { data, error } = await supabase
    .from('arbitrage_opportunities')
    .select('*')
    .gte('profit_pct', minProfit)
    .order('profit_pct', { ascending: false })
    .limit(50)

  if (error) throw error
  return data ?? []
}

export async function insertArbitrageOpportunity(
  opp: Omit<ArbitrageOpportunity, 'id' | 'found_at'>
): Promise<void> {
  const { error } = await createServiceClient()
    .from('arbitrage_opportunities')
    .insert(opp)
  if (error) throw error
}

// ─── Value Bets ───────────────────────────────────────────────────────────────

export async function getValueBets(minEdge = 0): Promise<ValueBet[]> {
  const { data, error } = await supabase
    .from('value_bets')
    .select('*')
    .gte('edge_pct', minEdge)
    .order('edge_pct', { ascending: false })
    .limit(50)

  if (error) throw error
  return data ?? []
}

export async function insertValueBet(bet: Omit<ValueBet, 'id' | 'found_at'>): Promise<void> {
  const { error } = await createServiceClient()
    .from('value_bets')
    .insert(bet)
  if (error) throw error
}

// ─── User Profiles ────────────────────────────────────────────────────────────

export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  const { data, error } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', userId)
    .single()

  if (error) return null
  return data
}

export async function upsertUserProfile(
  profile: Omit<UserProfile, 'created_at'>
): Promise<void> {
  const { error } = await createServiceClient()
    .from('user_profiles')
    .upsert(profile, { onConflict: 'id' })
  if (error) throw error
}

// ─── Alerts ───────────────────────────────────────────────────────────────────

export async function getUserAlerts(userId: string): Promise<Alert[]> {
  const { data, error } = await supabase
    .from('alerts')
    .select('*')
    .eq('user_id', userId)
    .eq('active', true)

  if (error) throw error
  return data ?? []
}

export async function upsertAlert(alert: Omit<Alert, 'id' | 'created_at'>): Promise<void> {
  const { error } = await createServiceClient()
    .from('alerts')
    .upsert(alert)
  if (error) throw error
}

export async function deleteAlert(alertId: string): Promise<void> {
  const { error } = await createServiceClient()
    .from('alerts')
    .delete()
    .eq('id', alertId)
  if (error) throw error
}

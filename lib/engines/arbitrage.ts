import type { OddsSnapshot } from '../db/schema'

export type BestOdds = {
  bookmaker: string
  odds: number
}

export type ArbitrageResult = {
  event_id: string
  market: string
  home_best: BestOdds
  draw_best: BestOdds | null
  away_best: BestOdds
  implied_total: number   // sum of 1/best_odds — if < 1, arb exists
  profit_pct: number      // (1 - implied_total) * 100
  bookmakers: string[]
}

export type StakeSplit = {
  outcome: string
  bookmaker: string
  odds: number
  stake: number
  payout: number
}

/**
 * Given a flat list of snapshots (potentially multiple per bookmaker per event),
 * detect all arbitrage opportunities across bookmakers.
 */
export function detectArbitrage(snapshots: OddsSnapshot[]): ArbitrageResult[] {
  // Step 1: Deduplicate — keep most recent snapshot per bookmaker+event+market
  const latest = new Map<string, OddsSnapshot>()
  for (const snap of snapshots) {
    const key = `${snap.bookmaker}::${snap.event_id}::${snap.market}`
    const existing = latest.get(key)
    if (!existing || snap.timestamp > existing.timestamp) {
      latest.set(key, snap)
    }
  }

  // Step 2: Group by event_id + market
  const grouped = new Map<string, OddsSnapshot[]>()
  for (const snap of latest.values()) {
    const key = `${snap.event_id}::${snap.market}`
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(snap)
  }

  const results: ArbitrageResult[] = []

  for (const [key, group] of grouped) {
    // Need at least 2 bookmakers to have an arb
    const uniqueBooks = new Set(group.map((s) => s.bookmaker))
    if (uniqueBooks.size < 2) continue

    const [event_id, market] = key.split('::')

    // Find best odds for each outcome across all bookmakers
    let home_best: BestOdds = { bookmaker: '', odds: 0 }
    let draw_best: BestOdds | null = null
    let away_best: BestOdds = { bookmaker: '', odds: 0 }

    for (const snap of group) {
      if (snap.home_odds > home_best.odds) {
        home_best = { bookmaker: snap.bookmaker, odds: snap.home_odds }
      }
      if (snap.away_odds > away_best.odds) {
        away_best = { bookmaker: snap.bookmaker, odds: snap.away_odds }
      }
      if (snap.draw_odds != null && snap.draw_odds > (draw_best?.odds ?? 0)) {
        draw_best = { bookmaker: snap.bookmaker, odds: snap.draw_odds }
      }
    }

    if (home_best.odds < 1.01 || away_best.odds < 1.01) continue

    const implied_total =
      1 / home_best.odds +
      1 / away_best.odds +
      (draw_best ? 1 / draw_best.odds : 0)

    if (implied_total >= 1) continue // No arbitrage

    const profit_pct = (1 - implied_total) * 100
    const bookmakers = Array.from(
      new Set([home_best.bookmaker, away_best.bookmaker, ...(draw_best ? [draw_best.bookmaker] : [])])
    )

    results.push({ event_id, market, home_best, draw_best, away_best, implied_total, profit_pct, bookmakers })
  }

  return results.sort((a, b) => b.profit_pct - a.profit_pct)
}

/**
 * Calculate optimal stake splits for a given bankroll on an arb opportunity.
 * Each stake is proportional to the outcome's implied probability so that
 * every possible outcome returns the same guaranteed profit.
 */
export function calculateStakes(arb: ArbitrageResult, bankroll: number): StakeSplit[] {
  const outcomes: { label: string; best: BestOdds }[] = [
    { label: 'Home', best: arb.home_best },
    { label: 'Away', best: arb.away_best },
    ...(arb.draw_best ? [{ label: 'Draw', best: arb.draw_best }] : []),
  ]

  return outcomes.map(({ label, best }) => {
    const stake = Math.round((1 / best.odds / arb.implied_total) * bankroll)
    return {
      outcome: label,
      bookmaker: best.bookmaker,
      odds: best.odds,
      stake,
      payout: Math.round(stake * best.odds),
    }
  })
}

'use client'
import { useState, useEffect, useCallback } from 'react'
import type { ArbitrageResult } from '@/lib/engines/arbitrage'
import ArbitrageCard from '@/components/arbitrage/ArbitrageCard'

export default function ArbitragePage() {
  const [opportunities, setOpportunities] = useState<ArbitrageResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [minProfit, setMinProfit] = useState(0)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchArbitrage = useCallback(async () => {
    try {
      const res = await fetch(`/api/arbitrage?minProfit=${minProfit}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setOpportunities(json.data ?? [])
      setLastUpdated(new Date())
      setError(null)
    } catch (e) {
      setError('Failed to load opportunities')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [minProfit])

  useEffect(() => {
    setLoading(true)
    fetchArbitrage()
    const interval = setInterval(fetchArbitrage, 30_000)
    return () => clearInterval(interval)
  }, [fetchArbitrage])

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Arbitrage Engine</h1>
          <p className="text-muted-foreground mt-1">
            Guaranteed-profit opportunities across 8 bookmakers
          </p>
        </div>
        <div className="text-right text-xs text-muted-foreground shrink-0">
          {lastUpdated && <p>Updated {lastUpdated.toLocaleTimeString()}</p>}
          <p>Auto-refreshes every 30s</p>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-4">
        <label className="text-sm text-muted-foreground">Min profit</label>
        <select
          value={minProfit}
          onChange={(e) => setMinProfit(Number(e.target.value))}
          className="bg-muted border border-border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:border-primary"
        >
          <option value={0}>Any</option>
          <option value={0.5}>≥ 0.5%</option>
          <option value={1}>≥ 1%</option>
          <option value={2}>≥ 2%</option>
          <option value={5}>≥ 5%</option>
        </select>
        <span className="text-xs text-muted-foreground">
          {loading ? 'Loading...' : `${opportunities.length} found`}
        </span>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && opportunities.length === 0 && (
        <div className="rounded-xl border border-border bg-card p-12 text-center">
          <p className="text-4xl mb-4">⇄</p>
          <p className="text-muted-foreground text-sm">
            No arbitrage found right now — checking every 5 min
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            Need odds from 2+ bookmakers on the same event
          </p>
        </div>
      )}

      {/* Results grid */}
      {opportunities.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {opportunities.map((arb) => (
            <ArbitrageCard key={`${arb.event_id}::${arb.market}`} arb={arb} />
          ))}
        </div>
      )}
    </div>
  )
}

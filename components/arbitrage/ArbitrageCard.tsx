import type { ArbitrageResult } from '@/lib/engines/arbitrage'
import StakeCalculator from './StakeCalculator'

interface Props {
  arb: ArbitrageResult
}

export default function ArbitrageCard({ arb }: Props) {
  const [home, away] = arb.event_id.split('_').slice(0, 2).join(' ').split('-vs-')

  return (
    <div className="rounded-xl border border-border bg-card p-6 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
            {arb.market} &middot; {arb.bookmakers.join(' vs ')}
          </p>
          <h3 className="font-semibold truncate">{arb.event_id.replace(/_/g, ' ')}</h3>
        </div>
        <div className="text-right shrink-0">
          <span className="text-2xl font-bold text-emerald-400">
            +{arb.profit_pct.toFixed(2)}%
          </span>
          <p className="text-xs text-muted-foreground">guaranteed</p>
        </div>
      </div>

      {/* Best odds per outcome */}
      <div className={`grid gap-2 text-center text-sm ${arb.draw_best ? 'grid-cols-3' : 'grid-cols-2'}`}>
        <div className="rounded-lg bg-muted p-2.5 border border-border">
          <p className="text-xs text-muted-foreground mb-1">Home</p>
          <p className="font-bold text-base">{arb.home_best.odds.toFixed(2)}</p>
          <p className="text-xs text-muted-foreground truncate">{arb.home_best.bookmaker}</p>
        </div>
        {arb.draw_best && (
          <div className="rounded-lg bg-muted p-2.5 border border-border">
            <p className="text-xs text-muted-foreground mb-1">Draw</p>
            <p className="font-bold text-base">{arb.draw_best.odds.toFixed(2)}</p>
            <p className="text-xs text-muted-foreground truncate">{arb.draw_best.bookmaker}</p>
          </div>
        )}
        <div className="rounded-lg bg-muted p-2.5 border border-border">
          <p className="text-xs text-muted-foreground mb-1">Away</p>
          <p className="font-bold text-base">{arb.away_best.odds.toFixed(2)}</p>
          <p className="text-xs text-muted-foreground truncate">{arb.away_best.bookmaker}</p>
        </div>
      </div>

      {/* Stake calculator */}
      <div className="border-t border-border pt-4">
        <StakeCalculator arb={arb} />
      </div>
    </div>
  )
}

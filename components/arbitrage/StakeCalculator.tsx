'use client'
import { useState } from 'react'
import type { ArbitrageResult, StakeSplit } from '@/lib/engines/arbitrage'
import { calculateStakes } from '@/lib/engines/arbitrage'

interface Props {
  arb: ArbitrageResult
}

export default function StakeCalculator({ arb }: Props) {
  const [bankroll, setBankroll] = useState(5000)
  const stakes: StakeSplit[] = calculateStakes(arb, bankroll)
  const guaranteedProfit = Math.round(bankroll * (1 / arb.implied_total - 1))

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <label className="text-xs text-muted-foreground whitespace-nowrap">Bankroll (KES)</label>
        <input
          type="number"
          value={bankroll}
          onChange={(e) => setBankroll(Math.max(100, Number(e.target.value)))}
          className="flex-1 bg-muted rounded-md px-3 py-1.5 text-sm border border-border focus:outline-none focus:border-primary"
          min={100}
          step={500}
        />
      </div>

      <div className="space-y-1.5">
        {stakes.map((s) => (
          <div key={s.outcome} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground w-8">{s.outcome}</span>
              <span className="text-xs bg-muted px-1.5 py-0.5 rounded border border-border">
                {s.bookmaker}
              </span>
              <span className="text-xs text-muted-foreground">@ {s.odds.toFixed(2)}</span>
            </div>
            <div className="text-right">
              <span className="font-medium">KES {s.stake.toLocaleString()}</span>
              <span className="text-xs text-muted-foreground ml-1">
                → {s.payout.toLocaleString()}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-between text-sm border-t border-border pt-2">
        <span className="text-muted-foreground">Guaranteed profit</span>
        <span className="font-bold text-emerald-400">
          KES {guaranteedProfit.toLocaleString()}
        </span>
      </div>
    </div>
  )
}

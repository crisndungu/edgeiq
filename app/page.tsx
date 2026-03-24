import Link from 'next/link'

const engines = [
  {
    href: '/arbitrage',
    title: 'Arbitrage Engine',
    description: 'Guaranteed-profit opportunities across 8 bookmakers. Exact stake splits calculated.',
    icon: '⇄',
    stat: '—',
    statLabel: 'Active opportunities',
    color: 'text-emerald-400',
  },
  {
    href: '/value-bets',
    title: 'Value Betting',
    description: 'AI-estimated true probability vs bookmaker odds. Surface mispriced markets.',
    icon: '◎',
    stat: '—',
    statLabel: 'Value bets found today',
    color: 'text-yellow-400',
  },
  {
    href: '/odds-tracker',
    title: 'Odds Movement',
    description: 'Real-time line movement. Sharp money, public bias, and steam move signals.',
    icon: '▲',
    stat: '—',
    statLabel: 'Movements tracked',
    color: 'text-blue-400',
  },
  {
    href: '/bankroll',
    title: 'Bankroll Optimizer',
    description: 'Kelly Criterion stake sizing. Prevent ruin, maximize long-term EV.',
    icon: '◆',
    stat: '—',
    statLabel: 'Expected value',
    color: 'text-purple-400',
  },
]

const bookmakers = ['Betika', 'SportPesa', 'Mozzart', '1xBet', 'Sportybet', 'Betpawa', 'Paripesa', 'OddsPortal']

export default function DashboardPage() {
  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Market intelligence across {bookmakers.length} Kenyan bookmakers
        </p>
      </div>

      {/* Bookmaker status bar */}
      <div className="flex flex-wrap gap-2">
        {bookmakers.map((bm) => (
          <span
            key={bm}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-primary inline-block" />
            {bm}
          </span>
        ))}
      </div>

      {/* Engine cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {engines.map((engine) => (
          <Link
            key={engine.href}
            href={engine.href}
            className="group block rounded-xl border border-border bg-card p-6 hover:border-primary/50 hover:bg-card/80 transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <span className={`text-2xl ${engine.color}`}>{engine.icon}</span>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-md">
                Live
              </span>
            </div>
            <h2 className="text-lg font-semibold mb-1 group-hover:text-primary transition-colors">
              {engine.title}
            </h2>
            <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
              {engine.description}
            </p>
            <div className="border-t border-border pt-4">
              <span className={`text-2xl font-bold ${engine.color}`}>{engine.stat}</span>
              <span className="text-xs text-muted-foreground ml-2">{engine.statLabel}</span>
            </div>
          </Link>
        ))}
      </div>

      {/* Data notice */}
      <p className="text-xs text-muted-foreground border-t border-border pt-4">
        EdgeIQ is a market intelligence tool. It does not predict outcomes or guarantee winnings.
        All data is for informational purposes only.
      </p>
    </div>
  )
}

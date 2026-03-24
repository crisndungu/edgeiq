export default function ArbitragePage() {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Arbitrage Engine</h1>
        <p className="text-muted-foreground mt-1">Guaranteed-profit opportunities across 8 bookmakers</p>
      </div>
      <div className="rounded-xl border border-border bg-card p-12 text-center">
        <p className="text-4xl mb-4">⇄</p>
        <p className="text-muted-foreground text-sm">No arbitrage found right now — checking every 5 min</p>
        <p className="text-xs text-muted-foreground mt-2">Scraper and detection engine coming in Phase D &amp; E</p>
      </div>
    </div>
  )
}

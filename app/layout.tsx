import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import Link from 'next/link'
import './globals.css'

const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] })
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'EdgeIQ — Betting Intelligence',
  description: 'Arbitrage, value bets, odds movement & bankroll optimization for Kenyan bettors',
}

const navItems = [
  { href: '/', label: 'Dashboard', icon: '◈' },
  { href: '/arbitrage', label: 'Arbitrage', icon: '⇄' },
  { href: '/value-bets', label: 'Value Bets', icon: '◎' },
  { href: '/odds-tracker', label: 'Odds Tracker', icon: '▲' },
  { href: '/bankroll', label: 'Bankroll', icon: '◆' },
  { href: '/alerts', label: 'Alerts', icon: '◉' },
]

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full`}>
      <body className="h-full flex bg-background text-foreground antialiased">
        {/* Sidebar */}
        <aside className="w-60 shrink-0 flex flex-col border-r border-border bg-sidebar">
          {/* Logo */}
          <div className="px-6 py-5 border-b border-border">
            <span className="text-xl font-bold tracking-tight text-primary">Edge</span>
            <span className="text-xl font-bold tracking-tight text-foreground">IQ</span>
            <p className="text-xs text-muted-foreground mt-0.5">Betting Intelligence</p>
          </div>

          {/* Nav */}
          <nav className="flex-1 px-3 py-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-primary transition-colors"
              >
                <span className="text-primary w-4 text-center">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-border">
            <p className="text-xs text-muted-foreground">8 bookmakers tracked</p>
            <p className="text-xs text-muted-foreground">Updating every 5 min</p>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 flex flex-col min-h-0 overflow-auto">
          {children}
        </main>
      </body>
    </html>
  )
}

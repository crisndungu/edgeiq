# EDGEIQ — AI Betting Intelligence Engine

## Project Overview
EdgeIQ is a betting intelligence platform for Kenyan bettors. It tracks odds
across 8 bookmakers (Betika, SportPesa, Mozzart Bet, 1xBet, Sportybet,
Betpawa, Paripesa, OddsPortal), detects arbitrage opportunities, surfaces
value bets, tracks line movement, and optimizes bankroll using Kelly Criterion.
This is NOT a prediction app. It is a market intelligence tool.

## Tech Stack
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
- Database: PostgreSQL via Supabase (free tier)
- Scraping: Python + Playwright (separate service, runs on Railway)
- Queue: Redis + BullMQ for scheduled scrape jobs
- Alerts: Telegram Bot API
- Auth: Supabase Auth (email + phone OTP)
- Payments: Flutterwave (M-Pesa KES support)
- Deploy: Vercel (frontend), Railway (scraper + queue)

## Architecture Rules
- Keep all pages in /app directory (Next.js App Router)
- Components in /components organized by feature (arbitrage/, value/, odds/, bankroll/)
- Database schema in /lib/db/schema.ts (single source of truth)
- API routes in /app/api/ with proper error handling + rate limiting
- Scraper lives in /scraper/ directory — never mix with Next.js code
- Environment variables in .env.local (NEVER commit this file)
- All monetary values stored in integers (KES cents, not decimals)

## Code Style
- TypeScript strict mode for all .ts and .tsx files
- Functional components only — no class components
- async/await always — never raw .then() chains
- Every API route: try/catch with proper error codes
- Files in kebab-case: arbitrage-detector.ts
- Components in PascalCase: ArbitrageCard.tsx
- Files under 200 lines — split if longer
- No inline styles — Tailwind classes only

## Bookmakers Tracked
Betika | SportPesa | Mozzart Bet | 1xBet | Sportybet | Betpawa | Paripesa | OddsPortal
All odds normalized to decimal format. Market names normalized to canonical form.

## Build Commands
- Dev: npm run dev
- Build: npm run build
- Lint: npm run lint
- Scraper dev: cd scraper && python main.py

## Critical Constraints
- Do NOT modify working features when adding new ones
- Always run npm run dev after changes to verify nothing broke
- Ask before installing new dependencies
- Scraper must use rotating proxies — never hit a bookmaker from the same IP twice in 60s
- Never store raw HTML — only normalized JSON odds data
- All alert thresholds configurable per user in the database
- Odds data older than 48h should be archived, not deleted

## Current Status
Phase: E — Arbitrage Detection Engine
Completed: [Phase A: Next.js init, shadcn, deps | Phase B: layout, dashboard, nav, stub pages | Phase C: schema.ts, queries.ts, supabase.ts | Phase D: Betika scraper (api.betika.com/v1/uo/matches), OddsPortal scraper (Nuxt state extraction, WIP)]
In Progress: Phase E — arbitrage engine, ArbitrageCard, StakeCalculator, /arbitrage page wired up
Blocked: OddsPortal API responses are base64-encrypted — DOM extraction fallback in place

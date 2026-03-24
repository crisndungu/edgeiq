"""
EdgeIQ Scraper - Entry point and scheduler.
Runs OddsPortal + Betika every 5 minutes, writes to Supabase.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from supabase import create_client, Client

# Add scraper root to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))

SUPABASE_URL = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_scrapers():
    from scrapers.betika import BetikaScraper
    from scrapers.sportpesa import SportPesaScraper
    from scrapers.mozzart import MozzartScraper
    from scrapers.oneXbet import OneXBetScraper
    from scrapers.sportybet import SportybetScraper
    from scrapers.betpawa import BetpawaScraper
    from scrapers.paripesa import ParipesaScraper
    return [
        BetikaScraper(),
        SportPesaScraper(),
        MozzartScraper(),
        OneXBetScraper(),
        SportybetScraper(),
        BetpawaScraper(),
        ParipesaScraper(),
    ]


async def run_scraper(scraper) -> int:
    rows = await scraper.scrape()
    if not rows:
        return 0

    # Upsert events first (FK constraint requires event to exist before snapshot)
    seen_events: set[str] = set()
    events_payload = []
    for r in rows:
        if r.event_id not in seen_events and r.home_team and r.away_team:
            seen_events.add(r.event_id)
            events_payload.append(r.to_event_dict())

    if events_payload:
        supabase.table("events").upsert(events_payload, on_conflict="id").execute()
        print(f"[{scraper.name}] Upserted {len(events_payload)} events")

    payload = [r.to_dict() for r in rows]
    result = supabase.table("odds_snapshots").insert(payload).execute()
    inserted = len(result.data) if result.data else 0
    print(f"[{scraper.name}] Inserted {inserted} rows into odds_snapshots")
    return inserted


def scrape_cycle():
    print("\n--- Scrape cycle starting ---")
    scrapers = get_scrapers()

    async def run_all():
        total = 0
        for scraper in scrapers:
            count = await run_scraper(scraper)
            total += count
        print(f"--- Cycle complete: {total} total rows inserted ---\n")

    asyncio.run(run_all())


if __name__ == "__main__":
    print("EdgeIQ Scraper starting...")
    print(f"Supabase: {SUPABASE_URL}")

    # Run once immediately on start
    scrape_cycle()

    # Then schedule every 5 minutes
    scheduler = BlockingScheduler()
    scheduler.add_job(scrape_cycle, "interval", minutes=5)
    print("Scheduler running - scraping every 5 minutes. Ctrl+C to stop.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scraper stopped.")

"""
OddsPortal scraper — intercepts their internal API responses.
Targets soccer pre-match odds for upcoming matches.
"""
import json
import re
from datetime import datetime, timezone

from playwright.async_api import Route, Request

from scrapers.base_scraper import BaseScraper, OddsRow
from normalizer.odds_normalizer import normalize
from normalizer.event_matcher import make_event_id

BASE_URL = "https://www.oddsportal.com/football/"
API_PATTERN = re.compile(r"oddsportal\.com/ajax-")

BOOKMAKER_NAME = "OddsPortal"


class OddsPortalScraper(BaseScraper):
    name = "oddsportal"

    async def _fetch(self) -> list[OddsRow]:
        page = await self._new_page()
        captured: list[dict] = []

        async def handle_route(route: Route, request: Request) -> None:
            if "oddsportal.com" in request.url:
                print(f"[oddsportal] req: {request.url}")
            if not API_PATTERN.search(request.url):
                await route.continue_()
                return
            try:
                response = await route.fetch()
                try:
                    body = await response.json()
                    captured.append({"url": request.url, "body": body})
                    print(f"[oddsportal] captured JSON from {request.url}")
                except Exception as je:
                    raw = await response.text()
                    print(f"[oddsportal] JSON error {request.url}: {je} | raw({len(raw)}): {raw[:200]!r}")
                await route.fulfill(response=response)
            except Exception as fe:
                print(f"[oddsportal] fetch error {request.url}: {fe}")
                await route.continue_()

        await page.route("**/*", handle_route)

        print(f"[{self.name}] Loading {BASE_URL}")
        await page.goto(BASE_URL, wait_until="load", timeout=30000)

        content = await page.content()
        if self._is_banned(content):
            print(f"[{self.name}] Ban detected — skipping")
            return []

        # Wait a bit for XHR calls to fire
        await page.wait_for_timeout(4000)
        await page.close()

        print(f"[{self.name}] Captured {len(captured)} ajax responses: {[c['url'] for c in captured]}")
        rows = self._parse(captured)
        print(f"[{self.name}] Got {len(rows)} odds rows")
        return rows

    def _parse(self, captured: list[dict]) -> list[OddsRow]:
        rows: list[OddsRow] = []

        for item in captured:
            body = item["body"]
            events = []

            # OddsPortal wraps events in different keys depending on endpoint
            if isinstance(body, dict):
                events = (
                    body.get("data", {}).get("rows", [])
                    or body.get("d", {}).get("rows", [])
                    or []
                )

            for event in events:
                try:
                    home = event.get("home-name") or event.get("homeName", "")
                    away = event.get("away-name") or event.get("awayName", "")
                    start_ts = event.get("date-start-timestamp") or event.get("dateStartTimestamp", 0)
                    start_time = datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat()

                    odds_data = event.get("odds", {})
                    # 1X2 market: keys '1', 'X', '2'
                    home_odds = normalize(float(odds_data.get("1", 0) or 0))
                    draw_odds = normalize(float(odds_data.get("X", 0) or 0))
                    away_odds = normalize(float(odds_data.get("2", 0) or 0))

                    if home_odds < 1.01 or away_odds < 1.01:
                        continue

                    event_id = make_event_id(home, away, start_time)

                    rows.append(OddsRow(
                        bookmaker=BOOKMAKER_NAME,
                        event_id=event_id,
                        market="1X2",
                        home_odds=home_odds,
                        away_odds=away_odds,
                        draw_odds=draw_odds if draw_odds > 1.01 else None,
                    ))
                except Exception as e:
                    print(f"[{self.name}] Parse error on event: {e}")
                    continue

        return rows

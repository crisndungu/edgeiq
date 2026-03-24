"""
OddsPortal scraper — extracts event data from Nuxt app state after page render.
OddsPortal encrypts all /ajax- responses, so we read from window.__nuxt__ instead.
"""
import json
import re
from datetime import datetime, timezone

from playwright.async_api import Page

from scrapers.base_scraper import BaseScraper, OddsRow
from normalizer.odds_normalizer import normalize
from normalizer.event_matcher import make_event_id

BASE_URL = "https://www.oddsportal.com/football/"
BOOKMAKER_NAME = "OddsPortal"


class OddsPortalScraper(BaseScraper):
    name = "oddsportal"

    async def _fetch(self) -> list[OddsRow]:
        page = await self._new_page()

        print(f"[{self.name}] Loading {BASE_URL}")
        await page.goto(BASE_URL, wait_until="load", timeout=45000)

        content = await page.content()
        if self._is_banned(content):
            print(f"[{self.name}] Ban detected — skipping")
            return []

        # Wait for Vue/Nuxt to hydrate and render event rows
        await page.wait_for_timeout(5000)

        # Try extracting from Nuxt app state
        events = await self._extract_nuxt_events(page)
        if not events:
            # Fallback: parse from rendered DOM
            events = await self._extract_dom_events(page)

        await page.close()
        rows = self._parse(events)
        print(f"[{self.name}] Got {len(rows)} odds rows")
        return rows

    async def _extract_nuxt_events(self, page: Page) -> list[dict]:
        """Pull event data from Nuxt/Vue app state."""
        try:
            raw = await page.evaluate("""
                () => {
                    // Nuxt 3 stores payload in window.__nuxt__ or useNuxtApp
                    const sources = [
                        window.__NUXT__,
                        window.__nuxt__,
                        window.pageVar,
                    ];
                    for (const src of sources) {
                        if (src && typeof src === 'object') {
                            return JSON.stringify(src);
                        }
                    }
                    // Try finding data in script tags
                    for (const el of document.querySelectorAll('script[type="application/json"]')) {
                        try { return el.textContent; } catch(e) {}
                    }
                    return null;
                }
            """)
            if not raw:
                print(f"[{self.name}] No Nuxt state found")
                return []
            data = json.loads(raw)
            return self._dig_events(data)
        except Exception as e:
            print(f"[{self.name}] Nuxt extract error: {e}")
            return []

    def _dig_events(self, obj, depth=0) -> list[dict]:
        """Recursively search for event arrays in Nuxt state."""
        if depth > 10:
            return []
        if isinstance(obj, list):
            # Check if this list looks like events (has home/away team keys)
            if obj and isinstance(obj[0], dict):
                keys = set(obj[0].keys())
                if keys & {"home-name", "homeName", "homeTeam", "home_team"}:
                    return obj
            results = []
            for item in obj[:20]:  # don't go too deep on large arrays
                results.extend(self._dig_events(item, depth + 1))
            return results
        if isinstance(obj, dict):
            results = []
            for v in obj.values():
                results.extend(self._dig_events(v, depth + 1))
            return results
        return []

    async def _extract_dom_events(self, page: Page) -> list[dict]:
        """Extract event data from rendered DOM rows as fallback."""
        try:
            events = await page.evaluate("""
                () => {
                    const rows = [];
                    // OddsPortal renders match rows with data attributes
                    document.querySelectorAll('[data-id]').forEach(el => {
                        const home = el.querySelector('[class*="home"]')?.textContent?.trim();
                        const away = el.querySelector('[class*="away"]')?.textContent?.trim();
                        const odds = Array.from(el.querySelectorAll('[class*="odds"]'))
                            .map(o => parseFloat(o.textContent));
                        if (home && away && odds.length >= 2) {
                            rows.push({
                                homeName: home,
                                awayName: away,
                                odds: { '1': odds[0], 'X': odds[1], '2': odds[2] },
                                dateStartTimestamp: 0,
                            });
                        }
                    });
                    return rows;
                }
            """)
            print(f"[{self.name}] DOM extraction found {len(events)} rows")
            return events or []
        except Exception as e:
            print(f"[{self.name}] DOM extract error: {e}")
            return []

    def _parse(self, events: list[dict]) -> list[OddsRow]:
        rows: list[OddsRow] = []

        for event in events:
            try:
                home = event.get("home-name") or event.get("homeName", "")
                away = event.get("away-name") or event.get("awayName", "")
                start_ts = event.get("date-start-timestamp") or event.get("dateStartTimestamp", 0)

                if not home or not away:
                    continue

                start_time = (
                    datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat()
                    if start_ts
                    else datetime.now(timezone.utc).isoformat()
                )

                odds_data = event.get("odds", {})
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
                print(f"[{self.name}] Parse error: {e}")
                continue

        return rows

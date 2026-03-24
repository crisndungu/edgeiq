"""
Betika scraper - intercepts their internal API calls via network interception.
Betika loads odds dynamically via XHR, so we capture those directly.
"""
import json
from datetime import datetime, timezone

from playwright.async_api import Route, Request

from scrapers.base_scraper import BaseScraper, OddsRow
from normalizer.odds_normalizer import normalize
from normalizer.event_matcher import make_event_id

BASE_URL = "https://www.betika.com/en-ke/s/prematch"
API_HOST = "api.betika.com"
BOOKMAKER_NAME = "Betika"


class BetikaScraper(BaseScraper):
    name = "betika"

    async def _fetch(self) -> list[OddsRow]:
        page = await self._new_page()
        captured: list[dict] = []

        async def handle_route(route: Route, request: Request) -> None:
            # Log all XHR/fetch requests to find actual API endpoints
            if request.resource_type in ("xhr", "fetch"):
                print(f"[betika] {request.resource_type}: {request.url}")
            if API_HOST not in request.url or "/v1/uo/matches" not in request.url:
                await route.continue_()
                return
            try:
                response = await route.fetch()
                try:
                    body = await response.json()
                    captured.append(body)
                except Exception:
                    pass
                await route.fulfill(response=response)
            except Exception:
                await route.continue_()

        await page.route("**/*", handle_route)

        print(f"[{self.name}] Loading {BASE_URL}")
        await page.goto(BASE_URL, wait_until="commit", timeout=30000)

        # Wait for DOM to hydrate before accessing document.body
        await page.wait_for_timeout(5000)

        content = await page.content()
        if self._is_banned(content):
            print(f"[{self.name}] Ban detected - skipping")
            return []

        # Scroll to trigger lazy-loaded content and wait for API calls
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(6000)
        await page.close()

        if captured:
            import json
            print(f"[betika] sample response keys: {list(captured[0].keys())}")
            sample = (captured[0].get("data") or [{}])
            if sample:
                print(f"[betika] sample event keys: {list(sample[0].keys())}")
                print(f"[betika] sample event: {json.dumps(sample[0], default=str)[:500]}")

        rows = self._parse(captured)
        print(f"[{self.name}] Got {len(rows)} odds rows")
        return rows

    def _parse(self, captured: list[dict]) -> list[OddsRow]:
        rows: list[OddsRow] = []

        for body in captured:
            data = body.get("data", [])
            if not isinstance(data, list):
                continue

            for event in data:
                try:
                    home = event.get("home_team", "")
                    away = event.get("away_team", "")
                    start_str = event.get("start_time", "")

                    if not home or not away or not start_str:
                        continue

                    # Betika start_time: "2024-03-25 15:00:00"
                    try:
                        dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                        start_time = dt.replace(tzinfo=timezone.utc).isoformat()
                    except ValueError:
                        start_time = start_str

                    picks = event.get("picks", [])
                    odds_map: dict[str, float] = {}
                    for pick in picks:
                        special_bet_value = pick.get("special_bet_value", "")
                        odd_value = pick.get("odd_value", 0)
                        if special_bet_value and odd_value:
                            odds_map[str(special_bet_value).strip()] = float(odd_value)

                    home_odds = normalize(odds_map.get("1", 0))
                    draw_odds = normalize(odds_map.get("X", 0))
                    away_odds = normalize(odds_map.get("2", 0))

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

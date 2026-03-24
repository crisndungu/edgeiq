"""
Betika scraper - intercepts their internal API calls via network interception.
Betika loads odds dynamically via XHR, so we capture those directly.
"""
import json
from datetime import datetime, timezone
from typing import Any, cast

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
        captured: list[dict[str, Any]] = []

        async def handle_route(route: Route, request: Request) -> None:
            if request.resource_type in ("xhr", "fetch"):
                print(f"[betika] {request.resource_type}: {request.url}")
            if API_HOST not in request.url or "/v1/uo/matches" not in request.url:
                await route.continue_()
                return
            try:
                response = await route.fetch()
                try:
                    body: dict[str, Any] = await response.json()
                    captured.append(body)
                except Exception:
                    pass
                await route.fulfill(response=response)
            except Exception:
                await route.continue_()

        await page.route("**/*", handle_route)
        print(f"[{self.name}] Loading {BASE_URL}")
        await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        content = await page.content()
        if self._is_banned(content):
            print(f"[{self.name}] Ban detected - skipping")
            return []

        await page.close()

        if captured:
            print(f"[betika] sample response keys: {list(captured[0].keys())}")
            raw: Any = captured[0].get("data") or [{}]
            sample: list[dict[str, Any]] = cast(list[dict[str, Any]], raw) if isinstance(raw, list) else [{}]
            if sample:
                print(f"[betika] sample event keys: {list(sample[0].keys())}")
                print(f"[betika] sample event: {json.dumps(sample[0], default=str)[:500]}")

        rows = self._parse(captured)
        print(f"[{self.name}] Got {len(rows)} odds rows")
        return rows

    def _parse(self, captured: list[dict[str, Any]]) -> list[OddsRow]:
        rows: list[OddsRow] = []

        for body in captured:
            raw: Any = body.get("data") or []
            data: list[dict[str, Any]] = cast(list[dict[str, Any]], raw) if isinstance(raw, list) else []

            for event in data:
                try:
                    home: str = str(event.get("home_team") or "")
                    away: str = str(event.get("away_team") or "")
                    start_str: str = str(event.get("start_time") or "")

                    if not home or not away or not start_str:
                        continue

                    try:
                        dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                        start_time = dt.replace(tzinfo=timezone.utc).isoformat()
                    except ValueError:
                        start_time = start_str

                    home_odds = normalize(float(event.get("home_odd") or 0))
                    draw_odds = normalize(float(event.get("neutral_odd") or 0))
                    away_odds = normalize(float(event.get("away_odd") or 0))

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
                        home_team=home,
                        away_team=away,
                        start_time=start_time,
                    ))
                except Exception as e:
                    print(f"[{self.name}] Parse error on event: {e}")
                    continue

        return rows

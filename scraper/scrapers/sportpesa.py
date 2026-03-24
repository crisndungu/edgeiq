"""
SportPesa scraper - intercepts their internal API calls.
"""
import json
from datetime import datetime, timezone
from typing import Any, cast

from playwright.async_api import Route, Request

from scrapers.base_scraper import BaseScraper, OddsRow
from normalizer.odds_normalizer import normalize
from normalizer.event_matcher import make_event_id

BASE_URL = "https://www.sportpesa.co.ke/sports/soccer"
API_HOSTS = ("sportpesa.co.ke", "sportpesa.com")
BOOKMAKER_NAME = "SportPesa"


class SportPesaScraper(BaseScraper):
    name = "sportpesa"

    async def _fetch(self) -> list[OddsRow]:
        page = await self._new_page()
        captured: list[dict[str, Any]] = []

        async def handle_route(route: Route, request: Request) -> None:
            if request.resource_type in ("xhr", "fetch"):
                print(f"[sportpesa] {request.resource_type}: {request.url[:100]}")
            if not any(h in request.url for h in API_HOSTS):
                await route.continue_()
                return
            try:
                response = await route.fetch()
                try:
                    body: Any = await response.json()
                    captured.append({"url": request.url, "body": body})
                except Exception:
                    pass
                await route.fulfill(response=response)
            except Exception:
                await route.continue_()

        await page.route("**/*", handle_route)
        print(f"[{self.name}] Loading {BASE_URL}")
        await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        await page.close()

        if captured:
            print(f"[sportpesa] captured {len(captured)} responses")
            for item in captured[:5]:
                events = _extract_events(item["body"])
                if len(events) > 3:
                    print(f"[sportpesa] found {len(events)} items at: {item['url'][:80]}")
                    print(f"[sportpesa] keys: {list(events[0].keys())}")
                    print(f"[sportpesa] sample: {json.dumps(events[0], default=str)[:400]}")
                    break

        rows = self._parse(captured)
        print(f"[{self.name}] Got {len(rows)} odds rows")
        return rows

    def _parse(self, captured: list[dict[str, Any]]) -> list[OddsRow]:
        rows: list[OddsRow] = []
        for item in captured:
            body: Any = item["body"]
            events: list[dict[str, Any]] = _extract_events(body)
            if len(events) < 2:
                continue
            for event in events:
                try:
                    home: str = str(event.get("home_team") or event.get("home") or
                                    event.get("homeName") or event.get("homeTeam") or "")
                    away: str = str(event.get("away_team") or event.get("away") or
                                    event.get("awayName") or event.get("awayTeam") or "")
                    start_raw: Any = (event.get("start_time") or event.get("startTime") or
                                      event.get("start_date") or "")
                    if not home or not away:
                        continue
                    try:
                        dt = datetime.strptime(str(start_raw)[:19], "%Y-%m-%d %H:%M:%S")
                        start_time = dt.replace(tzinfo=timezone.utc).isoformat()
                    except Exception:
                        start_time = str(start_raw)
                    home_odds = normalize(float(event.get("home_odd") or event.get("odds1") or event.get("1") or 0))
                    draw_odds = normalize(float(event.get("neutral_odd") or event.get("oddsX") or event.get("X") or 0))
                    away_odds = normalize(float(event.get("away_odd") or event.get("odds2") or event.get("2") or 0))
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
                    print(f"[{self.name}] parse error: {e}")
        return rows


def _extract_events(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return cast(list[dict[str, Any]], body)
    if not isinstance(body, dict):
        return []
    body_dict: dict[str, Any] = cast(dict[str, Any], body)
    for key in ("data", "events", "matches"):
        val: Any = body_dict.get(key)
        if isinstance(val, list):
            return cast(list[dict[str, Any]], val)
    return []

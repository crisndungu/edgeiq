"""
Sportybet scraper - intercepts their game service API.
"""
import json
from datetime import datetime, timezone
from typing import Any, cast

from playwright.async_api import Route, Request

from scrapers.base_scraper import BaseScraper, OddsRow
from normalizer.odds_normalizer import normalize
from normalizer.event_matcher import make_event_id

BASE_URL = "https://www.sportybet.com/ke/"
API_HOSTS = ("sportybet.com", "gameservice.sportybet.com")
BOOKMAKER_NAME = "Sportybet"


def _extract_events(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        if body and isinstance(body[0], dict):
            return cast(list[dict[str, Any]], body)
        return []
    if not isinstance(body, dict):
        return []
    body_dict: dict[str, Any] = cast(dict[str, Any], body)
    data: Any = body_dict.get("data")
    if isinstance(data, dict):
        data_dict: dict[str, Any] = cast(dict[str, Any], data)
        nested: Any = data_dict.get("events")
        if isinstance(nested, list):
            return cast(list[dict[str, Any]], nested)
    if isinstance(data, list):
        return cast(list[dict[str, Any]], data)
    for key in ("events", "tournaments"):
        val: Any = body_dict.get(key)
        if isinstance(val, list):
            return cast(list[dict[str, Any]], val)
    return []


class SportybetScraper(BaseScraper):
    name = "sportybet"

    async def _fetch(self) -> list[OddsRow]:
        page = await self._new_page()
        captured: list[dict[str, Any]] = []

        async def handle_route(route: Route, request: Request) -> None:
            if request.resource_type in ("xhr", "fetch"):
                print(f"[sportybet] {request.resource_type}: {request.url[:100]}")
            if not any(h in request.url for h in API_HOSTS):
                await route.continue_()
                return
            try:
                response = await route.fetch()
                try:
                    body: dict[str, Any] = await response.json()
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
            print(f"[sportybet] captured {len(captured)} responses")
            for item in captured[:5]:
                events = _extract_events(item["body"])
                if len(events) > 3:
                    print(f"[sportybet] found {len(events)} events at: {item['url'][:80]}")
                    print(f"[sportybet] keys: {list(events[0].keys())}")
                    print(f"[sportybet] sample: {json.dumps(events[0], default=str)[:400]}")
                    break

        rows = self._parse(captured)
        print(f"[{self.name}] Got {len(rows)} odds rows")
        return rows

    def _parse(self, captured: list[dict[str, Any]]) -> list[OddsRow]:
        rows: list[OddsRow] = []
        for item in captured:
            if "liveOrPrematch" not in item["url"] and "importantEvents" not in item["url"]:
                continue
            body: dict[str, Any] = item["body"]
            events: list[dict[str, Any]] = _extract_events(body)
            if len(events) < 2:
                continue
            for event in events:
                try:
                    home: str = (event.get("homeTeamName") or event.get("home_team") or
                                 event.get("home") or event.get("homeName") or "")
                    away: str = (event.get("awayTeamName") or event.get("away_team") or
                                 event.get("away") or event.get("awayName") or "")
                    start_raw: Any = (event.get("estimateStartTime") or event.get("startTime") or
                                      event.get("start_time") or 0)
                    if not home or not away:
                        continue
                    try:
                        if isinstance(start_raw, (int, float)) and start_raw > 1_000_000_000:
                            start_time = datetime.fromtimestamp(start_raw / 1000, tz=timezone.utc).isoformat()
                        else:
                            dt = datetime.strptime(str(start_raw)[:19], "%Y-%m-%d %H:%M:%S")
                            start_time = dt.replace(tzinfo=timezone.utc).isoformat()
                    except Exception:
                        start_time = str(start_raw)

                    home_odds = draw_odds = away_odds = 0.0
                    for market in cast(list[dict[str, Any]], event.get("markets") or []):
                        if market.get("id") not in ("1", 1) and "1X2" not in str(market.get("name", "")):
                            continue
                        for outcome in cast(list[dict[str, Any]], market.get("outcomes") or []):
                            desc: str = str(outcome.get("desc") or outcome.get("name") or "")
                            val = normalize(float(outcome.get("odds") or outcome.get("odds_value") or 0))
                            if desc in ("Home", "1", "W1"):
                                home_odds = val
                            elif desc in ("Draw", "X"):
                                draw_odds = val
                            elif desc in ("Away", "2", "W2"):
                                away_odds = val
                    if not home_odds:
                        home_odds = normalize(float(event.get("home_odd") or event.get("odds1") or 0))
                        draw_odds = normalize(float(event.get("neutral_odd") or event.get("oddsX") or 0))
                        away_odds = normalize(float(event.get("away_odd") or event.get("odds2") or 0))

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

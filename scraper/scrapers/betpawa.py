"""
Betpawa scraper - intercepts their internal API calls.
"""
import json
from datetime import datetime, timezone
from typing import Any, cast

from playwright.async_api import Route, Request

from scrapers.base_scraper import BaseScraper, OddsRow
from normalizer.odds_normalizer import normalize
from normalizer.event_matcher import make_event_id

BASE_URL = "https://www.betpawa.co.ke/events?sportId=1&marketId=1_1"
API_HOST = "betpawa.co.ke"
BOOKMAKER_NAME = "Betpawa"


def _extract_events(body: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("data", "events", "matches"):
        val: Any = body.get(key)
        if isinstance(val, list):
            return cast(list[dict[str, Any]], val)
    if isinstance(body, list):
        return cast(list[dict[str, Any]], body)
    return []


class BetpawaScraper(BaseScraper):
    name = "betpawa"

    async def _fetch(self) -> list[OddsRow]:
        page = await self._new_page()
        captured: list[dict[str, Any]] = []

        async def handle_route(route: Route, request: Request) -> None:
            if request.resource_type in ("xhr", "fetch"):
                print(f"[betpawa] {request.resource_type}: {request.url[:100]}")
            if API_HOST not in request.url:
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
            print(f"[betpawa] captured {len(captured)} responses")
            for item in captured:
                if "sportsbook" in item["url"] or "events" in item["url"]:
                    body = item["body"]
                    print(f"[betpawa] sportsbook url: {item['url'][:100]}")
                    print(f"[betpawa] sportsbook body type: {type(body).__name__}")
                    if isinstance(body, dict):
                        print(f"[betpawa] sportsbook keys: {list(body.keys())}")
                        print(f"[betpawa] sportsbook sample: {json.dumps(body, default=str)[:600]}")
                    elif isinstance(body, list) and body:
                        print(f"[betpawa] sportsbook list[0] keys: {list(body[0].keys()) if isinstance(body[0], dict) else type(body[0])}")
                        print(f"[betpawa] sportsbook list[0]: {json.dumps(body[0], default=str)[:400]}")

        rows = self._parse(captured)
        print(f"[{self.name}] Got {len(rows)} odds rows")
        return rows

    def _parse(self, captured: list[dict[str, Any]]) -> list[OddsRow]:
        rows: list[OddsRow] = []
        for item in captured:
            body: dict[str, Any] = item["body"]
            events: list[dict[str, Any]] = _extract_events(body)
            if len(events) < 2:
                continue
            for event in events:
                try:
                    home: str = str(event.get("homeTeam") or event.get("home_team") or
                                    event.get("home") or event.get("homeName") or "")
                    away: str = str(event.get("awayTeam") or event.get("away_team") or
                                    event.get("away") or event.get("awayName") or "")
                    start_raw: Any = event.get("startTime") or event.get("start_time") or event.get("date") or ""
                    if not home or not away:
                        continue
                    try:
                        dt = datetime.strptime(str(start_raw)[:19], "%Y-%m-%d %H:%M:%S")
                        start_time = dt.replace(tzinfo=timezone.utc).isoformat()
                    except Exception:
                        start_time = str(start_raw)

                    home_odds = draw_odds = away_odds = 0.0
                    for market in cast(list[dict[str, Any]], event.get("markets") or []):
                        if "1X2" not in str(market.get("name", "")) and market.get("id") not in ("1", 1):
                            continue
                        selections: list[dict[str, Any]] = cast(
                            list[dict[str, Any]],
                            market.get("selections") or market.get("outcomes") or []
                        )
                        for sel in selections:
                            tag: str = str(sel.get("tag") or sel.get("name") or sel.get("label") or "")
                            val = normalize(float(sel.get("odds") or sel.get("price") or 0))
                            if tag in ("1", "Home", "W1"):
                                home_odds = val
                            elif tag in ("X", "Draw"):
                                draw_odds = val
                            elif tag in ("2", "Away", "W2"):
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

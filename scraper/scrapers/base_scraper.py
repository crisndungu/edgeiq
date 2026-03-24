import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


# Minimum seconds between requests from the same IP
REQUEST_INTERVAL = 65

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]


class OddsRow:
    """Normalized odds row ready for Supabase insertion."""

    def __init__(
        self,
        bookmaker: str,
        event_id: str,
        market: str,
        home_odds: float,
        away_odds: float,
        draw_odds: Optional[float] = None,
        home_team: str = "",
        away_team: str = "",
        start_time: str = "",
        sport: str = "Football",
    ):
        self.bookmaker = bookmaker
        self.event_id = event_id
        self.market = market
        self.home_odds = home_odds
        self.away_odds = away_odds
        self.draw_odds = draw_odds
        self.home_team = home_team
        self.away_team = away_team
        self.start_time = start_time
        self.sport = sport
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "bookmaker": self.bookmaker,
            "event_id": self.event_id,
            "market": self.market,
            "home_odds": self.home_odds,
            "away_odds": self.away_odds,
            "draw_odds": self.draw_odds,
            "timestamp": self.timestamp,
        }

    def to_event_dict(self) -> dict[str, Any]:
        return {
            "id": self.event_id,
            "name": f"{self.home_team} vs {self.away_team}",
            "sport": self.sport,
            "start_time": self.start_time or datetime.now(timezone.utc).isoformat(),
            "home_team": self.home_team,
            "away_team": self.away_team,
        }


class BaseScraper(ABC):
    """
    Base class for all bookmaker scrapers.
    Handles browser lifecycle, rate limiting, and ban detection.
    """

    name: str = "base"
    _last_request_time: float = 0

    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def _launch(self) -> None:
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
            proxy={"server": self.proxy} if self.proxy else None,
        )
        self.context = await self.browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )

    async def _new_page(self) -> Page:
        assert self.context, "Browser not launched. Call _launch() first."
        return await self.context.new_page()

    async def _close(self) -> None:
        if self.browser:
            await self.browser.close()

    def _rate_limit(self) -> None:
        """Block until REQUEST_INTERVAL seconds have passed since last request."""
        elapsed = time.time() - BaseScraper._last_request_time
        if elapsed < REQUEST_INTERVAL:
            sleep_for = REQUEST_INTERVAL - elapsed + random.uniform(1, 5)
            print(f"[{self.name}] Rate limiting - waiting {sleep_for:.1f}s")
            time.sleep(sleep_for)
        BaseScraper._last_request_time = time.time()

    def _is_banned(self, content: str) -> bool:
        """Detect common ban/block page patterns."""
        ban_signals = [
            "access denied",
            "403 forbidden",
            "your ip has been blocked",
            "cloudflare",
            "just a moment",
            "enable javascript",
            "captcha",
        ]
        lower = content.lower()
        return any(signal in lower for signal in ban_signals)

    async def scrape(self) -> list[OddsRow]:
        """
        Main entry point. Launches browser, runs _fetch(), closes browser.
        Returns list of OddsRow objects.
        """
        self._rate_limit()
        await self._launch()
        try:
            rows = await self._fetch()
            return rows
        except Exception as e:
            print(f"[{self.name}] Scrape error: {e}")
            return []
        finally:
            await self._close()

    @abstractmethod
    async def _fetch(self) -> list[OddsRow]:
        """Implement bookmaker-specific scraping logic here."""
        ...

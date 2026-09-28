"""Shared HTTP client, rate limiting, and small value objects for adapters."""
from __future__ import annotations
import time
import random
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import httpx

USER_AGENT = "ACER-CRA-Tracker/0.1 (+https://github.com/acer-developer/acer-cra-tracker)"
MIN_INTERVAL = 1.5  # seconds between requests to one host (be polite)


@dataclass
class ListingItem:
    """One row discovered on an agency listing, before the PDF is parsed."""
    agency: str
    entity_name: str
    rating_date: Optional[date]
    source_url_primary: str            # the PDF
    source_url_display: Optional[str] = None
    rating_action: Optional[str] = None
    top_rating_string: Optional[str] = None
    top_amount_cr: Optional[float] = None


@dataclass
class ParsedAction:
    """A fully normalized rating action, ready to upsert."""
    agency: str
    entity_name: str
    rating_date: Optional[date]
    rating_action: str
    source_url_primary: str
    source_url_display: Optional[str] = None
    top_rating_string: Optional[str] = None
    top_grade: Optional[str] = None
    top_amount_cr: Optional[float] = None
    is_inc: bool = False
    audit_coverage: Optional[str] = None


class PoliteClient:
    """httpx client that spaces out requests per host and honors robots.txt."""

    def __init__(self, min_interval: float = MIN_INTERVAL):
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=30,
            follow_redirects=True,
        )
        self._last: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._min = min_interval

    def _host(self, url: str) -> str:
        return httpx.URL(url).host or ""

    def _throttle(self, host: str) -> None:
        prev = self._last.get(host, 0.0)
        wait = self._min - (time.time() - prev)
        if wait > 0:
            time.sleep(wait + random.uniform(0, 0.4))
        self._last[host] = time.time()

    def allowed(self, url: str) -> bool:
        host = self._host(url)
        rp = self._robots.get(host)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                rp.set_url(f"https://{host}/robots.txt")
                rp.read()
            except Exception:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse([])  # no robots -> allow
            self._robots[host] = rp
        try:
            return rp.can_fetch(USER_AGENT, url)
        except Exception:
            return True

    def get(self, url: str, **kw) -> httpx.Response:
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        self._throttle(self._host(url))
        for attempt in range(4):
            try:
                r = self._client.get(url, **kw)
                if r.status_code in (429, 503):
                    time.sleep(2 ** attempt)
                    continue
                return r
            except httpx.TransportError:
                time.sleep(2 ** attempt)
        return self._client.get(url, **kw)  # final try, let it raise/return

    def post(self, url: str, **kw) -> httpx.Response:
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        self._throttle(self._host(url))
        return self._client.post(url, **kw)

    def close(self) -> None:
        self._client.close()

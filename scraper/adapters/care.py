"""CARE Ratings adapter — reference implementation.

Recon: careratings.com is a Laravel app. Its find-ratings page loads results from
a JSON search endpoint (CSRF-protected) and renders PDF links under
`/upload/CompanyFiles/PR/<file>.pdf`. This adapter mirrors that: it reads the
CSRF token from the find-ratings page, then pages the search endpoint.

The exact endpoint path + POST body must be confirmed from the site's Network tab
(it changes occasionally). The two constants below are the only site-specific bits;
everything else is generic. Marked so with ponytail comments.
"""
from __future__ import annotations
import re
from datetime import datetime
from typing import Iterator, Optional
from dateutil import parser as dateparser
from .base import Adapter
from ..common import ListingItem

FIND_PAGE = "https://www.careratings.com/find-ratings"
# ponytail: confirm this route + params from the find-ratings Network tab before a
# real run; wrong values just yield an empty listing, not a crash.
SEARCH_ENDPOINT = "https://www.careratings.com/findsearch"
CSRF_RE = re.compile(r'name="csrf-token"\s+content="([^"]+)"')


class CareAdapter(Adapter):
    agency = "CARE"

    def _csrf(self) -> Optional[str]:
        r = self.client.get(FIND_PAGE)
        m = CSRF_RE.search(r.text)
        return m.group(1) if m else None

    def _parse_date(self, s: Optional[str]):
        if not s:
            return None
        try:
            return dateparser.parse(s, dayfirst=True).date()
        except Exception:
            return None

    def fetch_listing(self, max_pages: int) -> Iterator[ListingItem]:
        token = self._csrf()
        headers = {"X-CSRF-TOKEN": token or "", "X-Requested-With": "XMLHttpRequest"}
        for page in range(1, max_pages + 1):
            # ponytail: body shape mirrors the site's own request; adjust field
            # names here if the Network tab shows different keys.
            resp = self.client.post(
                SEARCH_ENDPOINT,
                headers=headers,
                data={"page": page, "type": "PR"},
            )
            if resp.status_code != 200:
                break
            try:
                rows = resp.json().get("data") or []
            except Exception:
                break
            if not rows:
                break
            for row in rows:
                pdf = row.get("pdf") or row.get("Url") or ""
                if not pdf:
                    continue
                if pdf.startswith("/") or not pdf.startswith("http"):
                    pdf = "https://www.careratings.com/upload/CompanyFiles/PR/" + pdf.lstrip("./")
                yield ListingItem(
                    agency=self.agency,
                    entity_name=(row.get("company_name") or row.get("name") or "").strip(),
                    rating_date=self._parse_date(row.get("date") or row.get("pr_date")),
                    source_url_primary=pdf,
                    source_url_display=FIND_PAGE,
                )

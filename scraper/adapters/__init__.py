"""Adapter registry. CARE is complete; the other six are stubs carrying the
recon notes needed to finish them. Each stub raises NotImplementedError so a run
fails loudly rather than silently producing nothing.
"""
from __future__ import annotations
from typing import Iterator
from .base import Adapter
from ..common import ListingItem
from .care import CareAdapter


class _Stub(Adapter):
    note = ""

    def fetch_listing(self, max_pages: int) -> Iterator[ListingItem]:
        raise NotImplementedError(
            f"{self.agency} adapter not implemented yet.\n  {self.note}\n"
            f"  Fill fetch_listing(): open the listing, watch the Network tab, "
            f"return ListingItem(...) per row."
        )


class CrisilAdapter(_Stub):
    agency = "CRISIL"
    note = "www.crisil.com — server-rendered rationale search; paginate the HTML result list."


class IcraAdapter(_Stub):
    agency = "ICRA"
    note = "www.icra.in — Vue SPA; find the JSON API it calls (Network tab) and page it directly."


class IndiaRatingsAdapter(_Stub):
    agency = "INDIA_RATINGS"
    note = "www.indiaratings.co.in — JS-loaded PR list backed by a JSON API; call the API."


class InfomericsAdapter(_Stub):
    agency = "INFOMERICS"
    note = "infomerics.com listing -> PDFs at infomericstorage.blob.core.windows.net."


class AcuiteAdapter(_Stub):
    agency = "ACUITE"
    note = "connect.acuite.in — data/connect portal; inspect its listing request."


class BrickworkAdapter(_Stub):
    agency = "BRICKWORK"
    note = "www.brickworkratings.com — ASP.NET .aspx; handle __VIEWSTATE postbacks when paging."


REGISTRY: dict[str, type[Adapter]] = {
    "CRISIL": CrisilAdapter,
    "CARE": CareAdapter,
    "ICRA": IcraAdapter,
    "INDIA_RATINGS": IndiaRatingsAdapter,
    "INFOMERICS": InfomericsAdapter,
    "ACUITE": AcuiteAdapter,
    "BRICKWORK": BrickworkAdapter,
}

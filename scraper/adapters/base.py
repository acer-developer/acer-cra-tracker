"""Adapter contract. One subclass per agency."""
from __future__ import annotations
from typing import Iterator
from ..common import PoliteClient, ListingItem, ParsedAction
from .. import parse_pdf


class Adapter:
    agency: str = "OVERRIDE"

    def __init__(self, client: PoliteClient):
        self.client = client

    def fetch_listing(self, max_pages: int) -> Iterator[ListingItem]:
        """Yield listing items newest-first. `backfill` sets max_pages high,
        `incremental` sets it to 1-2. MUST be implemented per agency."""
        raise NotImplementedError

    def parse_item(self, item: ListingItem) -> ParsedAction:
        """Download the PDF and extract fields. Default: generic PDF parse,
        with any structured values from the listing taking precedence."""
        r = self.client.get(item.source_url_primary)
        r.raise_for_status()
        fields = parse_pdf.parse(parse_pdf.text_from_pdf(r.content))
        return ParsedAction(
            agency=self.agency,
            entity_name=item.entity_name,
            rating_date=item.rating_date,
            rating_action=item.rating_action or fields["rating_action"],
            source_url_primary=item.source_url_primary,
            source_url_display=item.source_url_display,
            top_rating_string=item.top_rating_string or fields["top_rating_string"],
            top_grade=fields["top_grade"],
            top_amount_cr=item.top_amount_cr if item.top_amount_cr is not None else fields["top_amount_cr"],
            is_inc=fields["is_inc"],
        )

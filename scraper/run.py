"""Ingestion orchestrator.

    python run.py --agency CARE --mode incremental
    python run.py --agency CARE --mode backfill --max-pages 500
    python run.py --agency ALL  --mode incremental

For each agency: page its listing, skip PDFs already stored (incremental stops on
the first fully-seen page), download+parse the rest, upsert. Politeness and
robots.txt are handled by PoliteClient.
"""
from __future__ import annotations
import argparse
import sys
from .common import PoliteClient
from .db import Store
from .adapters import REGISTRY


def run_agency(agency: str, mode: str, max_pages: int, store: Store) -> dict:
    client = PoliteClient()
    adapter = REGISTRY[agency](client)
    found = upserted = errors = 0
    consecutive_seen = 0
    try:
        for item in adapter.fetch_listing(max_pages):
            found += 1
            if store.seen_key(agency, item.source_url_primary):
                consecutive_seen += 1
                # incremental: once we've hit a run of already-stored rows, the
                # rest of the listing is older and already ingested -> stop.
                if mode == "incremental" and consecutive_seen >= 25:
                    break
                continue
            consecutive_seen = 0
            try:
                action = adapter.parse_item(item)
                store.upsert_action(action.__dict__)
                upserted += 1
            except Exception as e:  # one bad PDF shouldn't kill the run
                errors += 1
                print(f"  [warn] {agency} parse failed: {e}", file=sys.stderr)
    finally:
        client.close()
    return {"agency": agency, "found": found, "upserted": upserted, "errors": errors}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agency", required=True, help="agency code or ALL")
    ap.add_argument("--mode", choices=["backfill", "incremental"], default="incremental")
    ap.add_argument("--max-pages", type=int, default=2)
    args = ap.parse_args()

    if args.mode == "backfill" and args.max_pages < 10:
        args.max_pages = 500  # sensible backfill depth unless overridden

    agencies = list(REGISTRY) if args.agency == "ALL" else [args.agency.upper()]
    store = Store()
    try:
        for ag in agencies:
            if ag not in REGISTRY:
                print(f"unknown agency: {ag}", file=sys.stderr)
                continue
            try:
                res = run_agency(ag, args.mode, args.max_pages, store)
                print(f"{res['agency']}: found={res['found']} "
                      f"upserted={res['upserted']} errors={res['errors']}")
            except NotImplementedError as e:
                print(f"{ag}: SKIPPED — {e}", file=sys.stderr)
    finally:
        store.close()


if __name__ == "__main__":
    main()

"""Postgres upsert layer. Writes into the same schema Prisma manages.

Uses raw SQL via psycopg so the scraper has no Node/Prisma dependency. Table and
column names match Prisma's mapping (PascalCase table, camelCase columns), so
they are quoted.
"""
from __future__ import annotations
import hashlib
import os
import uuid
from datetime import date, datetime, timezone
from typing import Optional
import psycopg

GOOD = {"AAA", "AA", "A", "BBB", "A1+", "A1", "A2+", "A2"}
WARN = {"BB", "B", "A3+", "A3", "A4+", "A4"}
SERIOUS = {"C"}
CRIT = {"D"}


def band_for(grade: Optional[str]) -> str:
    if not grade:
        return "unknown"
    g = grade.upper().replace(" ", "")
    for base in (g, g.rstrip("+-")):
        if base in GOOD:
            return "good"
        if base in WARN:
            return "warning"
        if base in SERIOUS:
            return "serious"
        if base in CRIT:
            return "critical"
    return "unknown"


def dedupe_key(agency: str, source_url_primary: str) -> str:
    return hashlib.sha1(f"{agency}|{source_url_primary}".encode()).hexdigest()


class Store:
    def __init__(self, dsn: Optional[str] = None):
        self.conn = psycopg.connect(dsn or os.environ["DATABASE_URL"], autocommit=True)

    def _entity_id(self, name: str) -> str:
        with self.conn.cursor() as cur:
            cur.execute('SELECT id FROM "Entity" WHERE name = %s', (name,))
            row = cur.fetchone()
            if row:
                return row[0]
            eid = str(uuid.uuid4())
            cur.execute(
                'INSERT INTO "Entity" (id, name, "createdAt") VALUES (%s, %s, %s) '
                'ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id',
                (eid, name, datetime.now(timezone.utc)),
            )
            return cur.fetchone()[0]

    def upsert_action(self, a: dict) -> bool:
        """Insert or update one action. Returns True if a row was written."""
        entity_id = self._entity_id(a["entity_name"])
        key = dedupe_key(a["agency"], a["source_url_primary"])
        band = band_for(a.get("top_grade"))
        with self.conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "RatingAction"
                  (id, "entityId", "entityName", agency, "ratingDate", "ratingAction",
                   "isInc", superseded, "topRatingString", "topGrade", band, "topAmountCr",
                   "auditCoverage", "sourceUrlPrimary", "sourceUrlDisplay", "dedupeKey",
                   "ingestedAt")
                VALUES (%s,%s,%s,%s,%s,%s,%s,false,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT ("dedupeKey") DO UPDATE SET
                  "ratingAction" = EXCLUDED."ratingAction",
                  "topRatingString" = EXCLUDED."topRatingString",
                  "topGrade" = EXCLUDED."topGrade",
                  band = EXCLUDED.band,
                  "topAmountCr" = EXCLUDED."topAmountCr",
                  "isInc" = EXCLUDED."isInc"
                ''',
                (
                    str(uuid.uuid4()), entity_id, a["entity_name"], a["agency"],
                    a.get("rating_date"), a["rating_action"], a.get("is_inc", False),
                    a.get("top_rating_string"), a.get("top_grade"), band,
                    a.get("top_amount_cr"), a.get("audit_coverage"),
                    a["source_url_primary"], a.get("source_url_display"), key,
                    datetime.now(timezone.utc),
                ),
            )
        return True

    def seen_key(self, agency: str, source_url_primary: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                'SELECT 1 FROM "RatingAction" WHERE "dedupeKey" = %s',
                (dedupe_key(agency, source_url_primary),),
            )
            return cur.fetchone() is not None

    def close(self) -> None:
        self.conn.close()

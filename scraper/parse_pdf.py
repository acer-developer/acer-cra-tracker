"""Extract rating fields from a press-release PDF.

Deliberately heuristic: each agency lays its PR out differently, so this pulls
the common signals (rating string, amount, INC flag, action verb) with regexes
and lets each adapter override where its format needs it.

ponytail: regex-first extraction, no ML. Upgrade a specific agency's parsing only
if its PRs prove too irregular for these patterns.
"""
from __future__ import annotations
import io
import re
from typing import Optional
import pdfplumber

# Long-term (AAA..D with +/-) and short-term (A1+..A4, D) rating tokens.
GRADE_RE = re.compile(
    r"\b(?:CRISIL|CARE|ICRA|IND|INFOMERICS|ACUITE|BWR)?\s*"
    r"(AAA|AA|A|BBB|BB|B|C|D|A1\+?|A2\+?|A3\+?|A4\+?)([+-])?\b"
)
AMOUNT_RE = re.compile(r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|cr\.?|lakh)", re.I)
INC_RE = re.compile(r"issuer\s+not\s+cooperating|ISSUER\s+NOT\s+COOPERATING", re.I)
ACTION_RE = re.compile(
    r"\b(reaffirm|downgrad|upgrad|assign|withdraw|revis|suspend|migrat)", re.I
)
ACTION_MAP = {
    "reaffirm": "REAFFIRMED", "downgrad": "DOWNGRADED", "upgrad": "UPGRADED",
    "assign": "ASSIGNED", "withdraw": "WITHDRAWN", "revis": "REVISED",
    "suspend": "SUSPENDED", "migrat": "MIGRATED",
}


def text_from_pdf(data: bytes, max_pages: int = 3) -> str:
    out = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages[:max_pages]:
            out.append(page.extract_text() or "")
    return "\n".join(out)


def extract_grade(text: str) -> tuple[Optional[str], Optional[str]]:
    """Return (top_rating_string, top_grade). First strong match wins."""
    m = GRADE_RE.search(text)
    if not m:
        return None, None
    grade = m.group(1) + (m.group(2) or "")
    # capture a short surrounding string like "CARE BB+; Stable" for display
    span = text[max(0, m.start() - 10): m.end() + 12].strip().replace("\n", " ")
    return span, grade


def extract_amount_cr(text: str) -> Optional[float]:
    m = AMOUNT_RE.search(text)
    if not m:
        return None
    val = float(m.group(1).replace(",", ""))
    return val / 100.0 if m.group(2).lower().startswith("lakh") else val


def extract_action(text: str) -> str:
    m = ACTION_RE.search(text)
    return ACTION_MAP.get(m.group(1).lower(), "ASSIGNED") if m else "ASSIGNED"


def parse(text: str) -> dict:
    rating_string, grade = extract_grade(text)
    return {
        "top_rating_string": rating_string,
        "top_grade": grade,
        "top_amount_cr": extract_amount_cr(text),
        "rating_action": extract_action(text),
        "is_inc": bool(INC_RE.search(text)),
    }

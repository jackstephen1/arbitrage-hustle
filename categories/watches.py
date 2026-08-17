"""
Watches category module.

v1 valuation approach: a manual reference table mapping known
models/references to an approximate current market price band. Fill
this table in with prices pulled from Chrono24 / WatchCharts for the
specific models you want to hunt.

A listing is matched to a model by simple keyword matching against its
title. This is intentionally crude to start — good enough to prove the
pipeline works end to end before investing in fuzzier matching or an
automated pricing feed.

Beginner-friendly $200-$700 lineup (researched August 2026):
- Tissot PRX (quartz and Powermatic 80 automatic) — popular, easy comps
- Seiko 5 Sports (SRPD line) and Seiko SKX007/009 — high trading volume
- Vintage Seiko 6309 "Turtle" diver — watch for franken-watches (mixed
  or fake parts); a too-good price is often a red flag here, not a deal
- Vintage Citizen Bullhead chronograph — top of the range, more upside
  but more originality/authenticity risk too
- Orient Bambino, Hamilton Khaki Field Mechanical, Certina DS Action,
  Seiko Alpinist — added to widen coverage since watches were showing
  up far less often than cameras
- Seiko Lord Matic and Bell-Matic — vintage automatics, still under-the-
  radar relative to other vintage Seikos, good arbitrage candidates
- Longines Conquest and Hamilton Khaki Field Titanium — added to push
  into the $300-700 tier specifically, better brand recognition/resale
  liquidity than the entry-level picks above
"""

from typing import List, Optional, Tuple

from core.models import Listing

CATEGORY_NAME = "watches"

SEARCH_TERMS: List[str] = [
    "Tissot PRX Powermatic 80",
    "Tissot PRX quartz",
    "Seiko 5 Sports SRPD",
    "Seiko SKX007",
    "Seiko SKX009",
    "Seiko 6309 Turtle",
    "Citizen Bullhead vintage",
    "Orient Bambino",
    "Hamilton Khaki Field Mechanical",
    "Certina DS Action",
    "Seiko Alpinist",
    "Seiko Lord Matic",
    "Seiko Bell-Matic",
    "Longines Conquest",
    "Hamilton Khaki Field Titanium",
]

# eBay category ID for Wristwatches
CATEGORY_ID: Optional[str] = "31387"

MIN_DISCOUNT_PCT = 25.0

# Manual price bands (USD), keyed by a lowercase keyword that should
# appear in the listing title. First match wins, so put more specific
# entries (e.g. a specific reference number) before general ones.
#
# Sourced August 2026 from WatchCharts / Chrono24 / collector guides.
# Re-check and update these every few months — used watch prices drift.
PRICE_BANDS = {
    "prx powermatic": (400, 550),
    "prx automatic": (400, 550),
    "prx": (200, 400),  # catches quartz PRX listings not caught above
    "srpd": (250, 350),
    "skx007": (280, 450),
    "skx009": (300, 480),
    "skx": (280, 450),  # fallback for other skx variants
    "6309": (250, 500),
    "bullhead": (400, 750),
    "bambino": (120, 220),
    "khaki field": (280, 420),
    "ds action": (280, 450),
    "alpinist": (400, 700),
    "lord matic": (200, 450),
    "lordmatic": (200, 450),
    "bell-matic": (250, 500),
    "bellmatic": (250, 500),
    "conquest": (450, 700),
    "khaki field titanium": (400, 600),
}

# Expected brand for each keyword — used to verify a listing's actual
# declared brand (from eBay's item data, not just its title) matches
# what it claims to be. Titles alone aren't trustworthy: some sellers
# reuse templates or mislabel items, so a title can say "Seiko Alpinist"
# on a listing that's actually a different brand entirely.
BRAND_BY_KEYWORD = {
    "prx powermatic": "Tissot",
    "prx automatic": "Tissot",
    "prx": "Tissot",
    "srpd": "Seiko",
    "skx007": "Seiko",
    "skx009": "Seiko",
    "skx": "Seiko",
    "6309": "Seiko",
    "bullhead": "Citizen",
    "bambino": "Orient",
    "khaki field": "Hamilton",
    "ds action": "Certina",
    "alpinist": "Seiko",
    "lord matic": "Seiko",
    "lordmatic": "Seiko",
    "bell-matic": "Seiko",
    "bellmatic": "Seiko",
    "conquest": "Longines",
    "khaki field titanium": "Hamilton",
}


def expected_brand_for(listing: Listing) -> Optional[str]:
    """Return the brand this listing's title claims to be, based on
    which price-band keyword matched. Used for brand verification."""
    title_lower = listing.title.lower()
    for keyword, brand in BRAND_BY_KEYWORD.items():
        if keyword in title_lower:
            return brand
    return None


def estimate_value(listing: Listing) -> Optional[Tuple[float, float]]:
    title_lower = listing.title.lower()
    for keyword, band in PRICE_BANDS.items():
        if keyword in title_lower:
            return band
    return None

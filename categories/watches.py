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
"""

from typing import List, Optional, Tuple

from core.models import Listing

CATEGORY_NAME = "watches"

SEARCH_TERMS: List[str] = [
    "Rolex Submariner",
    "Rolex Datejust",
    "Omega Speedmaster",
    "Omega Seamaster",
    "Tudor Black Bay",
]

# eBay category ID for Wristwatches
CATEGORY_ID: Optional[str] = "31387"

MIN_DISCOUNT_PCT = 20.0

# Manual price bands (USD), keyed by a lowercase keyword that should
# appear in the listing title. First match wins, so put more specific
# entries (e.g. a specific reference number) before general ones.
#
# TODO: fill these in with real current comps — these are placeholders.
PRICE_BANDS = {
    "submariner 116610": (9000, 11500),
    "submariner": (8500, 13000),
    "datejust": (4000, 7500),
    "speedmaster professional": (4500, 6500),
    "speedmaster": (3500, 7000),
    "seamaster 300": (3000, 4500),
    "seamaster": (2500, 5000),
    "black bay 58": (3200, 4200),
    "black bay": (2800, 4500),
}


def estimate_value(listing: Listing) -> Optional[Tuple[float, float]]:
    title_lower = listing.title.lower()
    for keyword, band in PRICE_BANDS.items():
        if keyword in title_lower:
            return band
    return None

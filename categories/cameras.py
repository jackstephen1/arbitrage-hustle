"""
Cameras category module.

v1 valuation approach: same pattern as watches.py — a manual reference
table mapping known models to an approximate current market price band,
matched against listing titles by keyword.

IMPORTANT — more than the other categories, camera pricing swings hard
on CONDITION (working shutter, no fungus/haze in the lens, working light
meter, no light seal issues). The price bands below reflect *decent
working condition*, not mint/collector-grade. A cheap listing on a
camera with an unclear "as-is, untested" description is not automatically
a deal — it's a bigger risk. Prioritize listings with clear photos and
"tested working" in the description.

These bands were built from general market research, not fresh sold
comps — treat them as a starting point and refine with real eBay sold
listings / KEH.com pricing before trusting them with real money.
"""

from typing import List, Optional, Tuple

from core.models import Listing

CATEGORY_NAME = "cameras"

SEARCH_TERMS: List[str] = [
    "Canon AE-1 35mm",
    "Pentax K1000",
    "Nikon FM2",
    "Olympus OM-1",
    "Minolta X-700",
]

# eBay category ID for Film Cameras
CATEGORY_ID: Optional[str] = "15230"

MIN_DISCOUNT_PCT = 25.0  # higher bar than watches — condition risk is greater

# Manual price bands (USD), keyed by a lowercase keyword that should
# appear in the listing title. First match wins.
#
# TODO: refine these with real current sold comps before relying on them.
PRICE_BANDS = {
    "ae-1 program": (120, 220),
    "ae-1": (100, 180),
    "k1000": (80, 160),
    "fm2": (200, 320),
    "fm": (150, 280),  # catches plain "Nikon FM" listings not caught above
    "om-1": (120, 250),
    "x-700": (100, 200),
}


def estimate_value(listing: Listing) -> Optional[Tuple[float, float]]:
    title_lower = listing.title.lower()
    for keyword, band in PRICE_BANDS.items():
        if keyword in title_lower:
            return band
    return None

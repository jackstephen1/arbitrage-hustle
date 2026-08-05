"""
Template for a new category module.

Copy this file to categories/<your_category>.py, fill in the pieces below,
and register it in core/deal_finder.py's ENABLED_CATEGORIES list.
"""

from typing import List, Optional, Tuple

from core.models import Listing

CATEGORY_NAME = "template"

# eBay keyword searches to run for this category. Keep these specific —
# broad terms return too much noise to score well.
SEARCH_TERMS: List[str] = [
    # "example search term here",
]

# Optional: restrict to an eBay category ID to cut down noise further.
# Look up IDs at https://www.ebay.com/n/all-categories
CATEGORY_ID: Optional[str] = None

# Minimum % below the low end of the estimated value range to count as a deal.
MIN_DISCOUNT_PCT = 20.0


def estimate_value(listing: Listing) -> Optional[Tuple[float, float]]:
    """
    Return (low_estimate, high_estimate) for this listing's true market
    value, or None if this listing can't be confidently valued (e.g. title
    doesn't match a known model/reference — better to skip than guess).
    """
    # TODO: implement valuation logic for this category.
    return None

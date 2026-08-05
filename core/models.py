"""Shared data structures used across all category modules."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Listing:
    """A single eBay listing pulled from the Browse API."""
    item_id: str
    title: str
    price: float
    currency: str
    condition: Optional[str]
    url: str
    image_url: Optional[str]
    seller_username: Optional[str]
    seller_feedback_score: Optional[int]


@dataclass
class Deal:
    """A listing that has been flagged as underpriced vs. estimated value."""
    listing: Listing
    category: str
    estimated_value_low: float
    estimated_value_high: float
    discount_pct: float
    notes: str = ""

    def summary_line(self) -> str:
        return (
            f"[{self.category}] {self.listing.title} — "
            f"${self.listing.price:,.0f} "
            f"(est. value ${self.estimated_value_low:,.0f}-"
            f"${self.estimated_value_high:,.0f}, "
            f"{self.discount_pct:.0f}% below low estimate) "
            f"{self.listing.url}"
        )

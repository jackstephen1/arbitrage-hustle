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

    def as_html_card(self) -> str:
        image_html = (
            f'<img src="{self.listing.image_url}" alt="" '
            f'style="width:100%;max-width:160px;height:auto;border-radius:6px;'
            f'display:block;margin-bottom:12px;">'
            if self.listing.image_url else ""
        )
        seller_line = (
            f"Seller: {self.listing.seller_username} "
            f"({self.listing.seller_feedback_score} feedback)"
            if self.listing.seller_username else ""
        )
        return f"""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
                      margin-bottom:16px;">
          <tr>
            <td style="padding:20px;">
              <span style="display:inline-block;background:#eef2ff;color:#4338ca;
                           font-size:12px;font-weight:600;padding:3px 10px;
                           border-radius:999px;text-transform:capitalize;
                           margin-bottom:12px;">{self.category}</span>
              {image_html}
              <div style="font-size:16px;font-weight:600;color:#111827;
                          margin-bottom:6px;line-height:1.4;">
                {self.listing.title}
              </div>
              <div style="font-size:14px;color:#6b7280;margin-bottom:4px;">
                {seller_line}
              </div>
              <div style="margin:12px 0;">
                <span style="font-size:22px;font-weight:700;color:#111827;">
                  ${self.listing.price:,.0f}
                </span>
                <span style="font-size:14px;color:#6b7280;margin-left:8px;">
                  est. value ${self.estimated_value_low:,.0f}–${self.estimated_value_high:,.0f}
                </span>
              </div>
              <span style="display:inline-block;background:#dcfce7;color:#166534;
                           font-size:13px;font-weight:600;padding:4px 10px;
                           border-radius:6px;margin-bottom:16px;">
                {self.discount_pct:.0f}% below estimated low value
              </span>
              <div>
                <a href="{self.listing.url}"
                   style="display:inline-block;background:#111827;color:#ffffff;
                          font-size:14px;font-weight:600;text-decoration:none;
                          padding:10px 18px;border-radius:6px;">
                  View listing →
                </a>
              </div>
            </td>
          </tr>
        </table>
        """

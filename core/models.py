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
    shipping_cost: float = 0.0
    ebay_category: Optional[str] = None  # eBay's own leaf category name, e.g. "Wristwatches"


@dataclass
class Deal:
    """A listing that has been flagged as underpriced vs. estimated value,
    after accounting for shipping cost and estimated resale fees."""
    listing: Listing
    category: str
    estimated_value_low: float
    estimated_value_high: float
    discount_pct: float
    landed_cost: float  # purchase price + shipping in
    net_profit_low: float  # profit if resold at estimated_value_low, after resale fees
    net_profit_high: float  # profit if resold at estimated_value_high, after resale fees
    notes: str = ""

    def summary_line(self) -> str:
        condition = self.listing.condition or "condition not specified"
        return (
            f"[{self.category}] {self.listing.title} — "
            f"${self.listing.price:,.0f} + ${self.listing.shipping_cost:,.0f} shipping "
            f"= ${self.landed_cost:,.0f} landed ({condition}) "
            f"(est. resale ${self.estimated_value_low:,.0f}-"
            f"${self.estimated_value_high:,.0f}, "
            f"est. profit ${self.net_profit_low:,.0f}-${self.net_profit_high:,.0f} "
            f"after fees, {self.discount_pct:.0f}% below low estimate) "
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
        condition_text = self.listing.condition or "Condition not specified"
        shipping_text = (
            f"+ ${self.listing.shipping_cost:,.0f} shipping"
            if self.listing.shipping_cost > 0 else "Free shipping"
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
              <span style="display:inline-block;background:#f3f4f6;color:#374151;
                           font-size:12px;font-weight:600;padding:3px 10px;
                           border-radius:999px;margin-bottom:12px;margin-left:6px;">
                {condition_text}
              </span>
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
                <span style="font-size:13px;color:#6b7280;margin-left:8px;">
                  {shipping_text} · landed ${self.landed_cost:,.0f}
                </span>
              </div>
              <div style="font-size:14px;color:#6b7280;margin-bottom:8px;">
                Est. resale ${self.estimated_value_low:,.0f}–${self.estimated_value_high:,.0f}
              </div>
              <span style="display:inline-block;background:#dcfce7;color:#166534;
                           font-size:13px;font-weight:600;padding:4px 10px;
                           border-radius:6px;margin-bottom:8px;">
                Est. profit ${self.net_profit_low:,.0f}–${self.net_profit_high:,.0f} after fees
              </span><br>
              <span style="display:inline-block;background:#f3f4f6;color:#374151;
                           font-size:12px;padding:3px 8px;border-radius:6px;
                           margin-bottom:16px;">
                {self.discount_pct:.0f}% below estimated low resale value
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

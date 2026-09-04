"""
Main runner: loops over enabled category modules, searches eBay for each
of their search terms, scores listings against estimated resale value
(factoring in shipping cost, sales tax, and estimated resale fees),
skips listings already alerted on, and emails a summary of any new
deals found.

Run manually:
    python -m core.deal_finder

Run on a schedule: see .github/workflows/run.yml
"""

import importlib
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from core.ebay_client import EbayClient
from core.models import Deal, Listing
from core.seen_store import load_seen, save_seen
from core.deal_store import append_deals

# Add new category module names here as you build them out
# (must match the filename in categories/, without .py)
ENABLED_CATEGORIES = [
    "watches",
    "cameras",
    # "pokemon",
    # "sports_cards",
    # "vintage",
]

# Title phrases that disqualify a listing regardless of price.
JUNK_PHRASES = [
    "for parts",
    "not working",
    "as is",
    "broken",
    "repair",
    "replica",
    "faux",
    "empty box",
    "box only",
    "case only",
    "women's",
    "womens",
    "ladies",
    "women watch",
    "compatible with",
    "compatible models",
    "bracelet only",
    "strap only",
    "band only",
    "accessory",
]

# Condition values (from eBay's own condition field, not just title text)
# that disqualify a listing regardless of price.
JUNK_CONDITIONS = [
    "for parts or not working",
    "for parts",
    "not working",
]

# BUG FIX (found after watches went silent for days): this used to also
# check eBay's full category PATH, which contains the word "Parts" for
# EVERY watch listing regardless of what it actually is — eBay's standard
# breadcrumb is "Jewelry & Watches > Watches, Parts & Accessories >
# Watches > Wristwatches". That's just the parent category's name, not a
# description of the item, so checking the full path against "part"
# incorrectly rejected every single genuine watch. Now this only checks
# eBay's specific "Type" item-specific field (e.g. "Wristwatch" vs
# "Band"/"Bracelet"), which is precise and doesn't have this problem.
JUNK_ITEM_TYPES = [
    "band",
    "bracelet",
    "strap",
    "accessor",
    "buckle",
    "clasp",
]

# Skip listings from sellers with very low feedback.
MIN_SELLER_FEEDBACK = 5

# Estimated cost of reselling on eBay: final value fee (~15% for Jewelry
# & Watches) plus the flat per-order fee.
RESALE_FEE_PCT = 0.15

# Sales tax on the PURCHASE, applied to (price + shipping). Set for
# delivery to Hillsborough County, FL (Tampa area) — 6% state + 1.5%
# county = 7.5% combined. Update this if the delivery address changes.
SALES_TAX_PCT = 0.075

# Estimated cost to ship the item back out when reselling.
OUTBOUND_SHIPPING_COST = 9.50


def is_junk_listing(listing: Listing) -> bool:
    title_lower = listing.title.lower()
    if any(phrase in title_lower for phrase in JUNK_PHRASES):
        return True
    if listing.condition:
        condition_lower = listing.condition.lower()
        if any(phrase in condition_lower for phrase in JUNK_CONDITIONS):
            return True
    if (
        MIN_SELLER_FEEDBACK > 0
        and listing.seller_feedback_score is not None
        and listing.seller_feedback_score < MIN_SELLER_FEEDBACK
    ):
        return True
    return False


def verify_complete_item(client: EbayClient, listing: Listing) -> bool:
    """
    Confirm this is genuinely the complete item, not an accessory/part,
    using ONLY eBay's "Type" item specific (e.g. "Wristwatch" vs "Band").
    Does NOT check the full category path anymore — see JUNK_ITEM_TYPES
    comment above for why that was a bug.
    """
    _, item_type, _ = client.get_item_details(listing.item_id)

    if not item_type.strip():
        return True  # no data — don't block on missing data

    item_type_lower = item_type.lower()
    if any(junk_word in item_type_lower for junk_word in JUNK_ITEM_TYPES):
        return False

    return True


def verify_brand(client: EbayClient, category_module, listing: Listing) -> bool:
    """
    Confirm a candidate deal's actual eBay-declared brand matches what
    its title claims.
    """
    expected_fn = getattr(category_module, "expected_brand_for", None)
    if expected_fn is None:
        return True

    expected = expected_fn(listing)
    if expected is None:
        return True

    actual = client.get_item_brand(listing.item_id)
    if not actual:
        return True

    return expected.lower() in actual.lower() or actual.lower() in expected.lower()


def score_listing(listing: Listing, category_module, category_name: str) -> "Deal | None":
    if is_junk_listing(listing):
        return None

    estimate = category_module.estimate_value(listing)
    if estimate is None:
        return None

    low, high = estimate

    pre_tax_cost = listing.price + listing.shipping_cost
    landed_cost = pre_tax_cost * (1 + SALES_TAX_PCT)
    if landed_cost <= 0 or low <= 0:
        return None

    discount_pct = (low - landed_cost) / low * 100

    net_profit_low = (low * (1 - RESALE_FEE_PCT)) - landed_cost - OUTBOUND_SHIPPING_COST
    net_profit_high = (high * (1 - RESALE_FEE_PCT)) - landed_cost - OUTBOUND_SHIPPING_COST

    if discount_pct >= category_module.MIN_DISCOUNT_PCT and net_profit_low > 0:
        return Deal(
            listing=listing,
            category=category_name,
            estimated_value_low=low,
            estimated_value_high=high,
            discount_pct=discount_pct,
            landed_cost=landed_cost,
            net_profit_low=net_profit_low,
            net_profit_high=net_profit_high,
        )
    return None


def run() -> List[Deal]:
    client = EbayClient()
    seen_ids = load_seen()
    new_deals: List[Deal] = []

    for category_name in ENABLED_CATEGORIES:
        module = importlib.import_module(f"categories.{category_name}")
        print(f"Scanning category: {category_name}")

        for term in module.SEARCH_TERMS:
            print(f"  Searching: {term}")
            try:
                listings = client.search(
                    query=term,
                    category_id=getattr(module, "CATEGORY_ID", None),
                )
            except Exception as e:
                print(f"    Search failed for '{term}': {e}")
                continue

            for listing in listings:
                if listing.item_id in seen_ids:
                    continue

                deal = score_listing(listing, module, category_name)
                if deal:
                    if not verify_complete_item(client, listing):
                        print(f"    Skipped (not a complete watch — accessory/part): {listing.title}")
                        seen_ids.add(listing.item_id)
                        continue
                    if not verify_brand(client, module, listing):
                        print(f"    Skipped (brand mismatch): {listing.title}")
                        seen_ids.add(listing.item_id)
                        continue
                    new_deals.append(deal)
                    seen_ids.add(listing.item_id)

    save_seen(seen_ids)
    append_deals(new_deals)
    return new_deals


def build_email_html(deals: List[Deal]) -> str:
    cards = "\n".join(deal.as_html_card() for deal in deals)
    vault_url = os.environ.get("VAULT_URL", "")
    vault_link_html = (
        f"""
        <div style="text-align:center;margin:8px 0 20px;">
          <a href="{vault_url}"
             style="display:inline-block;background:#ffffff;color:#111827;
                    font-size:14px;font-weight:600;text-decoration:none;
                    padding:10px 20px;border-radius:6px;border:1px solid #d1d5db;">
            View full deal vault →
          </a>
        </div>
        """
        if vault_url else ""
    )
    return f"""
    <div style="background:#f3f4f6;padding:24px;font-family:-apple-system,
                BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="max-width:560px;margin:0 auto;">
        <tr>
          <td style="padding-bottom:20px;">
            <div style="font-size:20px;font-weight:700;color:#111827;">
              Arbitrage Finder
            </div>
            <div style="font-size:14px;color:#6b7280;margin-top:4px;">
              {len(deals)} new deal(s) found today
            </div>
          </td>
        </tr>
        <tr>
          <td>
            {cards}
          </td>
        </tr>
        <tr>
          <td>
            {vault_link_html}
          </td>
        </tr>
        <tr>
          <td style="padding-top:8px;font-size:12px;color:#9ca3af;">
            Automated scan of live eBay listings against estimated market value,
            after shipping cost, sales tax, outbound shipping, and eBay's resale fee.
            Always double-check condition and seller details before buying.
          </td>
        </tr>
      </table>
    </div>
    """


def send_email(deals: List[Deal]) -> None:
    if not deals:
        print("No new deals found — skipping email.")
        return

    to_addr_raw = os.environ.get("ALERT_EMAIL_TO")
    from_addr = os.environ.get("ALERT_EMAIL_FROM")
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if not all([to_addr_raw, from_addr, smtp_host, smtp_user, smtp_pass]):
        print("Email env vars not fully set — printing deals instead:")
        for deal in deals:
            print(deal.summary_line())
        return

    to_addrs = [addr.strip() for addr in to_addr_raw.split(",") if addr.strip()]

    plain_body = "\n\n".join(deal.summary_line() for deal in deals)
    html_body = build_email_html(deals)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{len(deals)} new arbitrage deal(s) found"
    msg["From"] = f"Arbitrage Finder <{from_addr}>"
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(smtp_host, 465) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, to_addrs, msg.as_string())

    print(f"Sent email with {len(deals)} new deal(s).")


if __name__ == "__main__":
    found = run()
    print(f"\nFound {len(found)} new deal(s) total.")
    send_email(found)

"""
Main runner: loops over enabled category modules, searches eBay for each
of their search terms, scores listings against estimated resale value
(factoring in shipping cost and estimated resale fees), skips listings
already alerted on, and emails a summary of any new deals found.

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

# Title phrases that disqualify a listing regardless of price — these
# usually mean the item isn't in sellable condition, isn't the real
# item at all, isn't a complete item (accessories/parts), or isn't a
# category we're hunting (men's sport/automatic watches).
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

# eBay's own leaf category names (not just the category_id search filter)
# that mean this is an accessory/part, not the complete item. Checked as
# a second safety layer in case eBay ever miscategorizes something —
# this is what would have caught the "Alpinist bracelet, not the watch"
# mixup, since its title alone read like a complete watch.
JUNK_CATEGORIES = [
    "accessor",
    "band",
    "strap",
    "bracelet",
    "parts",
    "case",  # watch cases sold standalone, not the "case only" phrase above
]

# Skip listings from sellers with very low feedback — higher risk of scams
# or misrepresented condition. Set to 0 to disable this filter.
MIN_SELLER_FEEDBACK = 5

# Estimated cost of reselling on eBay: final value fee (~13%) plus
# payment processing (~3%). Applied to the resale price when estimating
# real profit — a "deal" on paper can still be a loss after these.
RESALE_FEE_PCT = 0.15


def is_junk_listing(listing: Listing) -> bool:
    title_lower = listing.title.lower()
    if any(phrase in title_lower for phrase in JUNK_PHRASES):
        return True
    if listing.condition:
        condition_lower = listing.condition.lower()
        if any(phrase in condition_lower for phrase in JUNK_CONDITIONS):
            return True
    if listing.ebay_category:
        category_lower = listing.ebay_category.lower()
        # "Wristwatches" contains none of the junk substrings, so this is
        # safe — it only trips for genuine accessory/parts categories.
        if any(phrase in category_lower for phrase in JUNK_CATEGORIES):
            return True
    if (
        MIN_SELLER_FEEDBACK > 0
        and listing.seller_feedback_score is not None
        and listing.seller_feedback_score < MIN_SELLER_FEEDBACK
    ):
        return True
    return False


def verify_brand(client: EbayClient, category_module, listing: Listing) -> bool:
    """
    Confirm a candidate deal's actual eBay-declared brand matches what
    its title claims. Only called for listings that already passed the
    price filter, to keep the extra API call cheap. If the category
    module doesn't define expected brands, this passes through (True).
    """
    expected_fn = getattr(category_module, "expected_brand_for", None)
    if expected_fn is None:
        return True

    expected = expected_fn(listing)
    if expected is None:
        return True  # no brand mapping matched — nothing to verify against

    actual = client.get_item_brand(listing.item_id)
    if not actual:
        return True  # eBay didn't return brand data — can't verify, don't block

    return expected.lower() in actual.lower() or actual.lower() in expected.lower()


def score_listing(listing: Listing, category_module, category_name: str) -> "Deal | None":
    if is_junk_listing(listing):
        return None

    estimate = category_module.estimate_value(listing)
    if estimate is None:
        return None

    low, high = estimate
    landed_cost = listing.price + listing.shipping_cost
    if landed_cost <= 0 or low <= 0:
        return None

    # Discount is measured against landed cost (price + shipping), not
    # just the listing price — a "cheap" item with expensive shipping
    # might not actually be a deal at all.
    discount_pct = (low - landed_cost) / low * 100

    net_profit_low = (low * (1 - RESALE_FEE_PCT)) - landed_cost
    net_profit_high = (high * (1 - RESALE_FEE_PCT)) - landed_cost

    # Require both: a big enough discount AND actual positive profit
    # after resale fees. A high discount_pct with thin/negative profit
    # (cheap item, but resale value is also low) shouldn't count.
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
                    continue  # already alerted on this one before

                deal = score_listing(listing, module, category_name)
                if deal:
                    if not verify_brand(client, module, listing):
                        print(f"    Skipped (brand mismatch): {listing.title}")
                        seen_ids.add(listing.item_id)  # don't re-check it every day
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
            after shipping cost and an estimated 15% resale fee. Always
            double-check condition and seller details before buying.
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

    # ALERT_EMAIL_TO can be a single address or a comma-separated list,
    # e.g. "you@gmail.com,partner@gmail.com"
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

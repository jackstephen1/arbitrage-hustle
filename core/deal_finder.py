"""
Main runner: loops over enabled category modules, searches eBay for each
of their search terms, scores listings against estimated value, and
emails a summary of any deals found.

Run manually:
    python -m core.deal_finder

Run on a schedule: see .github/workflows/run.yml
"""

import importlib
import os
import smtplib
from email.mime.text import MIMEText
from typing import List

from core.ebay_client import EbayClient
from core.models import Deal, Listing

# Add new category module names here as you build them out
# (must match the filename in categories/, without .py)
ENABLED_CATEGORIES = [
    "watches",
    # "cameras",
    # "pokemon",
    # "sports_cards",
    # "vintage",
]


def score_listing(listing: Listing, category_module, category_name: str) -> "Deal | None":
    estimate = category_module.estimate_value(listing)
    if estimate is None:
        return None

    low, high = estimate
    if listing.price <= 0 or low <= 0:
        return None

    discount_pct = (low - listing.price) / low * 100
    if discount_pct >= category_module.MIN_DISCOUNT_PCT:
        return Deal(
            listing=listing,
            category=category_name,
            estimated_value_low=low,
            estimated_value_high=high,
            discount_pct=discount_pct,
        )
    return None


def run() -> List[Deal]:
    client = EbayClient()
    all_deals: List[Deal] = []

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
                deal = score_listing(listing, module, category_name)
                if deal:
                    all_deals.append(deal)

    return all_deals


def send_email(deals: List[Deal]) -> None:
    if not deals:
        print("No deals found — skipping email.")
        return

    to_addr = os.environ.get("ALERT_EMAIL_TO")
    from_addr = os.environ.get("ALERT_EMAIL_FROM")
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if not all([to_addr, from_addr, smtp_host, smtp_user, smtp_pass]):
        print("Email env vars not fully set — printing deals instead:")
        for deal in deals:
            print(deal.summary_line())
        return

    body = "\n\n".join(deal.summary_line() for deal in deals)
    msg = MIMEText(body)
    msg["Subject"] = f"Arbitrage Finder: {len(deals)} deal(s) found"
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP_SSL(smtp_host, 465) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, [to_addr], msg.as_string())

    print(f"Sent email with {len(deals)} deal(s).")


if __name__ == "__main__":
    found = run()
    print(f"\nFound {len(found)} deal(s) total.")
    send_email(found)

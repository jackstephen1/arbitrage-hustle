"""
Keeps a running log of every deal ever found, for the vault webpage
(docs/index.html) to display. Different from seen_store.py — that one
just tracks IDs to avoid duplicate alerts; this one keeps the full
deal details so you can browse deal history later.
"""

import json
import os
from datetime import datetime, timezone
from typing import List

from core.models import Deal

LOG_FILE = "docs/deals_log.json"
MAX_ENTRIES = 500  # keep the file from growing forever


def load_log() -> List[dict]:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def append_deals(deals: List[Deal]) -> None:
    log = load_log()
    now = datetime.now(timezone.utc).isoformat()

    for deal in deals:
        log.append({
            "id": deal.listing.item_id,
            "category": deal.category,
            "title": deal.listing.title,
            "price": deal.listing.price,
            "estimated_value_low": deal.estimated_value_low,
            "estimated_value_high": deal.estimated_value_high,
            "discount_pct": deal.discount_pct,
            "url": deal.listing.url,
            "image_url": deal.listing.image_url,
            "seller_username": deal.listing.seller_username,
            "seller_feedback_score": deal.listing.seller_feedback_score,
            "date_found": now,
        })

    # keep most recent MAX_ENTRIES
    log = log[-MAX_ENTRIES:]

    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

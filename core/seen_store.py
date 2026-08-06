"""
Tracks which listing IDs have already been alerted on, so the same deal
doesn't get emailed every day it stays active.

Stored as a simple JSON file committed back to the repo after each run
(see .github/workflows/run.yml — it commits seen_listings.json back to
the repo after a successful scan).
"""

import json
import os
from typing import Set

SEEN_FILE = "seen_listings.json"


def load_seen() -> Set[str]:
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(json.load(f))


def save_seen(seen_ids: Set[str]) -> None:
    # Keep the file from growing forever — cap to the most recent 5000 IDs.
    # (Not perfectly precise since sets are unordered, but good enough to
    # bound file size over time.)
    trimmed = list(seen_ids)[-5000:]
    with open(SEEN_FILE, "w") as f:
        json.dump(trimmed, f)

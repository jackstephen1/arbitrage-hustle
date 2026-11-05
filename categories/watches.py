"""
Watches category module.

v1 valuation approach: a manual reference table mapping known
models/references to an approximate current market price band. Fill
this table in with prices pulled from Chrono24 / WatchCharts for the
specific models you want to hunt.

A listing is matched to a model by simple keyword matching against its
title. This is intentionally crude to start — good enough to prove the
pipeline works end to end before investing in fuzzier matching or an
automated pricing feed.

Beginner-friendly $200-$700 lineup (researched August 2026):
- Tissot PRX (quartz and Powermatic 80 automatic) — popular, easy comps
- Seiko 5 Sports (SRPD line) and Seiko SKX007/009 — high trading volume
- Vintage Seiko 6309 "Turtle" diver — watch for franken-watches (mixed
  or fake parts); a too-good price is often a red flag here, not a deal
- Vintage Citizen Bullhead chronograph — top of the range, more upside
  but more originality/authenticity risk too
- Orient Bambino, Hamilton Khaki Field Mechanical, Certina DS Action,
  Seiko Alpinist — added to widen coverage since watches were showing
  up far less often than cameras
- Seiko Lord Matic and Bell-Matic — vintage automatics, still under-the-
  radar relative to other vintage Seikos, good arbitrage candidates
- Longines Conquest and Hamilton Khaki Field Titanium — added to push
  into the $300-700 tier specifically, better brand recognition/resale
  liquidity than the entry-level picks above. NOTE: "Conquest" alone
  matches vintage/dress quartz Conquest models too, which are a
  DIFFERENT market segment worth much less than the modern automatic
  sport Conquest this price band is built from — verify case size
  (modern sport = 38-43mm) and movement (automatic, not quartz) before
  trusting this band on a Conquest listing.
- Bulova Jet Star — modern Precisionist quartz reissue, under-the-radar
- Citizen Tsuyosa — very popular "Datejust homage," strong demand/
  liquidity, though used resale runs a bit below the $300 floor
- Seiko 5 Sports GMT (SSK series) — affordable true-GMT automatic,
  strong demand, retails $350-450 new. WATCH FOR MODS: some sellers
  list "Seiko mod" watches with GMT-style dials on a plain 7S26
  movement (no real GMT function) — these are NOT genuine SSK
  references despite similar branding/appearance. Always verify the
  reference number matches a real SSK model and the movement is 4R34,
  not 7S26, before trusting the price band below.
- Seiko Presage Cocktail Time "Mojito" (SRPE45) — genuinely appreciating
  per WatchCharts (+18.3% over the past year), official Seiko retail is
  $450. NOTE: the Presage "Cocktail Time" line varies wildly by
  reference — the Mojito is a strong pick, but e.g. the "Espresso
  Martini" (SRPE17) is flagged "Extreme Risk" by WatchCharts and has
  been depreciating. Do NOT add other Presage references to this list
  without researching that specific reference's own price trend first —
  "Presage" as a brand/line is not a reliable single price band.
- Bulova Lunar Pilot Chronograph (96B251/96B258) — genuine heritage
  story (the actual watch worn on the moon when astronaut David Scott's
  Omega broke during Apollo 15), real liquid secondary market with
  comps clustering $414-579. WatchCharts flags it "High Risk" (62/100)
  for short-term volatility despite being up ~11% over the past year —
  a real but liquid market, not a red flag on its own.
- Traska Venturer GMT (added Nov 2026 to hunt one for a friend) —
  microbrand, so a thinner market than the mainstream picks above.
  Forum asking prices (not confirmed sales): older generations about
  $450-600, current generations about $580-825 (mostly $650-750), Dark
  Meteorite limited edition about $1,000-1,650. Retail is unconfirmed
  ($720 in older reviews, $950 on the brand's site). WATCH THE
  GENERATION: the first-generation Venturer reportedly has a rotating
  12-hour bezel and no independent GMT hand; later versions use the
  Miyota 9075 (true GMT). A cheap listing may be the older version —
  confirm the 9075 / independent hour hand before buying. The scanner
  cannot tell generations apart from the title alone.

Deliberately NOT added (researched and rejected, August 2026):
- Other microbrands (Nodus, Baltic, Unimatic, Brew, Christopher Ward)
  — well-regarded but thin secondary markets with far fewer buyers than
  mainstream brands; bad fit for arbitrage even when individually nice
  watches.
- Seiko Flightmaster (SND253) — real comps are wide and inconsistent
  ($151-330), no confident price band could be built.
- Anything priced mostly above $700 (Omega Seamaster, Zenith Defy,
  Christopher Ward C63) — outside the target range/capital comfort zone.
"""

from typing import List, Optional, Tuple

from core.models import Listing

CATEGORY_NAME = "watches"

SEARCH_TERMS: List[str] = [
    "Tissot PRX Powermatic 80",
    "Tissot PRX quartz",
    "Seiko 5 Sports SRPD",
    "Seiko SKX007",
    "Seiko SKX009",
    "Seiko 6309 Turtle",
    "Citizen Bullhead vintage",
    "Orient Bambino",
    "Hamilton Khaki Field Mechanical",
    "Certina DS Action",
    "Seiko Alpinist",
    "Seiko Lord Matic",
    "Seiko Bell-Matic",
    "Longines Conquest",
    "Hamilton Khaki Field Titanium",
    "Bulova Jet Star",
    "Citizen Tsuyosa",
    "Seiko 5 Sports GMT",
    "Seiko Presage Mojito",
    "Bulova Lunar Pilot",
    "Traska Venturer GMT",
    "Traska Venturer Meteorite",
]

# eBay category ID for Wristwatches
CATEGORY_ID: Optional[str] = "31387"

MIN_DISCOUNT_PCT = 20.0  # lowered back from 25% to surface more candidates while volume is low

# Manual price bands (USD), keyed by a lowercase keyword that should
# appear in the listing title. First match wins, so put more specific
# entries (e.g. a specific reference number) before general ones.
#
# Sourced August 2026 from WatchCharts / Chrono24 / collector guides.
# Re-check and update these every few months — used watch prices drift.
PRICE_BANDS = {
    "prx powermatic": (400, 550),
    "prx automatic": (400, 550),
    "prx": (200, 400),  # catches quartz PRX listings not caught above
    "srpd": (250, 350),
    "skx007": (280, 450),
    "skx009": (300, 480),
    "skx": (280, 450),  # fallback for other skx variants
    "6309": (250, 500),
    "bullhead": (400, 750),
    "bambino": (120, 220),
    "khaki field": (280, 420),
    "ds action": (280, 450),
    "alpinist": (400, 700),
    "lord matic": (200, 450),
    "lordmatic": (200, 450),
    "bell-matic": (250, 500),
    "bellmatic": (250, 500),
    "conquest": (450, 700),
    "khaki field titanium": (400, 600),
    "jet star": (300, 450),
    "tsuyosa": (220, 320),
    "5 sports gmt": (280, 420),
    "sports gmt": (280, 420),
    "mojito": (380, 480),
    "srpe45": (380, 480),
    "lunar pilot": (414, 579),
    "96b251": (414, 579),
    "96b258": (414, 579),
    "meteorite": (1000, 1300),  # Traska Dark Meteorite LE — keep before "venturer"
    "venturer": (650, 750),
}

# Expected brand for each keyword — used to verify a listing's actual
# declared brand (from eBay's item data, not just its title) matches
# what it claims to be. Titles alone aren't trustworthy: some sellers
# reuse templates or mislabel items, so a title can say "Seiko Alpinist"
# on a listing that's actually a different brand entirely.
BRAND_BY_KEYWORD = {
    "prx powermatic": "Tissot",
    "prx automatic": "Tissot",
    "prx": "Tissot",
    "srpd": "Seiko",
    "skx007": "Seiko",
    "skx009": "Seiko",
    "skx": "Seiko",
    "6309": "Seiko",
    "bullhead": "Citizen",
    "bambino": "Orient",
    "khaki field": "Hamilton",
    "ds action": "Certina",
    "alpinist": "Seiko",
    "lord matic": "Seiko",
    "lordmatic": "Seiko",
    "bell-matic": "Seiko",
    "bellmatic": "Seiko",
    "conquest": "Longines",
    "khaki field titanium": "Hamilton",
    "jet star": "Bulova",
    "tsuyosa": "Citizen",
    "5 sports gmt": "Seiko",
    "sports gmt": "Seiko",
    "mojito": "Seiko",
    "srpe45": "Seiko",
    "lunar pilot": "Bulova",
    "96b251": "Bulova",
    "96b258": "Bulova",
    "meteorite": "Traska",
    "venturer": "Traska",
}


def expected_brand_for(listing: Listing) -> Optional[str]:
    """Return the brand this listing's title claims to be, based on
    which price-band keyword matched. Used for brand verification."""
    title_lower = listing.title.lower()
    for keyword, brand in BRAND_BY_KEYWORD.items():
        if keyword in title_lower:
            return brand
    return None


def estimate_value(listing: Listing) -> Optional[Tuple[float, float]]:
    title_lower = listing.title.lower()
    for keyword, band in PRICE_BANDS.items():
        if keyword in title_lower:
            return band
    return None

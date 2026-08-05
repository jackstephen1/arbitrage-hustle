# Collectibles Arbitrage Finder

Automated system that scans eBay live listings for undervalued watches,
vintage items, cameras, Pokémon cards, and sports cards, compares each
listing against an estimated "true market value," and flags/emails deals
that clear a minimum discount threshold.

## How it's structured

- `core/ebay_client.py` — handles eBay OAuth token management and the
  Browse API search call. Shared by every category.
- `core/deal_finder.py` — the main runner. Loops over enabled categories,
  pulls listings, scores them, and sends an alert for anything good.
- `core/models.py` — shared data structures (Listing, Deal).
- `categories/` — one file per collectible type. Each defines:
  - what search terms to run
  - how to estimate "true value" for a given listing
  - the minimum discount % to count as a deal
  - `categories/watches.py` is built out first; the others are stubs
    ready to fill in once watches is proven out.
- `.github/workflows/run.yml` — scheduled GitHub Action, same pattern as
  your market intelligence agent. Runs the scanner on a schedule and
  emails you results.

## Setup

1. **Get eBay API credentials**
   - Sign up at https://developer.ebay.com
   - Create an application keyset (Application Keys page)
   - You need: `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` (Production keys,
     once you're past testing — start with Sandbox keys to confirm
     everything works, since Sandbox has separate credentials)

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Set environment variables** (locally in a `.env` file, or as GitHub
   Actions secrets for the scheduled version):
   ```
   EBAY_CLIENT_ID=your_client_id
   EBAY_CLIENT_SECRET=your_client_secret
   EBAY_ENV=SANDBOX   # or PRODUCTION
   ALERT_EMAIL_TO=you@example.com
   ALERT_EMAIL_FROM=your_agent@example.com
   SMTP_HOST=...
   SMTP_USER=...
   SMTP_PASS=...
   ```

4. **Run it**
   ```
   python -m core.deal_finder
   ```

## Watches: how "true value" is estimated (v1)

For the first version, `categories/watches.py` uses a simple reference
table of known models/references mapped to an approximate current market
price band (you fill these in — pulled manually from Chrono24 or
WatchCharts for the models you care about). A listing is flagged as a
deal when its price is more than `MIN_DISCOUNT_PCT` below the low end of
that band.

This is intentionally simple to start. Natural next upgrades (once this
is running and you trust the eBay-search half):
- Pull WatchCharts/Chrono24 pricing automatically instead of a manual
  table (their public APIs are limited/unofficial, so this usually means
  scraping — worth doing carefully and checking each site's terms of
  service first)
- Parse listing titles more precisely to extract reference numbers,
  box/papers status, condition
- Track price history per model over time instead of a single band

## Adding a new category (cameras, Pokémon, sports cards, vintage)

Copy `categories/_template.py`, fill in:
- `SEARCH_TERMS` — eBay keyword searches to run
- `CATEGORY_ID` — eBay category ID to restrict results to (optional but
  recommended, cuts down noise)
- `estimate_value(listing)` — your valuation logic for that category
- `MIN_DISCOUNT_PCT` — how big a gap counts as a "deal" for this category

Register it in `core/deal_finder.py`'s `ENABLED_CATEGORIES` list.

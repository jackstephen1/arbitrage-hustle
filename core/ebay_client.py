"""
Minimal eBay Browse API client.

Handles OAuth2 client-credentials token generation (no user login needed —
we're only searching public listings) and the item_summary/search call.

Docs: https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
"""

import base64
import os
import time
from typing import List, Optional
from urllib.parse import quote

import requests

from core.models import Listing


class EbayClient:
    def __init__(self):
        self.client_id = os.environ["EBAY_CLIENT_ID"]
        self.client_secret = os.environ["EBAY_CLIENT_SECRET"]
        self.env = os.environ.get("EBAY_ENV", "PRODUCTION").upper()

        if self.env == "SANDBOX":
            self.token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            self.search_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
        else:
            self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"
            self.search_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    def _get_token(self) -> str:
        """Return a cached token, refreshing it if it's expired or missing."""
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        resp = requests.post(
            self.token_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded}",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()

        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload["expires_in"]
        return self._token

    def search(
        self,
        query: str,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        condition: Optional[str] = None,
        limit: int = 50,
    ) -> List[Listing]:
        """Search live eBay listings. Returns a list of Listing objects."""
        token = self._get_token()

        filters = []
        if min_price is not None or max_price is not None:
            lo = min_price if min_price is not None else ""
            hi = max_price if max_price is not None else ""
            filters.append(f"price:[{lo}..{hi}]")
            filters.append("priceCurrency:USD")
        if condition:
            filters.append(f"conditions:{{{condition}}}")

        params = {"q": query, "limit": limit}
        if category_id:
            params["category_ids"] = category_id
        if filters:
            params["filter"] = ",".join(filters)

        resp = requests.get(
            self.search_url,
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            },
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()

        listings = []
        for item in data.get("itemSummaries", []):
            price_info = item.get("price", {})
            seller_info = item.get("seller", {})
            image_info = item.get("image", {})

            shipping_cost = 0.0
            shipping_options = item.get("shippingOptions", [])
            if shipping_options:
                cost_info = shipping_options[0].get("shippingCost", {})
                try:
                    shipping_cost = float(cost_info.get("value", 0))
                except (TypeError, ValueError):
                    shipping_cost = 0.0

            listings.append(
                Listing(
                    item_id=item.get("itemId", ""),
                    title=item.get("title", ""),
                    price=float(price_info.get("value", 0)),
                    currency=price_info.get("currency", "USD"),
                    condition=item.get("condition"),
                    url=item.get("itemWebUrl", ""),
                    image_url=image_info.get("imageUrl"),
                    seller_username=seller_info.get("username"),
                    seller_feedback_score=seller_info.get("feedbackScore"),
                    shipping_cost=shipping_cost,
                )
            )
        return listings

    def get_item_brand(self, item_id: str) -> str:
        """
        Fetch a single item's details and return its declared brand
        (e.g. "Seiko", "Citizen"), or "" if not available. Used to verify
        a listing's actual brand matches what its title claims — some
        sellers reuse listing templates or mislabel items, so title text
        alone isn't reliable enough to trust for a "deal" decision.
        """
        token = self._get_token()
        encoded_id = quote(item_id, safe="")
        url = f"{self.search_url.rsplit('/item_summary', 1)[0]}/item/{encoded_id}"

        try:
            resp = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return ""

        for aspect in data.get("localizedAspects", []):
            if aspect.get("name", "").lower() == "brand":
                return aspect.get("value", "")

        return data.get("brand", "")

"""
Google Places API (New) Scraper.

Sucht lokale Unternehmen in einem Gebiet und filtert die ohne eigene Website.
Docs: https://developers.google.com/maps/documentation/places/web-service/text-search
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from dotenv import load_dotenv

from . import storage

load_dotenv()

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"

# Felder die wir vom Search-Endpoint anfordern. Spart Kosten + Bandbreite.
SEARCH_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.types",
    "places.primaryType",
    "places.websiteUri",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.googleMapsUri",
    "nextPageToken",
])


class ScraperError(Exception):
    pass


def _api_key() -> str:
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        raise ScraperError(
            "GOOGLE_PLACES_API_KEY fehlt. Lege backend/.env an (siehe .env.example)."
        )
    return key


def search_text(
    query: str,
    *,
    language: str = "de",
    region: str | None = None,
    max_pages: int = 3,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """
    Volltext-Suche, z.B. 'Friseur in Berlin Mitte' oder 'restoran di Bali'.
    Gibt Roh-Places zurück (ungefiltert).
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": _api_key(),
        "X-Goog-FieldMask": SEARCH_FIELD_MASK,
    }

    results: list[dict[str, Any]] = []
    page_token: str | None = None

    with httpx.Client(timeout=30.0) as client:
        for page in range(max_pages):
            body: dict[str, Any] = {
                "textQuery": query,
                "languageCode": language,
                "pageSize": page_size,
            }
            if region:
                body["regionCode"] = region
            if page_token:
                body["pageToken"] = page_token
                # Google verlangt kurze Wartezeit bevor pageToken gültig ist
                time.sleep(2)

            resp = client.post(PLACES_TEXT_SEARCH_URL, headers=headers, json=body)
            if resp.status_code != 200:
                raise ScraperError(
                    f"Places API Fehler {resp.status_code}: {resp.text[:300]}"
                )
            data = resp.json()
            results.extend(data.get("places", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return results


def _normalize(place: dict[str, Any]) -> dict[str, Any]:
    """Vereinheitlicht das Google-Format zu unserem internen Lead-Schema."""
    loc = place.get("location") or {}
    name = (place.get("displayName") or {}).get("text") or ""
    return {
        "id": place["id"],
        "name": name,
        "address": place.get("formattedAddress"),
        "lat": loc.get("latitude"),
        "lng": loc.get("longitude"),
        "phone": place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"),
        "website": place.get("websiteUri"),
        "primary_type": place.get("primaryType"),
        "types": place.get("types", []),
        "rating": place.get("rating"),
        "rating_count": place.get("userRatingCount"),
        "business_status": place.get("businessStatus"),
        "google_maps_uri": place.get("googleMapsUri"),
        "discovered_at": datetime.now(timezone.utc).isoformat(),
    }


def find_leads(
    query: str,
    *,
    language: str = "de",
    region: str | None = None,
    max_pages: int = 3,
    only_without_website: bool = True,
    only_operational: bool = True,
    persist: bool = True,
) -> dict[str, Any]:
    """
    Hauptfunktion: sucht, filtert (ohne Website), speichert in data/leads.json.
    """
    raw = search_text(query, language=language, region=region, max_pages=max_pages)
    normalized = [_normalize(p) for p in raw]

    leads = normalized
    if only_operational:
        leads = [l for l in leads if (l.get("business_status") or "OPERATIONAL") == "OPERATIONAL"]
    if only_without_website:
        leads = [l for l in leads if not l.get("website")]

    if persist:
        for lead in leads:
            storage.upsert("leads", {
                **lead,
                "source_query": query,
                "status": "new",
            })

    return {
        "query": query,
        "total_found": len(normalized),
        "leads_without_website": len(leads),
        "leads": leads,
    }

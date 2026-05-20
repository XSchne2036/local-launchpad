"""
Mehrsprachigkeit: Auto-Detect (Region/Adresse → Sprache) + Batch-Übersetzung
der strukturierten Webseiten-Inhalte via Lovable AI Gateway.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

from .ai import GATEWAY_URL, DEFAULT_MODEL, AIError, _key

load_dotenv()

SUPPORTED_LANGUAGES = ["de", "en", "id"]
DEFAULT_LANGUAGE = "de"

# ISO-Region (ccTLD-ähnlich) → Sprache
REGION_TO_LANGUAGE: dict[str, str] = {
    "DE": "de", "AT": "de", "CH": "de", "LI": "de", "LU": "de",
    "ID": "id",
    "US": "en", "GB": "en", "IE": "en", "AU": "en", "NZ": "en", "CA": "en",
    "SG": "en", "MY": "en", "PH": "en", "IN": "en", "ZA": "en",
}

# Heuristik: Schlüsselwörter in Adresse → Region (für Leads ohne expliziten Region-Code)
ADDRESS_HINTS: list[tuple[str, str]] = [
    ("Deutschland", "DE"), ("Germany", "DE"),
    ("Österreich", "AT"), ("Austria", "AT"),
    ("Schweiz", "CH"), ("Switzerland", "CH"), ("Suisse", "CH"),
    ("Indonesia", "ID"), ("Bali", "ID"), ("Jakarta", "ID"),
    ("United Kingdom", "GB"), ("England", "GB"), ("Scotland", "GB"),
    ("United States", "US"), ("USA", "US"),
    ("Australia", "AU"), ("Canada", "CA"), ("Singapore", "SG"),
]


def detect_region(lead: dict[str, Any]) -> str | None:
    """Versucht Region aus Lead zu raten (explizites Feld → Adress-Heuristik)."""
    r = lead.get("region") or lead.get("region_code")
    if r:
        return r.upper()
    addr = (lead.get("address") or "")
    for needle, code in ADDRESS_HINTS:
        if needle.lower() in addr.lower():
            return code
    return None


def detect_language(lead: dict[str, Any], fallback: str = DEFAULT_LANGUAGE) -> str:
    """Region → Sprache. Fällt auf fallback zurück."""
    region = detect_region(lead)
    if region and region in REGION_TO_LANGUAGE:
        return REGION_TO_LANGUAGE[region]
    return fallback


# ---------- Batch-Übersetzung ----------

TRANSLATE_SCHEMA = {
    "name": "translated_content",
    "description": "Übersetzte Variante des Webseiten-Inhalts. Struktur 1:1 erhalten.",
    "parameters": {
        "type": "object",
        "properties": {
            "language": {"type": "string"},
            "tagline": {"type": "string"},
            "hero_title": {"type": "string"},
            "hero_subtitle": {"type": "string"},
            "about": {"type": "string"},
            "services": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["title", "description"],
                },
            },
            "why_choose_us": {"type": "array", "items": {"type": "string"}},
            "cta_text": {"type": "string"},
            "seo_title": {"type": "string"},
            "seo_description": {"type": "string"},
        },
        "required": [
            "language", "tagline", "hero_title", "hero_subtitle", "about",
            "services", "why_choose_us", "cta_text", "seo_title", "seo_description",
        ],
    },
}

LANG_NAMES = {"de": "Deutsch", "en": "English", "id": "Bahasa Indonesia"}


def translate_content(
    content: dict[str, Any],
    target_language: str,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Übersetzt den Inhalts-Dict in eine Zielsprache. Behält Struktur, Farben, Branding bei."""
    if target_language not in SUPPORTED_LANGUAGES:
        raise AIError(f"Sprache '{target_language}' nicht unterstützt. Erlaubt: {SUPPORTED_LANGUAGES}")

    src_lang = content.get("language", "?")
    if src_lang == target_language:
        return content  # nichts zu tun

    # Nur übersetzbare Felder isolieren (Farben/etc. unverändert übernehmen)
    payload = {k: content.get(k) for k in [
        "tagline", "hero_title", "hero_subtitle", "about", "services",
        "why_choose_us", "cta_text", "seo_title", "seo_description",
    ]}

    sys_prompt = (
        f"Du bist ein professioneller Marketing-Übersetzer. Übersetze den folgenden "
        f"Webseiten-Inhalt von '{src_lang}' nach '{LANG_NAMES.get(target_language, target_language)}'. "
        f"Bewahre Ton, Marken-Eigennamen und Struktur. Keine wörtliche, sondern eine "
        f"natürliche, lokal idiomatische Übersetzung. Antworte ausschließlich über das Tool."
    )
    user_prompt = "Quelle (JSON):\n" + json.dumps(payload, ensure_ascii=False, indent=2)

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "tools": [{"type": "function", "function": TRANSLATE_SCHEMA}],
        "tool_choice": {"type": "function", "function": {"name": "translated_content"}},
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {_key()}"}

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(GATEWAY_URL, headers=headers, json=body)

    if resp.status_code == 402:
        raise AIError("Lovable AI: Credits aufgebraucht.")
    if resp.status_code == 429:
        raise AIError("Lovable AI: Rate Limit. Kurz warten.")
    if resp.status_code != 200:
        raise AIError(f"Lovable AI Fehler {resp.status_code}: {resp.text[:300]}")

    try:
        tc = resp.json()["choices"][0]["message"]["tool_calls"][0]
        args = tc["function"]["arguments"]
        translated = json.loads(args) if isinstance(args, str) else args
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise AIError(f"Übersetzung nicht parsebar: {e}")

    # Original-Felder, die NICHT übersetzt werden (Farben, Sprache überschreiben)
    merged = {**content, **translated, "language": target_language}
    return merged


def translate_batch(
    content: dict[str, Any],
    target_languages: list[str],
) -> dict[str, dict[str, Any]]:
    """Übersetzt in mehrere Zielsprachen. Gibt {lang: content} zurück."""
    out: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    for lang in target_languages:
        try:
            out[lang] = translate_content(content, lang)
        except AIError as e:
            errors[lang] = str(e)
    if errors and not out:
        raise AIError(f"Alle Übersetzungen fehlgeschlagen: {errors}")
    return out

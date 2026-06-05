"""
Lovable AI Gateway Client.
Generiert strukturierte Website-Inhalte aus einem Lead.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

GATEWAY_URL = "https://ai.gateway.lovable.dev/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3-flash-preview"


class AIError(Exception):
    pass


def _key() -> str:
    k = os.getenv("LOVABLE_API_KEY")
    if not k:
        raise AIError("LOVABLE_API_KEY fehlt. Setze ihn in backend/.env.")
    return k


CONTENT_SCHEMA = {
    "name": "website_content",
    "description": "Strukturierter Inhalt für eine kleine Business-Webseite.",
    "parameters": {
        "type": "object",
        "properties": {
            "language": {"type": "string", "description": "ISO-Code: de, en, id"},
            "tagline": {"type": "string", "description": "Kurzer Slogan, max 80 Zeichen"},
            "hero_title": {"type": "string"},
            "hero_subtitle": {"type": "string"},
            "about": {"type": "string", "description": "2-3 Sätze über das Unternehmen"},
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
                "minItems": 3,
                "maxItems": 6,
            },
            "why_choose_us": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 5,
            },
            "cta_text": {"type": "string"},
            "color_primary": {"type": "string", "description": "Hex, z.B. #1e40af"},
            "color_accent": {"type": "string", "description": "Hex"},
            "seo_title": {"type": "string"},
            "seo_description": {"type": "string"},
        },
        "required": [
            "language", "tagline", "hero_title", "hero_subtitle", "about",
            "services", "why_choose_us", "cta_text", "color_primary",
            "color_accent", "seo_title", "seo_description",
        ],
    },
}


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60] or "site"


def generate_content(
    lead: dict[str, Any],
    language: str = "de",
    model: str = DEFAULT_MODEL,
    theme: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generiert Webseiten-Inhalt für ein Lead via Lovable AI Gateway (Tool-Calling für Struktur)."""
    from . import themes as _themes
    theme = theme or _themes.detect_theme(lead)
    business_type = lead.get("primary_type") or "local business"

    sys_prompt = (
        f"Du erstellst hochwertige, lokal optimierte Webseiten-Inhalte in der Sprache '{language}'. "
        f"Die Branche ist '{theme['name']}'. Schreibe im Ton: {theme['tone']}. "
        f"Sei konkret, vertrauenswürdig, vermeide generische Floskeln. "
        f"Empfohlene Farbpalette (kann übernommen werden): primary={theme['primary']}, accent={theme['accent']}. "
        f"Wähle nur dann andere Farben, wenn sie eindeutig besser zum Unternehmen passen."
    )
    user_prompt = (
        f"Erstelle den Inhalt für die Webseite folgenden Unternehmens:\n\n"
        f"Name: {lead.get('name')}\n"
        f"Branche: {business_type} (Theme: {theme['name']})\n"
        f"Adresse: {lead.get('address')}\n"
        f"Telefon: {lead.get('phone') or 'unbekannt'}\n"
        f"Google Bewertung: {lead.get('rating')} ({lead.get('rating_count')} Reviews)\n"
        f"Typen: {', '.join(lead.get('types', []))}\n\n"
        f"Sprache: {language}. Nutze ausschließlich diese Sprache."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "tools": [{"type": "function", "function": CONTENT_SCHEMA}],
        "tool_choice": {"type": "function", "function": {"name": "website_content"}},
    }

    headers = {
        "Content-Type": "application/json",
        "Lovable-API-Key": _key(),
        "X-Lovable-AIG-SDK": "locallift-backend",
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(GATEWAY_URL, headers=headers, json=body)

    if resp.status_code == 402:
        raise AIError("Lovable AI: Credits aufgebraucht. Workspace aufladen.")
    if resp.status_code == 429:
        raise AIError("Lovable AI: Rate Limit erreicht. Kurz warten und neu versuchen.")
    if resp.status_code != 200:
        raise AIError(f"Lovable AI Fehler {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        tool_call = data["choices"][0]["message"]["tool_calls"][0]
        args = tool_call["function"]["arguments"]
        return json.loads(args) if isinstance(args, str) else args
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise AIError(f"Konnte AI-Antwort nicht parsen: {e}; raw={str(data)[:300]}")

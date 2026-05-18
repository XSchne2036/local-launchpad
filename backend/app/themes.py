"""
Branchen-spezifisches Theme-System.

Mappt Google-Places-Types → Theme (Farben, Fonts, Hero-Style, Sektions-Labels, Ton).
Wird vom Renderer (Look) und von der AI (Ton + bevorzugte Farben) genutzt.
"""
from __future__ import annotations

from typing import Any


# ----- Labels pro Sprache (Sektionen) -----
LABELS: dict[str, dict[str, str]] = {
    "de": {
        "about": "Über uns", "services": "Leistungen", "why": "Warum wir",
        "contact": "Kontakt", "services_lead": "Was wir für Sie tun können.",
        "contact_lead": "Wir freuen uns auf Ihre Nachricht.",
        "phone": "Telefon", "address": "Adresse", "maps": "Auf Google Maps",
        "directions": "Route ansehen",
        "claim_q": "Ist das Ihr Unternehmen?",
        "claim_cta": "Jetzt kostenlos übernehmen →",
        "footer_made": "Webseite erstellt mit",
    },
    "en": {
        "about": "About", "services": "Services", "why": "Why us",
        "contact": "Contact", "services_lead": "What we can do for you.",
        "contact_lead": "We look forward to hearing from you.",
        "phone": "Phone", "address": "Address", "maps": "On Google Maps",
        "directions": "Get directions",
        "claim_q": "Is this your business?",
        "claim_cta": "Claim it for free →",
        "footer_made": "Website built with",
    },
    "id": {
        "about": "Tentang Kami", "services": "Layanan", "why": "Mengapa Kami",
        "contact": "Kontak", "services_lead": "Apa yang bisa kami lakukan.",
        "contact_lead": "Kami senang mendengar dari Anda.",
        "phone": "Telepon", "address": "Alamat", "maps": "Di Google Maps",
        "directions": "Lihat rute",
        "claim_q": "Apakah ini bisnis Anda?",
        "claim_cta": "Klaim gratis sekarang →",
        "footer_made": "Situs web dibuat dengan",
    },
}


def labels(lang: str) -> dict[str, str]:
    return LABELS.get(lang, LABELS["de"])


# ----- Themes -----
# Felder:
#   key, name, tone (AI), primary, accent, bg, fg, muted, card, border,
#   font_heading, font_body, hero_style (centered|split|imagery),
#   radius, shadow, badge_emoji
THEMES: dict[str, dict[str, Any]] = {
    "restaurant": {
        "key": "restaurant", "name": "Restaurant",
        "tone": "warm, einladend, appetitanregend, ehrlich-rustikal",
        "primary": "#b91c1c", "accent": "#f59e0b",
        "bg": "#fffaf5", "fg": "#1c1410", "muted": "#78716c",
        "card": "#fef3e2", "border": "#f5e1c8",
        "font_heading": "'Playfair Display', Georgia, serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "imagery", "radius": "14px",
        "shadow": "0 18px 40px -20px rgba(185,28,28,.35)",
        "badge_emoji": "🍽️",
    },
    "cafe": {
        "key": "cafe", "name": "Café / Bäckerei",
        "tone": "gemütlich, handwerklich, warm, persönlich",
        "primary": "#92400e", "accent": "#d97706",
        "bg": "#fdf8f1", "fg": "#1f1611", "muted": "#78716c",
        "card": "#fbf1e1", "border": "#ecddc4",
        "font_heading": "'Fraunces', Georgia, serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "imagery", "radius": "18px",
        "shadow": "0 16px 32px -18px rgba(146,64,14,.35)",
        "badge_emoji": "☕",
    },
    "beauty": {
        "key": "beauty", "name": "Beauty / Friseur / Spa",
        "tone": "elegant, ruhig, hochwertig, selbstbewusst",
        "primary": "#9d174d", "accent": "#f472b6",
        "bg": "#fdf6f9", "fg": "#1a0f15", "muted": "#6b5560",
        "card": "#fce7f3", "border": "#f7d2e2",
        "font_heading": "'Cormorant Garamond', Georgia, serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "split", "radius": "20px",
        "shadow": "0 20px 40px -22px rgba(157,23,77,.35)",
        "badge_emoji": "💇",
    },
    "fitness": {
        "key": "fitness", "name": "Fitness / Sport",
        "tone": "energisch, motivierend, direkt, kraftvoll",
        "primary": "#0f172a", "accent": "#22d3ee",
        "bg": "#0b1120", "fg": "#f8fafc", "muted": "#94a3b8",
        "card": "#111827", "border": "#1f2937",
        "font_heading": "'Archivo Black', sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "centered", "radius": "10px",
        "shadow": "0 20px 50px -20px rgba(34,211,238,.45)",
        "badge_emoji": "💪",
    },
    "medical": {
        "key": "medical", "name": "Medizin / Praxis",
        "tone": "vertrauenswürdig, ruhig, kompetent, sachlich",
        "primary": "#0e7490", "accent": "#06b6d4",
        "bg": "#f8fbfd", "fg": "#0f172a", "muted": "#64748b",
        "card": "#ecfeff", "border": "#cffafe",
        "font_heading": "'Inter', system-ui, sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "split", "radius": "12px",
        "shadow": "0 16px 32px -20px rgba(14,116,144,.25)",
        "badge_emoji": "🩺",
    },
    "legal": {
        "key": "legal", "name": "Recht / Beratung",
        "tone": "seriös, präzise, vertrauensbildend, formell",
        "primary": "#1e3a8a", "accent": "#b45309",
        "bg": "#f8fafc", "fg": "#0f1b3d", "muted": "#475569",
        "card": "#f1f5f9", "border": "#e2e8f0",
        "font_heading": "'Libre Baskerville', Georgia, serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "centered", "radius": "6px",
        "shadow": "0 14px 30px -18px rgba(30,58,138,.3)",
        "badge_emoji": "⚖️",
    },
    "automotive": {
        "key": "automotive", "name": "Werkstatt / Auto",
        "tone": "robust, ehrlich, technisch versiert, lokal",
        "primary": "#1f2937", "accent": "#f97316",
        "bg": "#f4f4f5", "fg": "#0f172a", "muted": "#52525b",
        "card": "#ffffff", "border": "#e4e4e7",
        "font_heading": "'Oswald', Impact, sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "centered", "radius": "8px",
        "shadow": "0 14px 30px -18px rgba(249,115,22,.4)",
        "badge_emoji": "🔧",
    },
    "craft": {
        "key": "craft", "name": "Handwerk",
        "tone": "bodenständig, zuverlässig, regional, ehrlich",
        "primary": "#166534", "accent": "#84cc16",
        "bg": "#fafaf7", "fg": "#1c1917", "muted": "#57534e",
        "card": "#f5f5f0", "border": "#e7e5e0",
        "font_heading": "'Work Sans', system-ui, sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "split", "radius": "10px",
        "shadow": "0 14px 30px -18px rgba(22,101,52,.3)",
        "badge_emoji": "🔨",
    },
    "retail": {
        "key": "retail", "name": "Einzelhandel / Boutique",
        "tone": "stilvoll, einladend, kuratiert, persönlich",
        "primary": "#7c3aed", "accent": "#ec4899",
        "bg": "#fbfaff", "fg": "#1e1b2e", "muted": "#6b7280",
        "card": "#f5f3ff", "border": "#ede9fe",
        "font_heading": "'Syne', system-ui, sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "imagery", "radius": "16px",
        "shadow": "0 18px 36px -20px rgba(124,58,237,.35)",
        "badge_emoji": "🛍️",
    },
    "hospitality": {
        "key": "hospitality", "name": "Hotel / Unterkunft",
        "tone": "gastfreundlich, ruhig, vertrauenswürdig, hochwertig",
        "primary": "#0c4a6e", "accent": "#0ea5e9",
        "bg": "#f8fafc", "fg": "#0f172a", "muted": "#64748b",
        "card": "#e0f2fe", "border": "#bae6fd",
        "font_heading": "'Cormorant Garamond', Georgia, serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "imagery", "radius": "14px",
        "shadow": "0 16px 32px -18px rgba(14,116,144,.35)",
        "badge_emoji": "🏨",
    },
    "default": {
        "key": "default", "name": "Standard",
        "tone": "professionell, klar, freundlich, vertrauenswürdig",
        "primary": "#1e40af", "accent": "#3b82f6",
        "bg": "#ffffff", "fg": "#0f172a", "muted": "#64748b",
        "card": "#f8fafc", "border": "#e2e8f0",
        "font_heading": "'Inter', system-ui, sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "hero_style": "centered", "radius": "12px",
        "shadow": "0 14px 30px -18px rgba(30,64,175,.3)",
        "badge_emoji": "✨",
    },
}


# Google Places primary_type / types → Theme-Key
TYPE_MAP: dict[str, str] = {
    # restaurant
    "restaurant": "restaurant", "meal_takeaway": "restaurant",
    "meal_delivery": "restaurant", "pizza_restaurant": "restaurant",
    "italian_restaurant": "restaurant", "asian_restaurant": "restaurant",
    "fast_food_restaurant": "restaurant", "bar_and_grill": "restaurant",
    "steak_house": "restaurant", "seafood_restaurant": "restaurant",
    "vegetarian_restaurant": "restaurant", "food": "restaurant",
    # cafe
    "cafe": "cafe", "bakery": "cafe", "coffee_shop": "cafe",
    "ice_cream_shop": "cafe", "dessert_shop": "cafe",
    # beauty
    "hair_salon": "beauty", "beauty_salon": "beauty",
    "nail_salon": "beauty", "spa": "beauty", "barber_shop": "beauty",
    "hair_care": "beauty",
    # fitness
    "gym": "fitness", "fitness_center": "fitness",
    "yoga_studio": "fitness", "sports_club": "fitness",
    # medical
    "doctor": "medical", "dentist": "medical", "physiotherapist": "medical",
    "hospital": "medical", "pharmacy": "medical", "veterinary_care": "medical",
    "medical_lab": "medical", "health": "medical",
    # legal
    "lawyer": "legal", "accounting": "legal", "consultant": "legal",
    "tax_consultant": "legal", "notary_public": "legal",
    # automotive
    "car_repair": "automotive", "car_dealer": "automotive",
    "car_wash": "automotive", "auto_parts_store": "automotive",
    "gas_station": "automotive",
    # craft
    "plumber": "craft", "electrician": "craft", "roofing_contractor": "craft",
    "painter": "craft", "carpenter": "craft", "locksmith": "craft",
    "general_contractor": "craft", "moving_company": "craft",
    # retail
    "clothing_store": "retail", "shoe_store": "retail", "jewelry_store": "retail",
    "book_store": "retail", "florist": "retail", "gift_shop": "retail",
    "boutique": "retail", "store": "retail",
    # hospitality
    "lodging": "hospitality", "hotel": "hospitality",
    "bed_and_breakfast": "hospitality", "guest_house": "hospitality",
}


def detect_theme(lead: dict[str, Any]) -> dict[str, Any]:
    """Wählt das passende Theme für einen Lead."""
    candidates = [lead.get("primary_type")] + list(lead.get("types") or [])
    for t in candidates:
        if not t:
            continue
        key = TYPE_MAP.get(t.lower())
        if key:
            return THEMES[key]
    return THEMES["default"]


def get_theme(key: str) -> dict[str, Any]:
    return THEMES.get(key, THEMES["default"])


def list_themes() -> list[dict[str, Any]]:
    return list(THEMES.values())

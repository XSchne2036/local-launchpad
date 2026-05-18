"""HTML-Renderer für generierte Webseiten. Theme-getrieben (siehe themes.py)."""
from __future__ import annotations

import html
from typing import Any

from . import themes


def _e(s: Any) -> str:
    return html.escape(str(s or ""))


def render_site(
    lead: dict[str, Any],
    content: dict[str, Any],
    slug: str,
    theme: dict[str, Any] | None = None,
    base_url: str = "",
) -> str:
    theme = theme or themes.detect_theme(lead)
    lang = content.get("language", "de")
    L = themes.labels(lang)

    # AI darf Farben überschreiben, sonst Theme-Default
    primary = content.get("color_primary") or theme["primary"]
    accent = content.get("color_accent") or theme["accent"]

    services_html = "\n".join(
        f"""<div class="card">
            <div class="card-icon">{theme['badge_emoji']}</div>
            <h3>{_e(s.get('title'))}</h3>
            <p>{_e(s.get('description'))}</p>
        </div>"""
        for s in content.get("services", [])
    )
    why_html = "\n".join(f"<li>{_e(w)}</li>" for w in content.get("why_choose_us", []))

    phone = lead.get("phone")
    address = lead.get("address")
    maps_uri = lead.get("google_maps_uri")
    rating = lead.get("rating")
    rating_count = lead.get("rating_count")

    # Hero-Varianten
    hero_style = theme["hero_style"]
    if hero_style == "split":
        hero_html = f"""
<div class="hero hero-split">
  <div class="container hero-grid">
    <div>
      <span class="tagline">{theme['badge_emoji']} {_e(content.get('tagline'))}</span>
      <h1>{_e(content.get('hero_title'))}</h1>
      <p>{_e(content.get('hero_subtitle'))}</p>
      <a class="btn" href="#contact">{_e(content.get('cta_text'))}</a>
    </div>
    <div class="hero-visual"><div class="hero-blob"></div><div class="hero-emoji">{theme['badge_emoji']}</div></div>
  </div>
</div>"""
    elif hero_style == "imagery":
        hero_html = f"""
<div class="hero hero-imagery">
  <div class="hero-bg"></div>
  <div class="container hero-content">
    <span class="tagline">{theme['badge_emoji']} {_e(content.get('tagline'))}</span>
    <h1>{_e(content.get('hero_title'))}</h1>
    <p>{_e(content.get('hero_subtitle'))}</p>
    <a class="btn" href="#contact">{_e(content.get('cta_text'))}</a>
  </div>
</div>"""
    else:  # centered
        hero_html = f"""
<div class="hero hero-centered">
  <div class="container">
    <span class="tagline">{theme['badge_emoji']} {_e(content.get('tagline'))}</span>
    <h1>{_e(content.get('hero_title'))}</h1>
    <p>{_e(content.get('hero_subtitle'))}</p>
    <a class="btn" href="#contact">{_e(content.get('cta_text'))}</a>
  </div>
</div>"""

    rating_badge = (
        f'<div class="rating">★ {rating} <span>({rating_count})</span></div>'
        if rating else ""
    )

    return f"""<!DOCTYPE html>
<html lang="{_e(lang)}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{_e(content.get('seo_title'))}</title>
<meta name="description" content="{_e(content.get('seo_description'))}" />
<meta property="og:title" content="{_e(content.get('seo_title'))}" />
<meta property="og:description" content="{_e(content.get('seo_description'))}" />
<meta name="theme-color" content="{primary}" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&family=Fraunces:wght@600;700&family=Cormorant+Garamond:wght@600;700&family=Archivo+Black&family=Oswald:wght@600;700&family=Libre+Baskerville:wght@700&family=Syne:wght@600;700&family=Work+Sans:wght@600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --primary: {primary};
  --accent: {accent};
  --bg: {theme['bg']};
  --fg: {theme['fg']};
  --muted: {theme['muted']};
  --card: {theme['card']};
  --border: {theme['border']};
  --radius: {theme['radius']};
  --shadow: {theme['shadow']};
  --font-h: {theme['font_heading']};
  --font-b: {theme['font_body']};
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: var(--bg); color: var(--fg); font: 16px/1.6 var(--font-b); -webkit-font-smoothing: antialiased; }}
h1, h2, h3 {{ font-family: var(--font-h); font-weight: 700; letter-spacing: -.015em; }}
a {{ color: var(--primary); text-decoration: none; }}
.container {{ max-width: 1140px; margin: 0 auto; padding: 0 24px; }}
header {{ padding: 18px 0; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter: blur(10px); z-index: 10; }}
header .row {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; }}
.brand {{ font-family: var(--font-h); font-weight: 700; font-size: 1.15rem; color: var(--fg); display: flex; align-items: center; gap: 10px; }}
.brand .dot {{ width: 28px; height: 28px; border-radius: 8px; background: linear-gradient(135deg, var(--primary), var(--accent)); display: grid; place-items: center; color: white; font-size: 14px; }}
.rating {{ font-size: .85rem; color: var(--muted); font-weight: 600; }}
.rating span {{ color: var(--muted); font-weight: 400; }}
.btn {{ display: inline-block; background: linear-gradient(135deg, var(--primary), color-mix(in srgb, var(--primary) 80%, var(--accent))); color: white; padding: 13px 24px; border-radius: var(--radius); font-weight: 600; transition: transform .15s, box-shadow .2s; box-shadow: var(--shadow); }}
.btn:hover {{ transform: translateY(-2px); }}

/* Hero variants */
.hero {{ padding: 90px 0 80px; position: relative; overflow: hidden; }}
.hero h1 {{ font-size: clamp(2.2rem, 5.2vw, 3.8rem); line-height: 1.05; margin-bottom: 20px; }}
.hero p {{ font-size: 1.15rem; color: var(--muted); margin-bottom: 30px; max-width: 580px; }}
.tagline {{ display: inline-block; padding: 6px 14px; border-radius: 999px; background: color-mix(in srgb, var(--accent) 15%, var(--bg)); border: 1px solid var(--border); color: var(--primary); font-size: .85rem; font-weight: 600; margin-bottom: 22px; }}

.hero-centered {{ text-align: center; background: radial-gradient(ellipse at top, color-mix(in srgb, var(--accent) 15%, transparent), transparent 70%); }}
.hero-centered p {{ margin-left: auto; margin-right: auto; }}

.hero-split .hero-grid {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 60px; align-items: center; }}
.hero-visual {{ aspect-ratio: 1; position: relative; display: grid; place-items: center; }}
.hero-blob {{ position: absolute; inset: 0; background: linear-gradient(135deg, var(--primary), var(--accent)); border-radius: 40% 60% 55% 45% / 50% 45% 55% 50%; opacity: .85; animation: blob 14s ease-in-out infinite; }}
.hero-emoji {{ position: relative; font-size: clamp(5rem, 14vw, 9rem); filter: drop-shadow(0 8px 20px rgba(0,0,0,.25)); }}
@keyframes blob {{ 50% {{ border-radius: 55% 45% 40% 60% / 45% 55% 45% 55%; }} }}

.hero-imagery {{ color: white; min-height: 520px; display: flex; align-items: center; }}
.hero-imagery .hero-bg {{ position: absolute; inset: 0; background: linear-gradient(135deg, var(--primary), color-mix(in srgb, var(--accent) 70%, var(--primary))); }}
.hero-imagery .hero-bg::after {{ content: ""; position: absolute; inset: 0; background: radial-gradient(circle at 80% 20%, color-mix(in srgb, var(--accent) 70%, transparent), transparent 60%); opacity: .8; }}
.hero-imagery .hero-content {{ position: relative; }}
.hero-imagery h1 {{ color: white; }}
.hero-imagery p {{ color: color-mix(in srgb, white 80%, transparent); }}
.hero-imagery .tagline {{ background: rgba(255,255,255,.18); border-color: rgba(255,255,255,.3); color: white; }}
.hero-imagery .btn {{ background: white; color: var(--primary); box-shadow: 0 18px 40px -16px rgba(0,0,0,.35); }}

@media (max-width: 760px) {{
  .hero-split .hero-grid {{ grid-template-columns: 1fr; }}
  .hero-visual {{ max-width: 320px; margin: 0 auto; }}
}}

section {{ padding: 90px 0; }}
section h2 {{ font-size: clamp(1.8rem, 3.5vw, 2.4rem); margin-bottom: 14px; }}
section .lead {{ color: var(--muted); margin-bottom: 44px; max-width: 640px; font-size: 1.05rem; }}
.grid {{ display: grid; gap: 22px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px; transition: transform .2s, box-shadow .2s; }}
.card:hover {{ transform: translateY(-3px); box-shadow: var(--shadow); }}
.card-icon {{ font-size: 1.8rem; margin-bottom: 14px; }}
.card h3 {{ margin-bottom: 10px; color: var(--primary); font-size: 1.2rem; }}
.card p {{ color: var(--muted); }}
ul.why {{ list-style: none; display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
ul.why li {{ padding: 18px 18px 18px 56px; position: relative; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); }}
ul.why li:before {{ content: "✓"; position: absolute; left: 18px; top: 18px; width: 26px; height: 26px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; display: flex; align-items: center; justify-content: center; font-size: .8rem; font-weight: 700; }}
.contact {{ background: var(--card); }}
.contact-grid {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-top: 30px; }}
.contact-item {{ padding: 22px; background: var(--bg); border-radius: var(--radius); border: 1px solid var(--border); }}
.contact-item strong {{ display: block; color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }}
.contact-item a {{ font-weight: 600; }}
footer {{ padding: 36px 0; border-top: 1px solid var(--border); color: var(--muted); font-size: .9rem; text-align: center; }}
.claim-banner {{ background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; padding: 11px; text-align: center; font-size: .9rem; }}
.claim-banner a {{ color: white; text-decoration: underline; font-weight: 600; }}
</style>
</head>
<body>
<div class="claim-banner">
  {L['claim_q']} <a href="/claim/{_e(slug)}">{L['claim_cta']}</a>
</div>
<header>
  <div class="container row">
    <div class="brand"><span class="dot">{theme['badge_emoji']}</span>{_e(lead.get('name'))}</div>
    {rating_badge}
    <a class="btn" href="#contact">{_e(content.get('cta_text'))}</a>
  </div>
</header>

{hero_html}

<section id="about">
  <div class="container">
    <h2>{L['about']}</h2>
    <p class="lead">{_e(content.get('about'))}</p>
  </div>
</section>

<section id="services" style="background: var(--card);">
  <div class="container">
    <h2>{L['services']}</h2>
    <p class="lead">{L['services_lead']}</p>
    <div class="grid">{services_html}</div>
  </div>
</section>

<section id="why">
  <div class="container">
    <h2>{L['why']}</h2>
    <ul class="why">{why_html}</ul>
  </div>
</section>

<section id="contact" class="contact">
  <div class="container">
    <h2>{L['contact']}</h2>
    <p class="lead">{L['contact_lead']}</p>
    <div class="contact-grid">
      {f'<div class="contact-item"><strong>{L["phone"]}</strong><a href="tel:{_e(phone)}">{_e(phone)}</a></div>' if phone else ''}
      {f'<div class="contact-item"><strong>{L["address"]}</strong>{_e(address)}</div>' if address else ''}
      {f'<div class="contact-item"><strong>{L["maps"]}</strong><a href="{_e(maps_uri)}" target="_blank" rel="noopener">{L["directions"]}</a></div>' if maps_uri else ''}
    </div>
  </div>
</section>

<footer>
  <div class="container">
    © {_e(lead.get('name'))} · {L['footer_made']} <a href="/" style="color:var(--primary)">LocalLift</a>
  </div>
</footer>
</body>
</html>
"""

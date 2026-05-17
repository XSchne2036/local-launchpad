"""HTML-Renderer für generierte Webseiten. Reines String-Templating, keine Engine."""
from __future__ import annotations

import html
from typing import Any


def _e(s: Any) -> str:
    return html.escape(str(s or ""))


def render_site(lead: dict[str, Any], content: dict[str, Any], slug: str, base_url: str = "") -> str:
    primary = content.get("color_primary", "#1e40af")
    accent = content.get("color_accent", "#3b82f6")
    lang = content.get("language", "de")

    services_html = "\n".join(
        f"""<div class="card">
            <h3>{_e(s.get('title'))}</h3>
            <p>{_e(s.get('description'))}</p>
        </div>"""
        for s in content.get("services", [])
    )

    why_html = "\n".join(
        f"<li>{_e(w)}</li>" for w in content.get("why_choose_us", [])
    )

    phone = lead.get("phone")
    address = lead.get("address")
    maps_uri = lead.get("google_maps_uri")

    return f"""<!DOCTYPE html>
<html lang="{_e(lang)}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{_e(content.get('seo_title'))}</title>
<meta name="description" content="{_e(content.get('seo_description'))}" />
<meta property="og:title" content="{_e(content.get('seo_title'))}" />
<meta property="og:description" content="{_e(content.get('seo_description'))}" />
<style>
:root {{
  --primary: {primary};
  --accent: {accent};
  --bg: #ffffff;
  --fg: #0f172a;
  --muted: #64748b;
  --card: #f8fafc;
  --border: #e2e8f0;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: var(--bg); color: var(--fg); font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }}
a {{ color: var(--primary); text-decoration: none; }}
.container {{ max-width: 1100px; margin: 0 auto; padding: 0 24px; }}
header {{ padding: 20px 0; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(255,255,255,.92); backdrop-filter: blur(8px); z-index: 10; }}
header .row {{ display: flex; justify-content: space-between; align-items: center; }}
.brand {{ font-weight: 700; font-size: 1.1rem; color: var(--fg); }}
.brand span {{ color: var(--primary); }}
.btn {{ display: inline-block; background: var(--primary); color: white; padding: 12px 22px; border-radius: 10px; font-weight: 600; transition: transform .15s, box-shadow .15s; }}
.btn:hover {{ transform: translateY(-1px); box-shadow: 0 8px 20px -8px var(--primary); }}
.hero {{ padding: 90px 0 70px; background: linear-gradient(135deg, color-mix(in srgb, var(--primary) 12%, transparent), color-mix(in srgb, var(--accent) 8%, transparent)); text-align: center; }}
.hero h1 {{ font-size: clamp(2rem, 5vw, 3.4rem); line-height: 1.1; margin-bottom: 18px; letter-spacing: -.02em; }}
.hero p {{ font-size: 1.2rem; color: var(--muted); max-width: 640px; margin: 0 auto 32px; }}
.tagline {{ display: inline-block; padding: 6px 14px; border-radius: 999px; background: white; border: 1px solid var(--border); color: var(--primary); font-size: .85rem; font-weight: 600; margin-bottom: 20px; }}
section {{ padding: 80px 0; }}
section h2 {{ font-size: 2rem; margin-bottom: 12px; letter-spacing: -.02em; }}
section .lead {{ color: var(--muted); margin-bottom: 40px; max-width: 640px; }}
.grid {{ display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 24px; }}
.card h3 {{ margin-bottom: 10px; color: var(--primary); }}
.card p {{ color: var(--muted); }}
ul.why {{ list-style: none; display: grid; gap: 14px; }}
ul.why li {{ padding-left: 32px; position: relative; }}
ul.why li:before {{ content: "✓"; position: absolute; left: 0; top: 0; width: 22px; height: 22px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: .8rem; font-weight: 700; }}
.contact {{ background: var(--card); }}
.contact-grid {{ display: grid; gap: 24px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-top: 30px; }}
.contact-item {{ padding: 20px; background: white; border-radius: 12px; border: 1px solid var(--border); }}
.contact-item strong {{ display: block; color: var(--muted); font-size: .85rem; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }}
footer {{ padding: 30px 0; border-top: 1px solid var(--border); color: var(--muted); font-size: .9rem; text-align: center; }}
.claim-banner {{ background: var(--primary); color: white; padding: 10px; text-align: center; font-size: .9rem; }}
.claim-banner a {{ color: white; text-decoration: underline; font-weight: 600; }}
</style>
</head>
<body>
<div class="claim-banner">
  Ist das Ihr Unternehmen? <a href="/claim/{_e(slug)}">Jetzt kostenlos übernehmen →</a>
</div>
<header>
  <div class="container row">
    <div class="brand">{_e(lead.get('name'))}</div>
    <a class="btn" href="#contact">{_e(content.get('cta_text'))}</a>
  </div>
</header>

<div class="hero">
  <div class="container">
    <span class="tagline">{_e(content.get('tagline'))}</span>
    <h1>{_e(content.get('hero_title'))}</h1>
    <p>{_e(content.get('hero_subtitle'))}</p>
    <a class="btn" href="#contact">{_e(content.get('cta_text'))}</a>
  </div>
</div>

<section id="about">
  <div class="container">
    <h2>Über uns</h2>
    <p class="lead">{_e(content.get('about'))}</p>
  </div>
</section>

<section id="services" style="background: var(--card);">
  <div class="container">
    <h2>Leistungen</h2>
    <p class="lead">Was wir für Sie tun können.</p>
    <div class="grid">
      {services_html}
    </div>
  </div>
</section>

<section id="why">
  <div class="container">
    <h2>Warum wir</h2>
    <ul class="why">{why_html}</ul>
  </div>
</section>

<section id="contact" class="contact">
  <div class="container">
    <h2>Kontakt</h2>
    <p class="lead">Wir freuen uns auf Ihre Nachricht.</p>
    <div class="contact-grid">
      {f'<div class="contact-item"><strong>Telefon</strong><a href="tel:{_e(phone)}">{_e(phone)}</a></div>' if phone else ''}
      {f'<div class="contact-item"><strong>Adresse</strong>{_e(address)}</div>' if address else ''}
      {f'<div class="contact-item"><strong>Auf Google Maps</strong><a href="{_e(maps_uri)}" target="_blank" rel="noopener">Route ansehen</a></div>' if maps_uri else ''}
    </div>
  </div>
</section>

<footer>
  <div class="container">
    © {_e(lead.get('name'))} · Webseite erstellt mit <a href="/" style="color:var(--primary)">LocalLift</a>
  </div>
</footer>
</body>
</html>
"""

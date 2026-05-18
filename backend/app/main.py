"""FastAPI App. Start: uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 (im backend/ Ordner)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from pydantic import BaseModel, EmailStr

from . import ai, renderer, scraper, storage, themes, tunnels

app = FastAPI(title="LocalLift Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------- Scraper ----------------

@app.post("/scraper/run")
def run_scraper(
    query: str = Query(..., description="z.B. 'Friseur in Berlin Mitte'"),
    language: str = Query("de"),
    region: str | None = Query(None, description="ISO-Ländercode, z.B. 'DE', 'ID'"),
    max_pages: int = Query(3, ge=1, le=5),
    only_without_website: bool = Query(True),
):
    try:
        return scraper.find_leads(
            query,
            language=language,
            region=region,
            max_pages=max_pages,
            only_without_website=only_without_website,
        )
    except scraper.ScraperError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------- Leads ----------------

@app.get("/leads")
def list_leads(status: str | None = None) -> dict:
    items = storage.load("leads")
    if status:
        items = [i for i in items if i.get("status") == status]
    return {"count": len(items), "leads": items}


@app.get("/leads/{lead_id}")
def get_lead(lead_id: str) -> dict:
    for lead in storage.load("leads"):
        if lead.get("id") == lead_id:
            return lead
    raise HTTPException(status_code=404, detail="Lead nicht gefunden")


def _find_lead(lead_id: str) -> dict:
    for lead in storage.load("leads"):
        if lead.get("id") == lead_id:
            return lead
    raise HTTPException(status_code=404, detail="Lead nicht gefunden")


# ---------------- Site Generation ----------------

@app.post("/sites/generate/{lead_id}")
def generate_site(
    lead_id: str,
    language: str = Query("de"),
    force: bool = Query(False, description="Vorhandene Seite überschreiben"),
    theme: str | None = Query(None, description="Theme-Key überschreiben (z.B. 'restaurant'); leer = Auto-Detect"),
):
    """Generiert (oder regeneriert) eine Webseite für ein Lead per Lovable AI."""
    lead = _find_lead(lead_id)

    existing = next((s for s in storage.load("sites") if s.get("lead_id") == lead_id), None)
    if existing and not force:
        return {"status": "exists", "site": {k: v for k, v in existing.items() if k != "html"}}

    chosen_theme = themes.get_theme(theme) if theme else themes.detect_theme(lead)

    try:
        content = ai.generate_content(lead, language=language, theme=chosen_theme)
    except ai.AIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    slug = ai.slugify(lead.get("name") or lead_id) + "-" + lead_id[-6:].lower()
    html_doc = renderer.render_site(lead, content, slug, theme=chosen_theme)

    site = {
        "id": slug,
        "lead_id": lead_id,
        "slug": slug,
        "language": language,
        "theme": chosen_theme["key"],
        "theme_name": chosen_theme["name"],
        "content": content,
        "html": html_doc,
        "status": "generated",
        "claimed": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    saved = storage.upsert("sites", site)
    storage.upsert("leads", {**lead, "status": "site_generated", "site_slug": slug})
    return {"status": "ok", "site": {k: v for k, v in saved.items() if k != "html"}}


@app.get("/themes")
def list_themes_endpoint() -> dict:
    return {"themes": [
        {k: v for k, v in t.items() if k in ("key", "name", "tone", "primary", "accent", "hero_style", "badge_emoji")}
        for t in themes.list_themes()
    ]}


@app.post("/sites/generate-batch")
def generate_batch(
    limit: int = Query(5, ge=1, le=50),
    language: str = Query("de"),
):
    """Generiert Webseiten für die nächsten N Leads ohne Site."""
    leads = storage.load("leads")
    generated_slugs = {s.get("lead_id") for s in storage.load("sites")}
    todo = [l for l in leads if l.get("id") not in generated_slugs][:limit]

    results = []
    for lead in todo:
        try:
            r = generate_site(lead["id"], language=language, force=False)
            results.append({"lead_id": lead["id"], "status": "ok", "slug": r["site"]["slug"]})
        except HTTPException as e:
            results.append({"lead_id": lead["id"], "status": "error", "detail": e.detail})
    return {"processed": len(results), "results": results}


@app.get("/sites")
def list_sites() -> dict:
    sites = storage.load("sites")
    return {
        "count": len(sites),
        "sites": [{k: v for k, v in s.items() if k != "html"} for s in sites],
    }


@app.get("/sites/{slug}", response_class=HTMLResponse)
def view_site(slug: str) -> HTMLResponse:
    for s in storage.load("sites"):
        if s.get("slug") == slug:
            return HTMLResponse(content=s["html"])
    raise HTTPException(status_code=404, detail="Site nicht gefunden")


# ---------------- Tunnels (Cloudflare Quick Tunnel pro Site) ----------------

@app.post("/tunnels/start/{slug}")
def tunnel_start(slug: str) -> dict:
    site = next((s for s in storage.load("sites") if s.get("slug") == slug), None)
    if not site:
        raise HTTPException(404, "Site nicht gefunden")
    try:
        t = tunnels.start_tunnel(slug)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    storage.upsert("sites", {**site, "public_url": t["public_url"], "tunnel_host": t["tunnel_host"]})
    return t


@app.post("/tunnels/stop/{slug}")
def tunnel_stop(slug: str) -> dict:
    tunnels.stop_tunnel(slug)
    return {"status": "stopped", "slug": slug}


@app.get("/tunnels")
def tunnel_list() -> dict:
    items = tunnels.list_tunnels()
    return {"count": len(items), "tunnels": items, "cloudflared": tunnels.cloudflared_available()}


# ---------------- Claim System ----------------

class ClaimRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    message: str | None = None


@app.post("/claim/{slug}")
def claim_site(slug: str, payload: ClaimRequest) -> dict:
    site = next((s for s in storage.load("sites") if s.get("slug") == slug), None)
    if not site:
        raise HTTPException(404, "Site nicht gefunden")

    claim = {
        "id": f"{slug}-{int(datetime.now(timezone.utc).timestamp())}",
        "slug": slug,
        "lead_id": site["lead_id"],
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "message": payload.message,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    storage.upsert("claims", claim)
    storage.upsert("sites", {**site, "claim_status": "pending"})
    return {"status": "ok", "claim_id": claim["id"]}


@app.get("/claims")
def list_claims(status: str | None = None) -> dict:
    items = storage.load("claims")
    if status:
        items = [c for c in items if c.get("status") == status]
    return {"count": len(items), "claims": items}


@app.post("/claims/{claim_id}/approve")
def approve_claim(claim_id: str) -> dict:
    claims = storage.load("claims")
    claim = next((c for c in claims if c.get("id") == claim_id), None)
    if not claim:
        raise HTTPException(404, "Claim nicht gefunden")
    storage.upsert("claims", {**claim, "status": "approved",
                              "approved_at": datetime.now(timezone.utc).isoformat()})
    site = next((s for s in storage.load("sites") if s.get("slug") == claim["slug"]), None)
    if site:
        storage.upsert("sites", {**site, "claimed": True, "claim_status": "approved",
                                 "owner_email": claim["email"]})
    return {"status": "approved"}


# ---------------- Claim-Formular (HTML) ----------------

@app.get("/claim/{slug}", response_class=HTMLResponse)
def claim_form(slug: str) -> HTMLResponse:
    site = next((s for s in storage.load("sites") if s.get("slug") == slug), None)
    if not site:
        raise HTTPException(404, "Site nicht gefunden")
    name = site["content"].get("hero_title", slug)
    return HTMLResponse(f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<title>Webseite übernehmen – {name}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{font:16px/1.6 system-ui;max-width:560px;margin:40px auto;padding:0 20px;color:#0f172a}}
h1{{font-size:1.6rem;margin-bottom:8px}} p.lead{{color:#64748b;margin-bottom:24px}}
label{{display:block;font-weight:600;margin:14px 0 6px}}
input,textarea{{width:100%;padding:12px;border:1px solid #e2e8f0;border-radius:10px;font:inherit}}
button{{margin-top:20px;background:#1e40af;color:#fff;border:0;padding:14px 22px;border-radius:10px;font-weight:600;cursor:pointer;width:100%}}
.ok{{background:#dcfce7;color:#166534;padding:14px;border-radius:10px;margin-top:20px}}
</style></head><body>
<h1>Diese Webseite übernehmen</h1>
<p class="lead">Bestätige, dass du Inhaber:in von <b>{name}</b> bist – wir übergeben dir die Seite kostenlos.</p>
<form id="f">
<label>Name</label><input name="name" required>
<label>E-Mail</label><input name="email" type="email" required>
<label>Telefon</label><input name="phone">
<label>Nachricht (optional)</label><textarea name="message" rows="3"></textarea>
<button>Anfrage senden</button>
</form>
<div id="r"></div>
<script>
document.getElementById('f').addEventListener('submit', async e => {{
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd.entries());
  const r = await fetch('/claim/{slug}', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(body)}});
  const j = await r.json();
  document.getElementById('r').innerHTML = r.ok
    ? '<div class="ok">Danke! Wir melden uns innerhalb von 24h per E-Mail.</div>'
    : '<div class="ok" style="background:#fee2e2;color:#991b1b">Fehler: '+(j.detail||'')+'</div>';
  if(r.ok) e.target.style.display='none';
}});
</script></body></html>""")


# ---------------- Admin Dashboard ----------------

@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    sites = storage.load("sites")
    leads = storage.load("leads")
    claims = storage.load("claims")
    tun = {t["slug"]: t for t in tunnels.list_tunnels()}

    rows = ""
    for s in sites:
        t = tun.get(s["slug"])
        pub = f'<a href="{t["public_url"]}" target="_blank">{t["tunnel_host"]}</a>' if t and t["status"] == "running" else '<span style="color:#94a3b8">–</span>'
        action = (
            f'<button onclick="stop(\'{s["slug"]}\')">Stop</button>'
            if t and t["status"] == "running"
            else f'<button onclick="start(\'{s["slug"]}\')">Tunnel starten</button>'
        )
        claimed = "✅" if s.get("claimed") else ("⏳" if s.get("claim_status") == "pending" else "—")
        rows += f"""<tr>
          <td><a href="/sites/{s['slug']}" target="_blank">{s['content'].get('hero_title', s['slug'])}</a><br><small>{s['slug']}</small></td>
          <td>{s.get('language','')}</td>
          <td>{claimed}</td>
          <td>{pub}</td>
          <td>{action}</td>
        </tr>"""

    return HTMLResponse(f"""<!doctype html><html><head><meta charset="utf-8"><title>LocalLift Admin</title>
<style>body{{font:15px system-ui;max-width:1100px;margin:30px auto;padding:0 20px;color:#0f172a}}
h1{{margin-bottom:4px}} .stats{{display:flex;gap:20px;margin:20px 0;color:#64748b}}
.stats div b{{display:block;font-size:1.8rem;color:#1e40af}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th,td{{text-align:left;padding:12px;border-bottom:1px solid #e2e8f0;vertical-align:top}}
th{{background:#f8fafc;font-size:.85rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b}}
button{{background:#1e40af;color:#fff;border:0;padding:8px 14px;border-radius:8px;cursor:pointer;font-weight:600}}
a{{color:#1e40af}}
.warn{{background:#fef3c7;color:#92400e;padding:12px;border-radius:10px;margin:12px 0}}
</style></head><body>
<h1>LocalLift – Admin</h1>
<div class="stats">
  <div><b>{len(leads)}</b>Leads</div>
  <div><b>{len(sites)}</b>Generierte Seiten</div>
  <div><b>{sum(1 for t in tun.values() if t['status']=='running')}</b>Aktive Tunnels</div>
  <div><b>{len(claims)}</b>Claim-Anfragen</div>
</div>
{'' if tunnels.cloudflared_available() else '<div class="warn">⚠️ <b>cloudflared</b> ist nicht installiert – Tunnels deaktiviert. <a href="https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/" target="_blank">Installieren</a></div>'}
<table><thead><tr><th>Site</th><th>Sprache</th><th>Claim</th><th>Public URL</th><th>Aktion</th></tr></thead>
<tbody>{rows or '<tr><td colspan=5 style="text-align:center;color:#94a3b8;padding:40px">Noch keine Seiten. Starte über <a href="/docs">/docs</a>.</td></tr>'}</tbody></table>
<p style="margin-top:30px"><a href="/docs">→ API Docs</a> · <a href="/claims">→ Claims JSON</a></p>
<script>
async function start(slug){{ const r=await fetch('/tunnels/start/'+slug,{{method:'POST'}}); if(!r.ok){{alert((await r.json()).detail)}} else location.reload(); }}
async function stop(slug){{ await fetch('/tunnels/stop/'+slug,{{method:'POST'}}); location.reload(); }}
</script>
</body></html>""")

"""FastAPI App. Start: uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 (im backend/ Ordner)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from pydantic import BaseModel, EmailStr

from fastapi import Request

from . import ai, i18n, outreach, renderer, scraper, storage, themes, tunnels, versions

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
    language: str = Query("auto", description="'auto' = aus Region erkennen; sonst de/en/id"),
    force: bool = Query(False, description="Vorhandene Seite überschreiben"),
    theme: str | None = Query(None, description="Theme-Key überschreiben (z.B. 'restaurant'); leer = Auto-Detect"),
):
    """Generiert (oder regeneriert) eine Webseite für ein Lead per Lovable AI."""
    lead = _find_lead(lead_id)

    existing = next((s for s in storage.load("sites") if s.get("lead_id") == lead_id), None)
    if existing and not force:
        return {"status": "exists", "site": {k: v for k, v in existing.items() if k not in ("html", "translations_html")}}
    if existing and force:
        versions.snapshot_site(existing, reason="regenerate")

    chosen_theme = themes.get_theme(theme) if theme else themes.detect_theme(lead)
    resolved_lang = i18n.detect_language(lead) if language == "auto" else language
    if resolved_lang not in i18n.SUPPORTED_LANGUAGES:
        resolved_lang = i18n.DEFAULT_LANGUAGE

    try:
        content = ai.generate_content(lead, language=resolved_lang, theme=chosen_theme)
    except ai.AIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    slug = ai.slugify(lead.get("name") or lead_id) + "-" + lead_id[-6:].lower()
    html_doc = renderer.render_site(lead, content, slug, theme=chosen_theme)

    site = {
        "id": slug,
        "lead_id": lead_id,
        "slug": slug,
        "language": resolved_lang,
        "language_source": "auto" if language == "auto" else "manual",
        "detected_region": i18n.detect_region(lead),
        "theme": chosen_theme["key"],
        "theme_name": chosen_theme["name"],
        "content": content,
        "html": html_doc,
        "translations": {},          # {lang: content}
        "translations_html": {},     # {lang: html}
        "status": "generated",
        "claimed": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    saved = storage.upsert("sites", site)
    storage.upsert("leads", {**lead, "status": "site_generated", "site_slug": slug})
    return {"status": "ok", "site": {k: v for k, v in saved.items() if k not in ("html", "translations_html")}}


@app.post("/sites/{slug}/translate")
def translate_site(
    slug: str,
    languages: str = Query("en,id", description="Komma-getrennte Zielsprachen (de,en,id)"),
):
    """Batch-Übersetzt eine bereits generierte Seite in N Zielsprachen und rendert sie."""
    site = next((s for s in storage.load("sites") if s.get("slug") == slug), None)
    if not site:
        raise HTTPException(404, "Site nicht gefunden")

    targets = [l.strip() for l in languages.split(",") if l.strip()]
    targets = [l for l in targets if l in i18n.SUPPORTED_LANGUAGES and l != site.get("language")]
    if not targets:
        return {"status": "noop", "reason": "Keine gültigen Zielsprachen (oder identisch mit Quelle)"}

    lead = _find_lead(site["lead_id"])
    theme_obj = themes.get_theme(site.get("theme", "default"))

    try:
        translations = i18n.translate_batch(site["content"], targets)
    except ai.AIError as e:
        raise HTTPException(502, str(e))

    existing_tr = site.get("translations") or {}
    existing_html = site.get("translations_html") or {}
    for lang, content in translations.items():
        existing_tr[lang] = content
        existing_html[lang] = renderer.render_site(lead, content, slug, theme=theme_obj)

    updated = storage.upsert("sites", {
        **site,
        "translations": existing_tr,
        "translations_html": existing_html,
    })
    return {
        "status": "ok",
        "slug": slug,
        "added": list(translations.keys()),
        "available_languages": [updated["language"]] + list(existing_tr.keys()),
    }


@app.get("/themes")
def list_themes_endpoint() -> dict:
    return {"themes": [
        {k: v for k, v in t.items() if k in ("key", "name", "tone", "primary", "accent", "hero_style", "badge_emoji")}
        for t in themes.list_themes()
    ]}


@app.post("/sites/generate-batch")
def generate_batch(
    limit: int = Query(5, ge=1, le=50),
    language: str = Query("auto", description="'auto' = pro Lead aus Region erkennen"),
    translate_to: str | None = Query(None, description="Komma-getrennt: nach Generierung in diese Sprachen übersetzen"),
):
    """Generiert Webseiten für die nächsten N Leads ohne Site. Optional: Auto-Übersetzungen."""
    leads = storage.load("leads")
    generated_slugs = {s.get("lead_id") for s in storage.load("sites")}
    todo = [l for l in leads if l.get("id") not in generated_slugs][:limit]

    results = []
    for lead in todo:
        try:
            r = generate_site(lead["id"], language=language, force=False)
            slug = r["site"]["slug"]
            row = {"lead_id": lead["id"], "status": "ok", "slug": slug, "language": r["site"].get("language")}
            if translate_to:
                try:
                    tr = translate_site(slug, languages=translate_to)
                    row["translated"] = tr.get("added", [])
                except HTTPException as te:
                    row["translation_error"] = te.detail
            results.append(row)
        except HTTPException as e:
            results.append({"lead_id": lead["id"], "status": "error", "detail": e.detail})
    return {"processed": len(results), "results": results}


@app.get("/sites")
def list_sites() -> dict:
    sites = storage.load("sites")
    public_fields = lambda s: {k: v for k, v in s.items() if k not in ("html", "translations_html")}
    return {
        "count": len(sites),
        "sites": [
            {
                **public_fields(s),
                "available_languages": [s.get("language")] + list((s.get("translations") or {}).keys()),
            }
            for s in sites
        ],
    }


@app.get("/sites/{slug}", response_class=HTMLResponse)
def view_site(slug: str, lang: str | None = Query(None, description="Optional: en/id/de für Übersetzung")) -> HTMLResponse:
    for s in storage.load("sites"):
        if s.get("slug") == slug:
            if lang and lang != s.get("language"):
                tr_html = (s.get("translations_html") or {}).get(lang)
                if tr_html:
                    return HTMLResponse(content=tr_html)
                raise HTTPException(404, f"Übersetzung '{lang}' nicht vorhanden. Erst /sites/{slug}/translate?languages={lang} aufrufen.")
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




# ---------------- Versions / Diff ----------------

def _build_site_url(request: Request, slug: str) -> str:
    site = next((s for s in storage.load("sites") if s.get("slug") == slug), None)
    if site and site.get("public_url"):
        return site["public_url"]
    base = str(request.base_url).rstrip("/")
    return f"{base}/sites/{slug}"


@app.get("/sites/{slug}/versions")
def site_versions(slug: str) -> dict:
    items = versions.list_versions(slug)
    return {"count": len(items), "versions": [
        {k: v for k, v in it.items() if k not in ("html", "content")} for it in items
    ]}


@app.get("/sites/{slug}/diff", response_class=HTMLResponse)
def site_diff(slug: str, version_id: str | None = None) -> HTMLResponse:
    site = next((s for s in storage.load("sites") if s.get("slug") == slug), None)
    if not site:
        raise HTTPException(404, "Site nicht gefunden")
    vlist = versions.list_versions(slug)
    if not vlist:
        return HTMLResponse('<div style="padding:30px;font:14px system-ui;color:#64748b">Keine früheren Versionen – Diff verfügbar nach erstmaligem „Neu generieren".</div>')
    old = versions.get_version(version_id) if version_id else vlist[0]
    if not old:
        raise HTTPException(404, "Version nicht gefunden")
    diff_text = versions.diff_content(old.get("content") or {}, site.get("content") or {})
    diff_body = versions.diff_html(diff_text)
    options = "".join(
        f'<option value="{v["id"]}"{" selected" if v["id"]==old["id"] else ""}>{v["created_at"][:19].replace("T"," ")} ({v.get("reason","")})</option>'
        for v in vlist
    )
    return HTMLResponse(f"""<!doctype html><html><head><meta charset="utf-8"><title>Diff – {slug}</title>
<style>body{{font:14px ui-monospace,Menlo,monospace;background:#0f172a;color:#e2e8f0;margin:0;padding:20px}}
h2{{font-family:system-ui;color:#fff;margin:0 0 14px}} .bar{{font-family:system-ui;margin-bottom:16px;display:flex;gap:10px;align-items:center}}
select{{padding:6px 10px;background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:6px}}
pre{{background:#1e293b;padding:18px;border-radius:10px;overflow:auto;line-height:1.5;white-space:pre}}
.diff-add{{color:#86efac;display:block}} .diff-del{{color:#fca5a5;display:block}}
.diff-meta{{color:#fbbf24;display:block;font-weight:700}} .diff-hunk{{color:#7dd3fc;display:block;margin-top:8px}}
.diff-ctx{{color:#94a3b8;display:block}}
</style></head><body>
<h2>📝 Diff: alte Version → aktuell ({slug})</h2>
<div class="bar"><label>Vergleichs-Version:</label>
<select onchange="location.href='/sites/{slug}/diff?version_id='+this.value">{options}</select>
<a href="/sites/{slug}" target="_blank" style="color:#7dd3fc">→ aktuelle Seite</a></div>
<pre>{diff_body}</pre></body></html>""")


@app.get("/sites/{slug}/preview", response_class=HTMLResponse)
def site_preview(slug: str, lang: str | None = None) -> HTMLResponse:
    """Live-Preview im Admin: iframe mit Sprach-Switcher, ohne Claim-Banner-Bypass."""
    site = next((s for s in storage.load("sites") if s.get("slug") == slug), None)
    if not site:
        raise HTTPException(404, "Site nicht gefunden")
    all_langs = [site.get("language")] + list((site.get("translations") or {}).keys())
    all_langs = [l for l in all_langs if l]
    current = lang or site.get("language")
    src = f"/sites/{slug}" + (f"?lang={current}" if current != site.get("language") else "")
    lang_btns = "".join(
        f'<a href="/sites/{slug}/preview?lang={l}" class="{"active" if l==current else ""}">{l}</a>'
        for l in all_langs
    )
    return HTMLResponse(f"""<!doctype html><html><head><meta charset="utf-8"><title>Preview – {slug}</title>
<style>body,html{{margin:0;height:100%;font:14px system-ui;background:#0f172a;color:#e2e8f0}}
.bar{{display:flex;gap:10px;align-items:center;padding:10px 16px;background:#1e293b;border-bottom:1px solid #334155}}
.bar a{{color:#cbd5e1;padding:4px 10px;border-radius:6px;text-decoration:none;border:1px solid #334155}}
.bar a.active{{background:#1e40af;color:#fff;border-color:#1e40af}}
.bar .spacer{{flex:1}} iframe{{display:block;width:100%;height:calc(100vh - 49px);border:0;background:#fff}}
.dev{{display:inline-flex;gap:6px;margin-left:8px}} .dev button{{background:#334155;color:#fff;border:0;padding:4px 10px;border-radius:6px;cursor:pointer}}
</style></head><body>
<div class="bar">
  <b>👁 {slug}</b>
  <span>{lang_btns}</span>
  <div class="dev">
    <button onclick="vp('375px')">📱</button>
    <button onclick="vp('768px')">📲</button>
    <button onclick="vp('100%')">🖥</button>
  </div>
  <div class="spacer"></div>
  <a href="/sites/{slug}/diff" target="_blank">📝 Diff</a>
  <a href="{src}" target="_blank">↗ Vollbild</a>
</div>
<div style="display:flex;justify-content:center;background:#0f172a"><iframe id="f" src="{src}" style="max-width:100%"></iframe></div>
<script>function vp(w){{document.getElementById('f').style.maxWidth=w}}</script>
</body></html>""")


# ---------------- Outreach (SMTP) ----------------

class OutreachPayload(BaseModel):
    to: EmailStr | None = None
    language: str | None = None  # auto = aus site/language
    custom_subject: str | None = None
    custom_body: str | None = None


@app.get("/outreach/config")
def outreach_config() -> dict:
    cfg = outreach.smtp_config()
    return {k: v for k, v in cfg.items() if k != "password"}


@app.get("/outreach")
def outreach_list() -> dict:
    items = sorted(storage.load("outreach"), key=lambda x: x.get("sent_at", ""), reverse=True)
    return {"count": len(items), "outreach": items}


@app.post("/outreach/send/{lead_id}")
def outreach_send(lead_id: str, payload: OutreachPayload, request: Request) -> dict:
    lead = _find_lead(lead_id)
    site = next((s for s in storage.load("sites") if s.get("lead_id") == lead_id), None)
    if not site:
        raise HTTPException(400, "Lead hat keine generierte Seite – erst /sites/generate/{lead_id} aufrufen.")

    to_email = (payload.to or lead.get("email") or "").strip()
    if not to_email:
        raise HTTPException(400, "Keine E-Mail-Adresse vorhanden. Bitte 'to' angeben.")

    cfg = outreach.smtp_config()
    if not cfg["configured"]:
        raise HTTPException(503, "SMTP nicht konfiguriert. Siehe /outreach/config.")

    lang = payload.language or site.get("language") or "de"
    site_url = _build_site_url(request, site["slug"])
    subject, body = outreach.render_template(lang, lead, site_url, cfg["from_name"])
    if payload.custom_subject:
        subject = payload.custom_subject
    if payload.custom_body:
        body = payload.custom_body

    try:
        result = outreach.send_email(to_email, subject, body, cfg=cfg)
    except outreach.OutreachError as e:
        outreach.log_outreach({"lead_id": lead_id, "slug": site["slug"], "to": to_email,
                               "subject": subject, "language": lang, "status": "error", "error": str(e)})
        raise HTTPException(502, str(e))

    log = outreach.log_outreach({
        "lead_id": lead_id, "slug": site["slug"], "to": to_email, "subject": subject,
        "language": lang, "status": "sent", "message_id": result["message_id"],
        "site_url": site_url,
    })
    storage.upsert("leads", {**lead, "status": "contacted", "last_outreach_at": log["sent_at"]})
    return {"status": "ok", "outreach": log}


@app.post("/outreach/send-batch")
def outreach_batch(request: Request, limit: int = Query(10, ge=1, le=50)) -> dict:
    sites = storage.load("sites")
    leads_by_id = {l["id"]: l for l in storage.load("leads")}
    already = {o["lead_id"] for o in storage.load("outreach") if o.get("status") == "sent"}
    results = []
    for site in sites:
        if len(results) >= limit:
            break
        lid = site.get("lead_id")
        if lid in already:
            continue
        lead = leads_by_id.get(lid)
        if not lead or not lead.get("email"):
            continue
        try:
            r = outreach_send(lid, OutreachPayload(), request)
            results.append({"lead_id": lid, "status": "ok", "to": r["outreach"]["to"]})
        except HTTPException as e:
            results.append({"lead_id": lid, "status": "error", "detail": e.detail})
    return {"processed": len(results), "results": results}


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
    out_log = storage.load("outreach")
    tun = {t["slug"]: t for t in tunnels.list_tunnels()}
    sites_by_lead = {s.get("lead_id"): s for s in sites}
    outreach_by_lead = {o.get("lead_id"): o for o in sorted(out_log, key=lambda x: x.get("sent_at",""))}
    smtp_cfg = outreach.smtp_config()
    versions_count = {slug: 0 for slug in (s["slug"] for s in sites)}
    for v in storage.load("site_versions"):
        if v.get("slug") in versions_count:
            versions_count[v["slug"]] += 1

    site_rows = ""
    for s in sites:
        t = tun.get(s["slug"])
        pub = f'<a href="{t["public_url"]}" target="_blank">{t["tunnel_host"]}</a>' if t and t["status"] == "running" else '<span style="color:#94a3b8">–</span>'
        action = (
            f'<button onclick="stop(\'{s["slug"]}\')">Stop</button>'
            if t and t["status"] == "running"
            else f'<button onclick="start(\'{s["slug"]}\')">Tunnel starten</button>'
        )
        claimed = "✅" if s.get("claimed") else ("⏳" if s.get("claim_status") == "pending" else "—")
        theme_key = s.get("theme", "default")
        theme_obj = themes.get_theme(theme_key)
        theme_cell = f'<span style="display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;background:{theme_obj["card"]};color:{theme_obj["primary"]};font-weight:600;font-size:.8rem;border:1px solid {theme_obj["border"]}">{theme_obj["badge_emoji"]} {theme_obj["name"]}</span>'
        translations = s.get("translations") or {}
        all_langs = [s.get("language")] + list(translations.keys())
        lang_links = " · ".join(
            f'<a href="/sites/{s["slug"]}{"?lang="+lg if lg != s.get("language") else ""}" target="_blank">{lg}{"★" if lg == s.get("language") else ""}</a>'
            for lg in all_langs if lg
        )
        missing = [lg for lg in ("de", "en", "id") if lg not in all_langs]
        tr_btn = (
            f'<button class="ghost" onclick="translate(\'{s["slug"]}\', \'{",".join(missing)}\')">+ {", ".join(missing)}</button>'
            if missing else '<span style="color:#94a3b8;font-size:.8rem">alle</span>'
        )
        src_note = '<span title="Auto erkannt" style="color:#15803d">🌐</span> ' if s.get("language_source") == "auto" else ""
        vcount = versions_count.get(s["slug"], 0)
        diff_btn = (f'<a href="/sites/{s["slug"]}/diff" target="_blank" class="pill">📝 Diff ({vcount})</a>'
                    if vcount else '<span style="color:#94a3b8;font-size:.78rem">v1</span>')
        preview_btn = f'<a href="/sites/{s["slug"]}/preview" target="_blank" class="pill">👁 Preview</a>'
        site_rows += f"""<tr>
          <td><a href="/sites/{s['slug']}" target="_blank">{s['content'].get('hero_title', s['slug'])}</a><br><small>{s['slug']}</small><br>{preview_btn} {diff_btn}</td>
          <td>{theme_cell}</td>
          <td>{src_note}{lang_links}<br>{tr_btn}</td>
          <td>{claimed}</td>
          <td>{pub}</td>
          <td>{action}</td>
        </tr>"""

    # Lead-Tabelle (neueste zuerst, max 30)
    leads_sorted = sorted(leads, key=lambda l: l.get("discovered_at", ""), reverse=True)[:30]
    lead_rows = ""
    for l in leads_sorted:
        has_site = l["id"] in sites_by_lead
        if has_site:
            site = sites_by_lead[l["id"]]
            site_cell = f'<a href="/sites/{site["slug"]}/preview" target="_blank">👁 Preview</a>'
            gen_btn = f'<button class="ghost" onclick="gen(\'{l["id"]}\', true)">Neu generieren</button>'
        else:
            site_cell = '<span style="color:#94a3b8">–</span>'
            gen_btn = f'<button onclick="gen(\'{l["id"]}\', false)">Seite generieren</button>'
        phone = l.get("phone") or "<span style='color:#94a3b8'>–</span>"
        rating = f'⭐ {l["rating"]} ({l.get("rating_count",0)})' if l.get("rating") else "–"
        email_val = l.get("email") or ""
        last_out = outreach_by_lead.get(l["id"])
        out_status = (f'<span style="color:#15803d">📧 {last_out["sent_at"][:10]}</span>'
                      if last_out and last_out.get("status") == "sent"
                      else ('<span style="color:#b91c1c">⚠ Fehler</span>' if last_out else '<span style="color:#94a3b8">–</span>'))
        if has_site and smtp_cfg["configured"]:
            mail_btn = f'<button class="ghost" onclick="mail(\'{l["id"]}\', \'{email_val}\')">✉ Mail</button>'
        elif has_site:
            mail_btn = '<span style="color:#94a3b8;font-size:.78rem" title="SMTP konfigurieren">SMTP fehlt</span>'
        else:
            mail_btn = '<span style="color:#94a3b8;font-size:.78rem">erst generieren</span>'
        lead_rows += f"""<tr>
          <td><b>{l.get('name','')}</b><br><small style="color:#64748b">{l.get('address','') or ''}</small>{'<br><small style=\"color:#1e40af\">'+email_val+'</small>' if email_val else ''}</td>
          <td><small>{l.get('primary_type','') or ''}</small></td>
          <td>{phone}</td>
          <td>{rating}</td>
          <td>{site_cell}<br>{out_status}</td>
          <td>{gen_btn} {mail_btn}</td>
        </tr>"""

    return HTMLResponse(f"""<!doctype html><html><head><meta charset="utf-8"><title>LocalLift Admin</title>
<style>body{{font:15px system-ui;max-width:1180px;margin:30px auto;padding:0 20px;color:#0f172a}}
h1{{margin-bottom:4px}} h2{{margin-top:40px;font-size:1.2rem;color:#1e293b}}
.stats{{display:flex;gap:20px;margin:20px 0;color:#64748b}}
.stats div b{{display:block;font-size:1.8rem;color:#1e40af}}
table{{width:100%;border-collapse:collapse;margin-top:12px}}
th,td{{text-align:left;padding:10px;border-bottom:1px solid #e2e8f0;vertical-align:top;font-size:.92rem}}
th{{background:#f8fafc;font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b}}
button{{background:#1e40af;color:#fff;border:0;padding:7px 12px;border-radius:8px;cursor:pointer;font-weight:600;font-size:.85rem}}
button.ghost{{background:#f1f5f9;color:#1e40af}}
button:disabled{{opacity:.5;cursor:wait}}
a{{color:#1e40af}}
.warn{{background:#fef3c7;color:#92400e;padding:12px;border-radius:10px;margin:12px 0}}
.card{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:18px;margin-top:14px}}
.row{{display:flex;gap:10px;flex-wrap:wrap;align-items:end}}
.row label{{display:flex;flex-direction:column;font-size:.78rem;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.04em;gap:4px}}
.row input,.row select{{padding:9px 12px;border:1px solid #cbd5e1;border-radius:8px;font:inherit;background:#fff;min-width:120px}}
.row input.wide{{min-width:340px}}
#status{{margin-top:10px;font-size:.9rem;color:#64748b;min-height:20px}}
#status.err{{color:#b91c1c}} #status.ok{{color:#15803d}}
.pill{{display:inline-block;padding:2px 8px;border-radius:999px;background:#eef2ff;color:#1e40af;font-size:.75rem;font-weight:600;text-decoration:none;margin-right:4px}}
.pill:hover{{background:#e0e7ff}}
</style></head><body>
<h1>LocalLift – Admin</h1>
<div class="stats">
  <div><b>{len(leads)}</b>Leads</div>
  <div><b>{len(sites)}</b>Generierte Seiten</div>
  <div><b>{sum(1 for o in out_log if o.get('status')=='sent')}</b>E-Mails gesendet</div>
  <div><b>{sum(1 for t in tun.values() if t['status']=='running')}</b>Aktive Tunnels</div>
  <div><b>{len(claims)}</b>Claim-Anfragen</div>
</div>
{'' if tunnels.cloudflared_available() else '<div class="warn">⚠️ <b>cloudflared</b> ist nicht installiert – Tunnels deaktiviert. <a href="https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/" target="_blank">Installieren</a></div>'}
{'' if smtp_cfg['configured'] else '<div class="warn">✉️ <b>SMTP nicht konfiguriert</b> – Outreach deaktiviert. Setze <code>SMTP_HOST</code>, <code>SMTP_FROM</code>, <code>SMTP_USER</code>, <code>SMTP_PASS</code> (optional <code>SMTP_PORT</code>, <code>SMTP_SECURE=starttls|ssl|none</code>, <code>SMTP_FROM_NAME</code>) in <code>backend/.env</code>.</div>' if not smtp_cfg['configured'] else f'<div style="background:#dcfce7;color:#166534;padding:10px 14px;border-radius:10px;margin:12px 0;font-size:.9rem">✉️ SMTP bereit · {smtp_cfg["host"]}:{smtp_cfg["port"]} · Absender <b>{smtp_cfg["from_email"]}</b></div>'}

<h2>🔎 Scraper – Leads finden</h2>
<div class="card">
  <div class="row">
    <label>Suchbegriff<input id="q" class="wide" placeholder="z.B. Friseur in Berlin Mitte" value=""></label>
    <label>Sprache (Quelle)
      <select id="lang">
        <option value="auto">🌐 Auto (aus Region)</option>
        <option value="de">Deutsch</option>
        <option value="en">English</option>
        <option value="id">Bahasa Indonesia</option>
      </select>
    </label>
    <label>Region
      <select id="region">
        <option value="">Auto</option>
        <option value="DE">DE</option>
        <option value="AT">AT</option>
        <option value="CH">CH</option>
        <option value="ID">ID</option>
        <option value="US">US</option>
      </select>
    </label>
    <label>Seiten<input id="pages" type="number" min="1" max="5" value="2" style="min-width:70px"></label>
    <label style="flex-direction:row;align-items:center;gap:6px;text-transform:none;font-size:.9rem;font-weight:500">
      <input id="noweb" type="checkbox" checked style="min-width:auto"> nur ohne Website
    </label>
    <label style="flex-direction:row;align-items:center;gap:6px;text-transform:none;font-size:.9rem;font-weight:500">
      <input id="autoTr" type="checkbox" style="min-width:auto"> Batch: auch übersetzen (en,id)
    </label>
    <button id="runBtn" onclick="runScraper()">Scrapen</button>
    <button class="ghost" onclick="batchGen()">Batch: 5 Seiten generieren</button>
    <button class="ghost" onclick="batchMail()">📧 Batch-Outreach (10)</button>
  </div>
  <div id="status"></div>
</div>

<h2>📋 Letzte Leads ({len(leads_sorted)} von {len(leads)})</h2>
<table><thead><tr><th>Unternehmen</th><th>Branche</th><th>Telefon</th><th>Bewertung</th><th>Site</th><th>Aktion</th></tr></thead>
<tbody>{lead_rows or '<tr><td colspan=6 style="text-align:center;color:#94a3b8;padding:30px">Noch keine Leads. Scraper oben starten.</td></tr>'}</tbody></table>

<h2>🌐 Generierte Sites</h2>
<table><thead><tr><th>Site</th><th>Theme</th><th>Sprachen</th><th>Claim</th><th>Public URL</th><th>Aktion</th></tr></thead>
<tbody>{site_rows or '<tr><td colspan=6 style="text-align:center;color:#94a3b8;padding:30px">Noch keine Seiten generiert.</td></tr>'}</tbody></table>

<p style="margin-top:30px;color:#64748b;font-size:.9rem">
  <a href="/docs">→ API Docs</a> · <a href="/themes">→ Themes JSON</a> · <a href="/leads">→ Leads JSON</a> · <a href="/claims">→ Claims JSON</a>
</p>

<script>
const s = document.getElementById('status');
function setStatus(msg, cls){{ s.className = cls||''; s.textContent = msg; }}

async function runScraper(){{
  const q = document.getElementById('q').value.trim();
  if(!q){{ setStatus('Bitte Suchbegriff eingeben.', 'err'); return; }}
  const params = new URLSearchParams({{
    query: q,
    language: document.getElementById('lang').value,
    max_pages: document.getElementById('pages').value,
    only_without_website: document.getElementById('noweb').checked,
  }});
  const region = document.getElementById('region').value;
  if(region) params.append('region', region);
  const btn = document.getElementById('runBtn');
  btn.disabled = true; setStatus('Suche läuft…');
  try {{
    const r = await fetch('/scraper/run?'+params, {{method:'POST'}});
    const j = await r.json();
    if(!r.ok) throw new Error(j.detail || 'Fehler');
    setStatus(`✅ ${{j.total_found}} gefunden · ${{j.leads_without_website}} ohne Website hinzugefügt`, 'ok');
    setTimeout(()=>location.reload(), 1200);
  }} catch(e){{ setStatus('❌ '+e.message, 'err'); btn.disabled = false; }}
}}

async function gen(leadId, force){{
  const lang = document.getElementById('lang').value;
  setStatus('Generiere Seite per AI ('+lang+')…');
  const r = await fetch(`/sites/generate/${{leadId}}?force=${{force}}&language=${{lang}}`, {{method:'POST'}});
  const j = await r.json();
  if(!r.ok){{ setStatus('❌ '+(j.detail||'Fehler'), 'err'); return; }}
  setStatus('✅ Seite generiert ('+(j.site.language||'?')+'): '+j.site.slug, 'ok');
  setTimeout(()=>location.reload(), 800);
}}

async function batchGen(){{
  const lang = document.getElementById('lang').value;
  const tr = document.getElementById('autoTr').checked ? '&translate_to=en,id' : '';
  setStatus('Batch-Generierung läuft (kann dauern)…');
  const r = await fetch('/sites/generate-batch?limit=5&language='+lang+tr, {{method:'POST'}});
  const j = await r.json();
  if(!r.ok){{ setStatus('❌ Fehler', 'err'); return; }}
  const ok = j.results.filter(x=>x.status==='ok').length;
  setStatus(`✅ ${{ok}}/${{j.processed}} Seiten generiert`, 'ok');
  setTimeout(()=>location.reload(), 1200);
}}

async function translate(slug, langs){{
  setStatus('Übersetze '+slug+' → '+langs+'…');
  const r = await fetch(`/sites/${{slug}}/translate?languages=${{langs}}`, {{method:'POST'}});
  const j = await r.json();
  if(!r.ok){{ setStatus('❌ '+(j.detail||'Fehler'), 'err'); return; }}
  setStatus('✅ Übersetzt: '+(j.added||[]).join(', '), 'ok');
  setTimeout(()=>location.reload(), 800);
}}

async function start(slug){{ const r=await fetch('/tunnels/start/'+slug,{{method:'POST'}}); if(!r.ok){{setStatus('❌ '+(await r.json()).detail,'err')}} else location.reload(); }}
async function stop(slug){{ await fetch('/tunnels/stop/'+slug,{{method:'POST'}}); location.reload(); }}
</script>
</body></html>""")

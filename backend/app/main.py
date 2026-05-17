"""FastAPI App. Start: uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 (im backend/ Ordner)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from pydantic import BaseModel, EmailStr

from . import ai, renderer, scraper, storage, tunnels

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
):
    """Generiert (oder regeneriert) eine Webseite für ein Lead per Lovable AI."""
    lead = _find_lead(lead_id)

    existing = next((s for s in storage.load("sites") if s.get("lead_id") == lead_id), None)
    if existing and not force:
        return {"status": "exists", "site": existing}

    try:
        content = ai.generate_content(lead, language=language)
    except ai.AIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    slug = ai.slugify(lead.get("name") or lead_id) + "-" + lead_id[-6:].lower()
    html_doc = renderer.render_site(lead, content, slug)

    site = {
        "id": slug,
        "lead_id": lead_id,
        "slug": slug,
        "language": language,
        "content": content,
        "html": html_doc,
        "status": "generated",
        "claimed": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    saved = storage.upsert("sites", site)
    storage.upsert("leads", {**lead, "status": "site_generated", "site_slug": slug})
    return {"status": "ok", "site": {k: v for k, v in saved.items() if k != "html"}}


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


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    sites = storage.load("sites")
    items = "".join(
        f'<li><a href="/sites/{s["slug"]}">{s["content"].get("hero_title", s["slug"])}</a> '
        f'<small>({s["language"]})</small></li>'
        for s in sites
    )
    return HTMLResponse(f"""
    <html><head><title>LocalLift Sites</title>
    <style>body{{font:16px system-ui;max-width:720px;margin:40px auto;padding:0 20px}}
    li{{margin:8px 0}} a{{color:#1e40af}}</style></head>
    <body><h1>LocalLift – Generierte Seiten ({len(sites)})</h1>
    <ul>{items or '<p>Noch keine Seiten generiert.</p>'}</ul>
    <p><a href="/docs">→ API Docs</a></p>
    </body></html>
    """)

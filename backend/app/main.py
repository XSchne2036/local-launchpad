"""FastAPI App. Start: uvicorn app.main:app --reload (im backend/ Ordner)."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import scraper, storage

app = FastAPI(title="LocalLift Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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

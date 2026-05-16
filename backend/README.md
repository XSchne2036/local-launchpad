# LocalLift Backend

Python FastAPI Backend. Storage = JSON-Dateien in `data/`. Kein DB-Setup nötig.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# trage deinen GOOGLE_PLACES_API_KEY ein
```

**Google API Key** holen:
1. https://console.cloud.google.com/ → neues Projekt
2. APIs & Services → Library → **"Places API (New)"** aktivieren
3. Credentials → API Key erstellen → in `.env` einfügen

## Starten

```bash
uvicorn app.main:app --reload --port 8000
```

→ http://localhost:8000/docs  (Swagger UI)

## Scraper testen

```bash
curl -X POST "http://localhost:8000/scraper/run?query=Friseur%20in%20Berlin%20Mitte&region=DE"
```

Ergebnis landet in `data/leads.json`. Nur Einträge ohne Website werden gespeichert.

## Cloudflare Tunnel (für Kunden-Hosting)

```bash
cloudflared tunnel --url http://localhost:8000
```

→ liefert eine `*.trycloudflare.com` URL die du dem Kunden gibst.

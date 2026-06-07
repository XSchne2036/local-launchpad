# LocalLift Backend

Python FastAPI Backend. Storage = JSON-Dateien in `data/`. Kein DB-Setup.
Seiten-Erstellung via **Lovable API: Build with URL** (kein API-Key nötig).

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# eintragen: GOOGLE_PLACES_API_KEY
```

**Google Places Key**: https://console.cloud.google.com → "Places API (New)" aktivieren → API Key.
**Lovable Build with URL**: Der Backend-Button erzeugt einen Link wie `https://lovable.dev/?autosubmit=true#prompt=...`.

## Starten (Port 8002, im LAN erreichbar)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

- Lokal:    http://localhost:8002
- Netzwerk: http://<deine-ip>:8002
- Docs:     http://localhost:8002/docs

## Workflow

```bash
# 1. Leads scrapen (ohne Website)
curl -X POST "http://localhost:8002/scraper/run?query=Friseur%20in%20Berlin%20Mitte&region=DE"

# 2. Lovable Build-URL für ein Lead erzeugen
curl -X POST "http://localhost:8002/sites/generate/<LEAD_ID>?language=de"

# 3. Bulk: Build-URLs für 5 nächste Leads
curl -X POST "http://localhost:8002/sites/generate-batch?limit=5&language=de"

# 4. Übersicht
open http://localhost:8002/
```

## Cloudflare Tunnel (Kunden-Hosting)

```bash
cloudflared tunnel --url http://localhost:8002
```

→ liefert `*.trycloudflare.com` URL für den Kunden.

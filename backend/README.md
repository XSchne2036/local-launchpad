# LocalLift Backend

Python FastAPI Backend. Storage = JSON-Dateien in `data/`. Kein DB-Setup.
AI-Generation via **Lovable AI Gateway** (kein extra OpenAI-Key nötig).

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# eintragen: GOOGLE_PLACES_API_KEY + LOVABLE_API_KEY
```

**Google Places Key**: https://console.cloud.google.com → "Places API (New)" aktivieren → API Key.
**Lovable API Key**: Lovable Workspace → Settings → API Keys.

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

# 2. Webseite für ein Lead generieren
curl -X POST "http://localhost:8002/sites/generate/<LEAD_ID>?language=de"

# 3. Bulk: 5 nächste Leads
curl -X POST "http://localhost:8002/sites/generate-batch?limit=5&language=de"

# 4. Übersicht
open http://localhost:8002/
```

## Cloudflare Tunnel (Kunden-Hosting)

```bash
cloudflared tunnel --url http://localhost:8002
```

→ liefert `*.trycloudflare.com` URL für den Kunden.

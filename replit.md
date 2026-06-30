# LocalLift

A full-stack lead generation tool for local businesses. Finds businesses without websites via Google Maps, generates Lovable landing pages for them, and manages outreach.

## Stack

- **Frontend**: TanStack Start + React 19 + Tailwind CSS v4 + shadcn/ui (port 5000)
- **Backend**: Python FastAPI + uvicorn (port 8000)
- **Storage**: JSON files in `backend/data/`

## How to run

Two workflows are configured and auto-start:

| Workflow | Command | Port |
|---|---|---|
| `Start application` | `pnpm dev --port 5000 --host 0.0.0.0` | 5000 (frontend landing page) |
| `Backend` | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | 8000 (admin dashboard) |

The admin dashboard is at **port 8000** — switch to it in the Replit preview or open it via "Admin öffnen" on the landing page.

## Environment variables

Set these in `backend/.env` (copy from `backend/.env.example`):

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_PLACES_API_KEY` | ✅ Yes | Google Places API (New) – for the lead scraper |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` | Optional | SMTP for email outreach |
| `SMTP_FROM` / `SMTP_FROM_NAME` / `SMTP_SECURE` | Optional | SMTP sender details |
| `LOVABLE_API_KEY` | Optional | For AI-powered translations via Lovable gateway |

Set `VITE_BACKEND_URL` as a Replit Secret if deploying the frontend separately from the backend.

## Admin dashboard features

- **Scraper**: finds leads via Google Places API
- **Build-URL generation**: creates Lovable "Build with URL" links (opens Lovable to auto-create sites)
- **Two-table layout**: new leads (top) vs. generated/build-ready leads (bottom)
- **WhatsApp links**: phone numbers → `wa.me` links for direct messaging
- **Email links**: mailto: links pre-filled for Thunderbird (subject + body)
- **vCard download**: 📇 button downloads contact as `.vcf` for address book
- **Display filter**: hides leads that already have a website
- **Batch actions**: generates up to 5 Build-URLs at once (opens all in Lovable)
- **SMTP outreach**: sends templated emails; batch mode for up to 10 leads

## User preferences

- German UI throughout the admin dashboard
- Logo embedded from http://mrermin.com/logo.png
- Admin color scheme: dark navy (#1a3a6b) primary, amber (#e8a020) accent

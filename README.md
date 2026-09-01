# VeriGrid

**Crowdsourced hazard reports, verified by consensus — not by trust.**

VeriGrid turns scattered, unverifiable citizen hazard reports (flooding, road damage, unsafe construction, and more) into confidence-scored, geospatially-clustered hotspots — grounded against real terrain, weather, and infrastructure data, and routed to the right authority with a human still in the loop before anything is sent.

Built for [Hackathon Name] — see [Live Demo](#) · [Demo Video](#) · [Slides](#)

---

## Table of contents

- [The problem](#the-problem)
- [What VeriGrid does](#what-verigrid-does)
- [How it works](#how-it-works)
- [Key features](#key-features)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Running a live demo](#running-a-live-demo)
- [Project structure](#project-structure)
- [Known limitations & roadmap](#known-limitations--roadmap)
- [Team](#team)

---

## The problem

Citizen hazard reports on their own are noise, not signal: any single report could be a duplicate, a mistake, or spam, and local authorities have no reliable way to tell a real emerging hazard from one person's complaint — so most reports go nowhere. Meanwhile, the geospatial and environmental data that *could* corroborate a report (terrain, flood risk, weather, infrastructure proximity) sits in a completely separate system that citizen reporting tools never touch.

## What VeriGrid does

VeriGrid closes that loop. A citizen reports a hazard on a map; VeriGrid clusters it against nearby reports of the same kind, scores consensus confidence with anti-gaming protection (one person spamming the same report can't inflate a cluster), and cross-checks the location against real MirEye terrain/hazard data and NOAA weather. Once a cluster is independently confirmed by enough distinct reporters, it becomes a **verified hotspot** — at which point VeriGrid can draft an evidence-backed complaint to the responsible local authority (a human still has to approve and send it), warn drivers routing through the area, and answer natural-language questions about any point on the map, citing exactly which source — citizen reports or MirEye/NOAA data — each part of the answer came from.

## How it works

```
Citizen report (map click)
        │
        ▼
DBSCAN spatial clustering  ──── groups reports of the same category within ~150m
        │
        ▼
Consensus scoring  ──── dedup by reporter, confidence 0–100, anti-gaming capped
        │
        ├── forming (< 25)  →  candidate (25+)  →  verified (60+)
        │
        ▼
MirEye terrain/hazard context  +  NOAA weather context
        │
        ▼
   ┌────┴─────────────────────────────────┐
   ▼                                      ▼
Ask VeriGrid (RAG chat)          Authority Agent (verified clusters only)
grounded, source-attributed       LLM-drafted complaint → human approval
answer citing VeriGrid vs.        → send (SMTP or logged mock delivery)
MirEye/NOAA evidence

                Hazard-aware routing
     OSRM route → checked against verified hotspots
     → picks the first alternative that clears them,
       or warns if none do
```

Every report also gets an on-submission MirEye credibility check (e.g. is a flooding report actually near a floodplain or low elevation?) — advisory, never blocking, logged either way.

## Key features

- **Live map** — Leaflet map with click-to-report, category and verification-status filters, and distinct marker styles for raw reports vs. candidate vs. verified clusters.
- **Anonymous, no-login reporting** — a citizen is identified by a device-scoped id (no account needed), which the consensus engine uses to prevent one person's repeat reports from single-handedly verifying a cluster.
- **Spatial clustering (DBSCAN)** — reports within ~150m of each other and the same category are grouped into a single hazard cluster automatically, re-clustered on every new report.
- **Consensus + anti-gaming trust model** — confidence is the sum of each *distinct* reporter's trust score (capped per person); reporting the same thing five times counts once. Verifying a cluster rewards every contributor with a small trust bump.
- **MirEye geospatial grounding** — every report is checked against real terrain/flood-risk/hazard data for its category (flooding → flood-risk preset, safety → natural-hazard preset, etc.), producing a plausibility score and human-readable notes.
- **RAG chat ("Ask VeriGrid")** — ask a natural-language question about any point on the map; the answer is retrieved from nearby VeriGrid reports/clusters plus MirEye and NOAA context, and is explicitly labeled by which source it actually came from.
- **Authority Agent** — a verified cluster becomes an LLM-drafted, evidence-cited complaint addressed to the correct local authority (a fixed category → authority mapping), with severity, confidence, and contributor count computed from the cluster itself, not invented by the model. A human must approve before it's sent (SMTP if configured, otherwise a logged mock delivery for a repeatable demo).
- **Hazard-aware routing** — real OSRM routing, checked against verified hotspots along the path; picks the first alternative route that clears all of them, or is honest that none do, with full turn-by-turn directions.
- **Live sync status** — a visible, real (not decorative) log of every MirEye API call the backend has actually made.

## Tech stack

**Frontend** — Next.js 16 (App Router) · React 19 · Tailwind CSS v4 · Leaflet / react-leaflet · Axios

**Backend** — FastAPI · SQLAlchemy + GeoAlchemy2 · PostgreSQL + PostGIS (Neon serverless) · Alembic migrations · scikit-learn (DBSCAN) · OpenAI API (chat + reasoning agent) · MirEye API (terrain/hazard/infrastructure context) · NOAA National Weather Service API · OSRM (routing)

## Architecture

```
┌─────────────────┐        ┌──────────────────────────┐        ┌─────────────────┐
│   Next.js UI     │ HTTP   │        FastAPI            │        │   PostgreSQL     │
│  (map, chat,     │──────▶│  reports / clusters /      │◀──────▶│   + PostGIS      │
│  report form,    │◀──────│  chat / authority / route  │  SQL   │   (Neon)         │
│  authority view) │  JSON  │                            │        └─────────────────┘
└─────────────────┘        └──────────┬─────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┬───────────────┐
                    ▼                  ▼                  ▼               ▼
              MirEye API          NOAA API          OpenAI API        OSRM
        (terrain/hazard/       (weather/forecast)  (chat + complaint  (routing)
         infrastructure)                             generation)
```

## Getting started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- A PostgreSQL database with the PostGIS extension enabled (this project develops against [Neon](https://neon.tech)'s serverless Postgres)
- API keys: [OpenAI](https://platform.openai.com), MirEye (contact your MirEye access provider)

### 1. Clone

```bash
git clone https://github.com/bibrocks1/VeriGrid.git
cd VeriGrid
```

### 2. Backend

```bash
cd backend
python -m venv env
env\Scripts\activate        # Windows — use `source env/bin/activate` on macOS/Linux
pip install -r requirements.txt

cp .env.example .env        # then fill in DATABASE_URL, MIREYE_API_KEY, OPENAI_API_KEY
alembic upgrade head

uvicorn main:app --reload --port 8000
```

Backend is now live at `http://localhost:8000` (`/health` for a quick check, `/docs` for interactive Swagger UI).

### 3. Frontend

```bash
cd frontend
npm install

echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev:frontend
```

Frontend is now live at `http://localhost:3000`.

> Running `npm run dev` from `frontend/` starts both the frontend and backend together via `concurrently` — convenient once your `.env` is set up.

### Docker Compose (alternative)

```bash
docker-compose up --build
```

Builds both services from their `Dockerfile.dev`, exposes `:3000` and `:8000`, and hot-reloads on file changes. Requires `backend/.env` to already exist (compose reads it via `env_file`) — the PostGIS database itself is external (e.g. Neon), not included in the compose file.

### Without a backend at all

The frontend works standalone: every API call transparently falls back to realistic fixture data if `NEXT_PUBLIC_API_URL` is unset or the backend is unreachable, so `npm run dev:frontend` alone is enough to explore the UI.

## Environment variables

`backend/.env` (see `backend/.env.example`):

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL + PostGIS connection string |
| `MIREYE_API_KEY` | yes | MirEye terrain/hazard/infrastructure API |
| `MIREYE_BASE_URL` | no | Defaults to `https://api.mireye.com/v1` |
| `OPENAI_API_KEY` | yes | Powers the chat/reasoning agent and authority complaint drafting |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `AUTHORITY_DEMO_EMAIL` | no | Real email delivery for approved authority complaints. Omit any of these and delivery falls back to a logged mock send — the app works fully without them. |

`frontend/.env.local`:

| Variable | Required | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | no | Backend URL. Unset = demo mode against fixture data. |

## API reference

All routes are served from the FastAPI backend; full interactive docs at `/docs` once running.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/reports` | Submit a hazard report (triggers clustering + MirEye credibility check) |
| `GET` | `/reports` | All reports |
| `GET` | `/reports/nearby` | Reports within a radius of a point, with distance |
| `GET` | `/clusters` | All non-forming hazard clusters |
| `GET` | `/stats` | Active reports / verified hotspots / contributor counts |
| `POST` | `/chat` | RAG-grounded question answering (VeriGrid + MirEye + NOAA) |
| `POST` | `/clusters/{id}/assess` | Run the reasoning agent's severity assessment on a cluster |
| `GET` | `/clusters/{id}/report` | Generate (or fetch) a verified cluster's authority complaint draft |
| `POST` | `/clusters/{id}/send-report` | Approve and deliver an authority complaint |
| `GET` | `/complaints` | List all authority complaints |
| `GET` | `/alerts/nearby` | Verified clusters near a point (for polling-based alerts) |
| `GET` | `/route/safe` | Hazard-aware route between two points |
| `GET` | `/mireye/sync-log` | Log of real MirEye API calls made |

## Running a live demo

Verification needs **distinct reporters** — consensus dedupes by reporter, so one browser submitting the same report five times only ever counts once (that's the anti-gaming protection working as intended). To demo cluster verification without switching devices:

1. Open the **Report** section and submit a hazard report.
2. Click **"Simulate new reporter"** on the form (swaps the browser's local reporter identity) and submit again — same category, same approximate location.
3. Repeat: **3 distinct reporters** flips the cluster to *candidate*, **6** flips it to *verified*.
4. Once verified, scroll to **For authorities** to generate and approve a complaint, or try **Ask VeriGrid** and **Routes** to see the same cluster surfaced there.

## Project structure

```
VeriGrid/
├── backend/
│   ├── main.py              # FastAPI app, all routes
│   ├── models.py            # SQLAlchemy models (User, Report, HazardCluster, ...)
│   ├── clustering.py        # DBSCAN spatial clustering
│   ├── consensus.py         # Confidence scoring + anti-gaming + trust rewards
│   ├── mireye_service.py    # Report-credibility scoring against MirEye context
│   ├── adapters/            # MirEye, NOAA, OSRM routing adapters
│   ├── reasoning/           # Chat retrieval + reasoning agent + authority agent
│   ├── routing/             # Hazard-aware route selection
│   ├── notifications/       # Nearby-verified-hazard alerts
│   └── alembic/             # Database migrations
└── frontend/
    └── src/
        ├── app/page.js       # Landing/product page composition
        ├── components/       # map, report, chat, authority, verification UI
        └── lib/               # API client (with demo-mode fallback), constants
```

## Known limitations & roadmap

- MirEye's documented API doesn't currently expose an observation-write endpoint, so verified clusters can't be pushed back to MirEye — this is logged as a skipped attempt rather than silently doing nothing.
- Routing selects among a handful of OSRM route alternatives rather than true avoid-polygon routing; if no alternative fully avoids every verified hazard, it says so rather than guessing.
- No real user accounts — identity is a device-scoped id by design, matching the product's zero-friction reporting goal.
- Authority complaint delivery falls back to a logged mock send unless SMTP is configured.

## Team

- [Name] — [role]
- [Name] — [role]
- [Name] — [role]

---

Built for [Hackathon Name], [Date].

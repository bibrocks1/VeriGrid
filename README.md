<!-- SETUP.md Purpose: step-by-step developer setup for VeriGrid. Copy this file into the repository root (e.g., /SETUP.md) so contributors can run the project locally. -->
VeriGrid — Local Development Setup
<!-- Short summary for readers scanning the file -->

This document explains how to run VeriGrid locally for development (no fork required). It covers Docker Compose (recommended), local-only instructions for frontend and backend, environment variables, an optional PostGIS service, troubleshooting, and a basic branch/PR workflow.

Quick overview
<!-- Describe the main components and their default ports -->
Frontend: Next.js (frontend/) — serves at http://localhost:3000
Backend: FastAPI (backend/) — serves at http://localhost:8000 (health check: /health)
docker-compose.yml builds frontend and backend using Dockerfile.dev in each folder and mounts source code for hot reload.
Prerequisites
<!-- List what contributors need installed locally -->
Git (you have contributor access; no fork required)
Docker & Docker Compose (recommended)
If running without Docker:
Python 3.11+ and pip
Node.js (18+ recommended) and npm
System build dependencies (libpq-dev, gcc for psycopg2)
Optional: local Postgres + PostGIS instance if using geospatial database features
What's included
<!-- Point contributors to the relevant files already in the repo -->
frontend/README.md — Next.js instructions
docker-compose.yml — defines frontend and backend services (ports 3000 and 8000), uses Dockerfile.dev in each
backend/Dockerfile.dev and backend/requirements.txt — Python 3.11; dependencies include fastapi, psycopg2-binary, GeoAlchemy2
frontend/package.json — Next 16, React 19; dev script is npm run dev
backend/main.py — FastAPI app with a /health endpoint
1) Clone repository (no fork required)
<!-- Exact commands to clone; contributor will push branches to origin -->

SSH:

bash
git clone git@github.com:bibrocks1/VeriGrid.git
cd VeriGrid

or HTTPS:

bash
git clone https://github.com/bibrocks1/VeriGrid.git
cd VeriGrid
2) Run with Docker Compose (recommended)
<!-- Preferred path: builds both services and wires up hot reload via volume mounts -->

Prerequisites: Docker installed and running (and docker-compose if your Docker CLI needs it).

From the repo root:

bash
docker-compose up --build

What this does:

<!-- Explain each service's build context and exposed port -->
Builds frontend (context: ./frontend, Dockerfile.dev) and exposes localhost:3000
Builds backend (context: ./backend, Dockerfile.dev) and exposes localhost:8000
Mounts code as volumes so edits reload inside containers
<!-- Call out the .env dependency explicitly since compose will not start cleanly without it -->

Important — database configuration: docker-compose.yml references backend/.env (env_file: ./backend/.env). Create or check backend/.env before starting so the backend has a DATABASE_URL and any other secrets it expects. The repo expects PostGIS, but the compose file does not include a DB service.

Optional: local Postgres + PostGIS
<!-- Only needed if you don't already have a Postgres/PostGIS instance available -->

If you need a local Postgres+PostGIS, run one (example):

bash
docker run --name verigrid-postgis \
  -e POSTGRES_USER=vg \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=verigrid \
  -p 5432:5432 \
  -d postgis/postgis:15-3.3

Then set DATABASE_URL in backend/.env:

DATABASE_URL=postgresql://vg:secret@host.docker.internal:5432/verigrid
<!-- Note on Docker networking so contributors aren't confused by host.docker.internal -->

Note: When the backend runs in Docker, host.docker.internal lets the container reach a DB on the host. If you run the DB in a container on the same Docker network instead, use that service/container name as the host.

After compose is up
Frontend: http://localhost:3000
Backend health: http://localhost:8000/health
3) Run services locally (no Docker)
<!-- Alternative path for contributors who prefer running services directly on their machine -->
Backend (local Python)
Ensure system build deps for psycopg2 (Debian/Ubuntu example):
bash
   sudo apt-get update && sudo apt-get install -y libpq-dev gcc
Create and activate a virtual environment:
bash
   python3 -m venv .venv
   source .venv/bin/activate
Install Python dependencies:
bash
   pip install --upgrade pip
   pip install -r backend/requirements.txt
Configure environment: create backend/.env with DATABASE_URL (and any other required env vars).
Run uvicorn from the backend directory:
bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
Check: http://localhost:8000/health
Frontend (local Node)
Install Node.js (Node 18+ or latest LTS; Next 16 may expect a modern Node version).
Install and run from the repo root:
bash
   cd frontend
   npm install
   npm run dev
Visit: http://localhost:3000
Branching & contributing
<!-- Contributors push branches directly to origin — no fork/PR-from-fork workflow -->
Create a feature branch locally (don't fork):
bash
   git checkout -b feat/your-topic
Commit and push to origin:
bash
   git push -u origin feat/your-topic
Open a pull request on GitHub from that branch.
Troubleshooting tips
<!-- Common failure modes and quick fixes -->
Missing backend/.env: Create it and check for DATABASE_URL. Without a DB connection, the backend may error or not be fully functional.
psycopg2 install errors: Ensure libpq-dev and gcc are installed (or use psycopg2-binary, which the repo already lists).
Docker networking: If the DB runs as a separate container, prefer adding it to the compose file so services share a network and you can use the service name as the host.
Ports in use: If 3000 or 8000 are occupied, change host mappings in docker-compose.yml or use environment variables when running locally.
Hot-reload issues: If hot-reload doesn't pick up changes in Docker on some platforms, the compose file sets WATCHPACK_POLLING=true and mounts source — that helps on Windows/WSL.
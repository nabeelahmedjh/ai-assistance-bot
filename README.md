# AI Assistance Bot - Memox Technical Test

Proof-of-concept AI sales assistant for a shipping container company.

## Tech Stack

- Backend: Django + Django REST Framework + Channels
- Retrieval: sentence-transformers + pgvector
- Frontend: Next.js (App Router) + TypeScript
- Realtime: WebSocket chat with typing + token streaming

## Repository Structure

- `Backend/`: Django project (APIs, retrieval, ingestion, websocket consumer)
- `frontend/`: Next.js app (chat widget + admin page)
- `scripts/e2e_sanity.mjs`: End-to-end sanity test
- `DECISIONS.md`: Key implementation decisions
- `requirements.md`: Original assignment requirements

## Prerequisites

- Python 3.12+
- Node.js 22+
- npm

## Backend Setup

```bash
cd Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

Run backend API server:

```bash
python manage.py runserver 127.0.0.1:8000
```

Run websocket ASGI server (separate terminal):

```bash
cd Backend
source .venv/bin/activate
daphne -b 127.0.0.1 -p 8001 config.asgi:application
```

## Frontend Setup

```bash
cd frontend
nvm use 22
npm install
cp .env.local.example .env.local
npm run dev
```

Open:

- Chat page: `http://localhost:3000/`
- Admin page: `http://localhost:3000/admin`

## Environment Variables (frontend)

Defined in `frontend/.env.local.example`:

- `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000/api`)
- `NEXT_PUBLIC_WS_URL` (default `ws://127.0.0.1:8001`)
- `NEXT_PUBLIC_DEFAULT_LEAD_ID` (default `lead-demo-1`)

## API Endpoints

- `GET /api/documents/`
- `POST /api/documents/`
- `POST /api/documents/<id>/ingest/`
- `GET /api/documents/<id>/chunks/`
- `POST /api/ai/chat/`
- `GET /api/ai/chat/history/<lead_id>/`

WebSocket:

- `/ws/chat/<lead_id>/`

## Tests

Backend tests:

```bash
cd Backend
source .venv/bin/activate
python manage.py test documents.tests
```

Frontend checks:

```bash
cd frontend
nvm use 22
npm run lint
npm run build
```

## End-to-End Sanity Test

This script exercises: upload docs -> ingest -> REST chat -> history -> websocket chat.

```bash
cd /path/to/repo
nvm use 22
node scripts/e2e_sanity.mjs
```

Optional overrides:

- `API_BASE_URL`
- `WS_BASE_URL`
- `E2E_LEAD_ID`
- `E2E_CHAT_MESSAGE`

## Requirements Traceability

- Ingestion pipeline + chunking + embeddings: `Backend/documents/services/ingestion.py`
- Retrieval: `Backend/documents/services/retrieval.py`
- Prompting: `Backend/documents/services/prompting.py`
- Intent + routing: `Backend/documents/services/chat.py`
- REST views: `Backend/documents/views.py`
- WebSocket consumer + streaming: `Backend/documents/consumers.py`
- Chat widget: `frontend/src/components/chat-widget.tsx`
- Admin page: `frontend/src/app/admin/page.tsx`

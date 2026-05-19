# Iraqi Laboratory Transaction Management System (PWA)

Arabic-first governmental-style laboratory transaction platform for sample receipt/delivery, chain of custody, attachments, and reporting.

## Stack
- Frontend: Vue 3 + Vite + Pinia + Vue Router + Tailwind + PWA
- Backend: FastAPI + SQLAlchemy + Pydantic + Alembic-ready
- Database: PostgreSQL (UUID, FK, indexed)

## Key Features
- JWT login with roles: admin/supervisor/user/auditor
- Transaction-based architecture (not form-only)
- Transaction headers, items, status tracking, attachments metadata
- Validation rule: `total = valid + damaged + rejected + non-conforming`
- Immutable-style audit table (append-only usage)
- PWA installability with standalone mode
- Structured storage under `storage/`

## Project Structure
- `frontend/` Vue PWA application with RTL Arabic shell and required pages
- `backend/` FastAPI modular API with models/schemas/services/routes
- `storage/` receipts, attachments, exports, backups, temp
- `scripts/seed.py` seed organizations (35) and admin user

## Setup (Development)
1. Copy env:
   ```bash
   cp .env.example .env
   ```
2. Start PostgreSQL (docker):
   ```bash
   docker compose up -d db
   ```
3. Backend:
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
4. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## API Endpoints (initial)
- `POST /api/auth/login`
- `GET /api/transactions`
- `POST /api/transactions`
- `GET /api/health`

## Deployment (Ubuntu + Nginx)
- Run backend via gunicorn/uvicorn workers behind Nginx reverse proxy
- Build frontend static assets (`npm run build`) and serve via Nginx
- Use PostgreSQL managed service or local cluster
- Keep `storage/` on persistent disk

## Future Expansion Ready
Architecture separates API, services, repositories, and models to support LIS/HL7-FHIR, ministry integration, scanner hardware, multi-branch networking, and mobile clients.

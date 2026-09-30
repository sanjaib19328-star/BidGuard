# BidGuard AI — Backend (Phase 1)

AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement.

## Architecture
- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL 16+ with Async SQLAlchemy 2.0 & Alembic
- **Driver**: `asyncpg`
- **Audit**: Immutable audit event ledger with JSONB state tracking

---

## 1. Local PostgreSQL Setup (Docker Compose)

Start the PostgreSQL service:
```bash
docker compose up -d
```

Verify the container status:
```bash
docker compose ps
```

Stop the database service:
```bash
docker compose down
```

---

## 2. Environment Setup

### Create and activate virtual environment
```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Configure `.env`
Ensure your `.env` contains:
```env
DATABASE_URL=postgresql+asyncpg://bidguard:bidguard@localhost:5432/bidguard
DATABASE_ECHO=false
```

---

## 3. Database Migrations (Alembic)

Run migrations to apply the latest database schema:
```bash
alembic upgrade head
```

Check the current migration revision:
```bash
alembic current
```

View migration history:
```bash
alembic history
```

---

## 4. Running the Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

- **API Health**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 5. Running Tests

```bash
pytest -v
```

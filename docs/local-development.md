# Local development

Set up the FastAPI backend, React frontend, and (optionally) the test toolchain on your machine.

## Prerequisites

- Python 3.11+ (recommended)
- Node.js 18+ and npm

## 1. Python virtual environment

From the repository root:

```bash
cd /path/to/TELC-writing-evaluator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

For tests and coverage, also install:

```bash
pip install -r requirements-dev.txt
```

## 2. Backend environment variables

Create a `.env` file in the **repository root** (the same directory from which you run `uvicorn` and `pytest`):

```env
OPENROUTER_API_KEY=your_openrouter_key
MODEL_NAME=model_id e.g. openai/gpt-4o-mini
FALLBACK_MODEL_NAME=fallback_model_id
```

Without these, LLM-based evaluation calls will not work. Tests set safe dummy values via `backend/tests/conftest.py`, so you can run the suite before adding a real key.

## 3. Run the backend

With the venv activated:

```bash
PYTHONPATH=. uvicorn backend.main:app --reload
```

| Resource | URL / path |
| -------- | ---------- |
| API | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| Health | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) |
| Interactive docs | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| SQLite DB | `telc_evaluator.db` in the process working directory |

On startup the app creates tables and loads demo users plus the task bank from JSON idempotently (`backend/seed.py`, `backend/seed_tasks/`).

Seed accounts: `user@example.com`, `admin@example.com`. In the MVP most endpoints use a **fixed** demo user without JWT — see [`api_contract.md`](api_contract.md) and `backend/routers/users.py`.

## 4. Run the frontend

In a **second** terminal (venv not required for the UI):

```bash
cd frontend
npm install
npm run dev
```

By default the UI calls the API at `http://127.0.0.1:8000`. If the backend runs elsewhere, copy `frontend/.env.example` to `frontend/.env` and set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Restart `npm run dev` after changing `.env`.

Vite defaults to [http://127.0.0.1:5173](http://127.0.0.1:5173).

## Related

- [Testing](testing.md)
- [Deployment](deployment.md)
- [API contract](api_contract.md)

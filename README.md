# TELC Writing Evaluator

A web app for practicing TELC B2–style writing tasks with AI-assisted feedback (OpenRouter). It is a training aid, not an official TELC product or examiner.

## User workflow

1. **Home** — Read what the tool does and the disclaimer (no official link to TELC; AI results may differ from real exam marking). Accept the disclaimer to unlock training areas (stored in the browser).
2. **Training** — Start a **task session**: the app loads a paired **information** task and **complaint** task. Choose one, optionally use the **timer**, write your text in German, then submit.
3. **Evaluation** — The backend runs the evaluation pipeline (relevance, key points, communication, accuracy, scoring, improvement text) via an LLM. The UI shows progress, then redirects to **Result** with scores, criterion feedback, highlighted issues, and a suggested improved version.
4. **Archive** — Browse past submissions for the current demo user (again requires the accepted disclaimer).
5. **Profile** — View usage counters and account metadata exposed by the API.
6. **Admin** — UI for admin-only API actions (users, activate/deactivate, counters; CRUD for info and complaint tasks). In the MVP, the backend resolves an admin identity from seed data; see `docs/api_contract.md` and `backend/routers/admin.py`.

**Stack:** backend — Python, FastAPI, SQLite, SQLAlchemy; frontend — React (Vite), Tailwind. The HTTP API contract is documented in [`docs/api_contract.md`](docs/api_contract.md).

---

## Deployed (production)

| Service | URL                                              |
| ------- |--------------------------------------------------|
| Frontend | https://telc-writing-evaluator-9tee.onrender.com |
| Backend API | https://telc-writing-evaluator.onrender.com/docs |

After you add the URLs, confirm the frontend was built with `VITE_API_BASE_URL` pointing at the backend’s **HTTPS** URL (see **Render** below).

---

## Local development

Set everything up on your machine: backend API, frontend dev server, and (optionally) automated tests with coverage.

### Prerequisites

- Python 3.11+ (recommended)
- Node.js 18+ and npm

### 1. Python virtual environment

From the repository root:

```bash
cd /path/to/TELC-writing-evaluator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

For **tests and coverage** (section 5), also install dev tools:

```bash
pip install -r requirements-dev.txt
```

### 2. Backend environment variables

Create a `.env` file in the **repository root** (the same directory from which you run `uvicorn` and `pytest`):

```env
OPENROUTER_API_KEY=your_openrouter_key
MODEL_NAME=model_id e.g. openai/gpt-4o-mini
FALLBACK_MODEL_NAME=fallback_model_id
```

Without these, LLM-based evaluation calls will not work. Tests set safe dummy values via `conftest.py`, so you can run the suite even before adding a real key.

### 3. Run the backend

With the venv activated:

```bash
PYTHONPATH=. uvicorn backend.main:app --reload
```

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)  
- SQLite: `telc_evaluator.db` in the process working directory. On startup the app creates tables; demo users and the task bank from JSON are loaded idempotently (see `backend/seed.py`, `backend/seed_tasks/`).

The seed creates `user@example.com` and `admin@example.com`. In the current MVP, most endpoints use a **fixed** demo user (`user@example.com`) without a full session/JWT flow — see `backend/routers/users.py` and `docs/api_contract.md`.

### 4. Run the frontend

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

### 5. Backend tests and coverage

From the repository root, with the venv activated and dev dependencies installed (`requirements-dev.txt`):

**Run all backend tests:**

```bash
PYTHONPATH=. pytest backend/tests
```

**Coverage summary in the terminal** (overall % per file and missing lines in the table):

```bash
PYTHONPATH=. pytest backend/tests --cov=backend --cov-report=term-missing
```

**Coverage with HTML report** (same as above, plus browseable line coverage — open `htmlcov/index.html`):

```bash
PYTHONPATH=. pytest backend/tests \
  --cov=backend \
  --cov-report=term-missing \
  --cov-report=html
```

**Machine-readable coverage (e.g. for CI):**

```bash
PYTHONPATH=. pytest backend/tests --cov=backend --cov-report=xml
```

This writes `coverage.xml` in the repo root (also ignored by git via `.gitignore` patterns where applicable).

Coverage artifacts (`htmlcov/`, `.coverage`, `coverage.xml`) are covered by `.gitignore` where listed.

---

## Deploying on Render

Typical setup: two services — a **Web Service** (FastAPI) and a **Static Site** (Vite build).

### Backend (Web Service)

- **Root Directory:** leave empty (repo root) if the repo root already contains `backend/`.
- **Runtime:** Python.
- **Build Command:**  
  `pip install -r backend/requirements.txt`
- **Start Command:**  
  `PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

**Environment (Render → Environment):**

| Key | Value |
| --- | ----- |
| `OPENROUTER_API_KEY` | your OpenRouter secret |
| `MODEL_NAME` | e.g. `openai/gpt-oss-120b:free` |
| `FALLBACK_MODEL_NAME` | fallback model id |
| `CORS_ORIGINS` | comma-separated **exact** frontend origins (scheme + host, no trailing slash), e.g. `https://telc-writing-evaluator-9tee.onrender.com` |

The API always allows local Vite (`http://localhost:5173`, `http://127.0.0.1:5173`). For a deployed static site, set **`CORS_ORIGINS`** on the **backend** service to that site’s public URL, or the browser will block `fetch` with a CORS error.

**SQLite on Render:** the instance filesystem is **ephemeral** — data may be lost after redeploys. For durable data, attach a **Persistent Disk** or move to an external database when you need it.

### Frontend (Static Site)

**Important:** `package.json` lives in `frontend/`, not the repo root. If **Root Directory** is left blank, the build fails with `ENOENT ... package.json` (npm looks in `/opt/render/project/src/`).

Use **one** of these setups:

| Setting | Value A (recommended) | Value B (repo root as cwd) |
| --- | --- | --- |
| **Root Directory** | `frontend` | *(empty)* |
| **Build Command** | `npm install && npm run build` | `cd frontend && npm install && npm run build` |
| **Publish Directory** | `dist` | `frontend/dist` |

In the Render dashboard: open your static site → **Settings** → set **Root Directory** to `frontend` (and publish `dist`) → **Save Changes** → **Manual Deploy** → **Clear build cache & deploy**.

**Build-time environment:** `VITE_*` variables are inlined when `npm run build` runs. Set at least:

| Key | Value |
| --- | ----- |
| `VITE_API_BASE_URL` | full HTTPS URL of your Render backend, e.g. `https://your-api.onrender.com` |

Trigger a **new deploy** of the static site after changing `VITE_API_BASE_URL`.

---


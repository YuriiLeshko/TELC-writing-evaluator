# Triage Log — TELC Writing Evaluator

A running record of technical hurdles and how they were resolved while shipping the MVP. Dates are approximate; the goal is to capture **recurring** problem classes for reuse and onboarding.

| Period | Area | Problem | Resolution |
| ------ | ---- | ------- | ---------- |
| Early prototype | Frontend | First UI attempts in **Python** (e.g. Streamlit or a minimal templated server) were a poor fit for an **interactive** flow: sessions, task-selection steps, timer, smooth transition to a result view with highlights. App state **reset** between reruns; keeping a single contract with the API was painful. | Moved to an **SPA: React + Vite** — one place for client state, routing, and predictable REST calls. The contract is documented in `docs/api_contract.md`. |
| Early prototype | Process | Duplicated “result display” logic between a **demo script** and a real client. | Single client: the frontend; the backend returns JSON only. |
| Integration | Backend | **`OPENROUTER_API_KEY` / models** were read at **import** time; without a `.env` the process crashed before the server (or tests) started. | Documented required variables in the README; tests use `os.environ.setdefault(...)` in `conftest.py`. |
| Integration | Backend | **CORS**: the Render-hosted frontend (`*.onrender.com`) could not call the API — the browser blocked `fetch` with no `Access-Control-Allow-Origin`. | Added **`CORS_ORIGINS`** (comma-separated origins) plus default localhost origins for Vite; set the static site’s exact HTTPS URL on Render. |
| Data | Backend | After `init_db()` **tables were empty** — tasks never appeared and sessions could not start. The seeder lived in a standalone script and was easy to **forget**. | Call an **idempotent seed** on app startup (`apply_idempotent_seed` in lifespan); tests patch it so they do not touch production DB files. |
| Data | Backend | **`test_seed`** assumed **one** info and one complaint task, while `seed_tasks/` already had **20+ JSON files** per type — failure `assert 20 == 1`. | Expected counts come from `load_*_task_seeds()`; a second seed pass still asserts idempotency. |
| Infra | Backend / Render | **SQLite** on Render’s **ephemeral** disk — data disappeared after redeploys; not obvious when you are used to “one file next to the project” locally. | Documented in the README; for durable storage use a **Persistent Disk** or an external database. |
| Infra | Backend / Render | **`backend.*` imports** failed without `PYTHONPATH=.` — `ModuleNotFoundError` when running `uvicorn backend.main:app`. | README and Render **Start Command**: `PYTHONPATH=. uvicorn …`. |
| Infra | Frontend / Render | Build on Render: **`ENOENT package.json`** — the build ran from the **repo root** while `package.json` lives under `frontend/`. | Static Site: **Root Directory** = `frontend`, or use `cd frontend && npm ci && npm run build` and publish `frontend/dist`. |
| Infra | Frontend / Render | **`frontend/src/lib/utils.js`** never reached Git because **`.gitignore` contained `lib/`** (Python template pattern), so the Vite build failed on Render. | Switched to **`/lib/`** (repo root only); committed `utils.js`. |
| Infra | Frontend | **`VITE_API_BASE_URL`** missing at **build** time — production still pointed at `localhost:8000`. | Set the API’s HTTPS URL in Render static-site env **before** build; redeploy after changes. |
| Quality | Backend | **DeprecationWarning** from FastAPI: `@app.on_event("startup")` is deprecated. | Migrated to **`lifespan`** in `main.py`; pytest no longer emits those warnings. |
| Quality | Tooling | **No `npm` / Node** on the machine — the frontend could not be installed or built. | Documented install (e.g. Arch/Manjaro: `pacman -S nodejs npm`) or a version manager (nvm/fnm). |

## How to extend this log

1. One row = one **observable** failure or blocker.  
2. The **Resolution** column should name a concrete action (command, env var, commit, PR link), not “thought about it.”  
3. If the issue is **not** resolved, mark it open and add the next step.

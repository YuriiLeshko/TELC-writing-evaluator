# Deployment (Render)

Typical production layout: a **Web Service** (FastAPI) and a **Static Site** (Vite build).

## Deployed URLs

| Service | URL |
| ------- | --- |
| Frontend | https://telc-writing-evaluator-9tee.onrender.com |
| Backend API | https://telc-writing-evaluator.onrender.com/docs |

Confirm the frontend was built with `VITE_API_BASE_URL` pointing at the backend’s **HTTPS** URL (see Frontend below).

---

## Backend (Web Service)

| Setting | Value |
| ------- | ----- |
| **Root Directory** | empty (repo root) if the repo root already contains `backend/` |
| **Runtime** | Python |
| **Build Command** | `pip install -r backend/requirements.txt` |
| **Start Command** | `PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |

### Environment

| Key | Value |
| --- | ----- |
| `OPENROUTER_API_KEY` | your OpenRouter secret |
| `MODEL_NAME` | e.g. `openai/gpt-oss-120b:free` |
| `FALLBACK_MODEL_NAME` | fallback model id |
| `CORS_ORIGINS` | comma-separated **exact** frontend origins (scheme + host, no trailing slash), e.g. `https://telc-writing-evaluator-9tee.onrender.com` |

The API always allows local Vite (`http://localhost:5173`, `http://127.0.0.1:5173`). For a deployed static site, set **`CORS_ORIGINS`** on the **backend** to that site’s public URL, or the browser will block `fetch` with a CORS error.

### SQLite on Render

The instance filesystem is **ephemeral** — data may be lost after redeploys. For durable data, attach a **Persistent Disk** or move to an external database.

---

## Frontend (Static Site)

**Important:** `package.json` lives in `frontend/`, not the repo root. If **Root Directory** is left blank, the build fails with `ENOENT ... package.json` (npm looks in `/opt/render/project/src/`).

Use **one** of these setups:

| Setting | Value A (recommended) | Value B (repo root as cwd) |
| ------- | --------------------- | -------------------------- |
| **Root Directory** | `frontend` | *(empty)* |
| **Build Command** | `npm install && npm run build` | `cd frontend && npm install && npm run build` |
| **Publish Directory** | `dist` | `frontend/dist` |

In the Render dashboard: Static Site → **Settings** → **Root Directory** = `frontend` (publish `dist`) → **Save Changes** → **Manual Deploy** → **Clear build cache & deploy**.

### Build-time environment

`VITE_*` variables are inlined when `npm run build` runs. Set at least:

| Key | Value |
| --- | ----- |
| `VITE_API_BASE_URL` | full HTTPS URL of your Render backend, e.g. `https://your-api.onrender.com` |

Trigger a **new deploy** of the static site after changing `VITE_API_BASE_URL`.

---

## Related pitfalls

See [TRIAGE.md](../TRIAGE.md) for recurring CORS, `PYTHONPATH`, seed, and Render build issues.

# TELC Writing Evaluator — React Frontend

Vite + React (JavaScript) SPA. Talks to the FastAPI backend over HTTP; shapes are defined in [`docs/api_contract.md`](../docs/api_contract.md).

## Quick start

Full setup (venv, `.env`, both servers): [`docs/local-development.md`](../docs/local-development.md).

```bash
# API (repo root, venv on)
PYTHONPATH=. uvicorn backend.main:app --reload

# UI
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL if needed
npm run dev
```

Vite defaults to `http://127.0.0.1:5173`.

## Scripts

| Command | Description |
| ------- | ----------- |
| `npm run dev` | Dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |

## Deploy

Render static-site settings: [`docs/deployment.md`](../docs/deployment.md).

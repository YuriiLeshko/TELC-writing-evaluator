# TELC Writing Evaluator — React Frontend

Vite + React (JavaScript) SPA. Communicates with the FastAPI backend only via HTTP, following `docs/api_contract.md`.

## Lokale Entwicklung

**Backend:**

```bash
PYTHONPATH=. uvicorn backend.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Vite läuft standardmäßig unter `http://127.0.0.1:5173`. Die API-URL setzen Sie in `.env` über `VITE_API_BASE_URL` (siehe `.env.example`).

## Render Deployment

- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `dist`
- **Environment:** `VITE_API_BASE_URL=https://your-backend-url.onrender.com`

## Skripte

| Befehl        | Beschreibung        |
| ------------- | ------------------- |
| `npm run dev` | Entwicklungsserver  |
| `npm run build` | Produktions-Build |
| `npm run preview` | Vorschau des Builds |

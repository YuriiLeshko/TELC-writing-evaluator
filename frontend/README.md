# TELC Writing Evaluator Frontend (Streamlit MVP)

This frontend is an MVP UI for the existing FastAPI backend.
It communicates with backend endpoints only through HTTP requests.

## Prerequisites

- Python 3.10+
- Backend running locally

## Run backend

From the project root:

```bash
PYTHONPATH=. uvicorn backend.main:app --reload
```

By default backend is available on `http://127.0.0.1:8000`.

## Install frontend dependencies

From the project root:

```bash
pip install -r frontend/requirements.txt
```

## Run frontend

```bash
API_BASE_URL=http://127.0.0.1:8000 streamlit run frontend/app.py
```

If `API_BASE_URL` is not set, frontend uses:

- `http://127.0.0.1:8000`

## Demo auth note

Current backend auth is demo-based (no JWT yet). The frontend provides a UI role selector (User/Admin) for MVP navigation, while backend access control still follows backend demo helper logic.

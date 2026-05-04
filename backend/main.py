from __future__ import annotations
"""
FastAPI application entrypoint for TELC Writing Evaluator backend.

Purpose:
- Create and configure the API app instance for local MVP usage.
- Register middleware, startup database initialization, and route modules.

Structure:
- `app`: FastAPI instance with project title.
- CORS middleware: local Vite origins plus `CORS_ORIGINS` (comma-separated).
- Startup hook calling `init_db()`.
- `/health` endpoint for quick service checks.
- Router registration for users, task sessions, and submissions.

Dependencies:
- `fastapi` and `fastapi.middleware.cors`.
- `backend.database.init_db` for schema initialization.
- `backend.routers.*` modules for HTTP endpoints.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import submissions, task_sessions, users
from backend.routers import admin as admin_router
from backend.seed import apply_idempotent_seed

_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _cors_allow_origins() -> list[str]:
    """Local Vite defaults plus optional CORS_ORIGINS (comma-separated HTTPS origins on Render)."""
    extra = os.getenv("CORS_ORIGINS", "")
    merged: list[str] = list(_DEFAULT_CORS_ORIGINS)
    for part in extra.split(","):
        origin = part.strip()
        if origin and origin not in merged:
            merged.append(origin)
    return merged


app = FastAPI(title="TELC Writing Evaluator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    apply_idempotent_seed()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(task_sessions.router)
app.include_router(submissions.router)
app.include_router(admin_router.router)


if __name__ == "__main__":
    print("main.py smoke test passed.")
    print(f"app title: {app.title}")
    print(f"registered routes: {len(app.routes)}")

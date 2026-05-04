from __future__ import annotations
"""
FastAPI application entrypoint for TELC Writing Evaluator backend.

Purpose:
- Create and configure the API app instance for local MVP usage.
- Register middleware, startup database initialization, and route modules.

Structure:
- `app`: FastAPI instance with project title.
- CORS middleware for local frontend origins.
- Startup hook calling `init_db()`.
- `/health` endpoint for quick service checks.
- Router registration for users, task sessions, and submissions.

Dependencies:
- `fastapi` and `fastapi.middleware.cors`.
- `backend.database.init_db` for schema initialization.
- `backend.routers.*` modules for HTTP endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import submissions, task_sessions, users
from backend.routers import admin as admin_router
from backend.seed import apply_idempotent_seed

app = FastAPI(title="TELC Writing Evaluator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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

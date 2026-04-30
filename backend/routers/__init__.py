"""
Router package exports for TELC Writing Evaluator API.

Purpose:
- Provide a single import surface for route modules used in `backend.main`.

Structure:
- Re-exports: `users`, `task_sessions`, `submissions`.

Dependencies:
- Internal router modules from `backend.routers.*`.
"""

from backend.routers import submissions, task_sessions, users

__all__ = ["users", "task_sessions", "submissions"]


if __name__ == "__main__":
    print("routers/__init__.py smoke test passed.")
    print(f"exported routers: {', '.join(__all__)}")

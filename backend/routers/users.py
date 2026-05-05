from __future__ import annotations
"""
User router and demo-user dependency for MVP authentication placeholder.

Purpose:
- Provide simple user endpoints without JWT/auth flows.
- Resolve a fixed demo current user used by other routers.

Structure:
- `get_demo_current_user()` dependency (email-based lookup).
- `GET /users/me` for current demo user profile.
- `POST /users/register` for public registration.
- `PATCH /users/me` for own profile credentials update.
- `DELETE /users/me` for own account deletion.

Dependencies:
- `fastapi` routing/dependencies and HTTPException.
- `sqlalchemy` session + select.
- `backend.database.get_db`, `backend.models.User`, `backend.api_schemas.UserRead`.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api_schemas import UserRead, UserRegister, UserSelfUpdate
from backend.database import get_db
from backend.models import User

router = APIRouter(prefix="/users", tags=["users"])


def get_demo_current_user(db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.email == "user@example.com"))
    if user is None:
        user = db.scalar(select(User).where(User.username == "user"))
    if user is None:
        raise HTTPException(status_code=401, detail="Demo user not found. Run backend/seed.py first.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive.")
    return user


def get_demo_admin_user(db: Session = Depends(get_db)) -> User:
    admin = db.scalar(select(User).where(User.email == "admin@example.com"))
    if admin is None:
        raise HTTPException(status_code=401, detail="Demo admin not found. Run backend/seed.py first.")
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin user is inactive.")
    return admin


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_demo_current_user)) -> UserRead:
    return UserRead.model_validate(current_user, from_attributes=True)


@router.post("/register", response_model=UserRead, status_code=201)
def register_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
) -> UserRead:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already exists.")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=payload.password,
        role="user",
        is_active=True,
        available_sessions=5,
        available_submissions=5,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user, from_attributes=True)


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserSelfUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> UserRead:
    data = payload.model_dump(exclude_unset=True)
    if "username" in data:
        username_value = data["username"]
        current_user.username = username_value.strip() if isinstance(username_value, str) else username_value
    if "email" in data:
        email_value = data["email"]
        if not isinstance(email_value, str) or not email_value.strip():
            raise HTTPException(status_code=400, detail="Email cannot be empty.")
        normalized_email = email_value.strip()
        if normalized_email == current_user.email:
            normalized_email = None
        if normalized_email is not None:
            existing = db.scalar(select(User).where(User.email == normalized_email))
            if existing is not None:
                raise HTTPException(status_code=400, detail="Email already exists.")
            current_user.email = normalized_email
    if "password" in data:
        password_value = data["password"]
        if isinstance(password_value, str) and password_value.strip():
            current_user.hashed_password = password_value

    db.commit()
    db.refresh(current_user)
    return UserRead.model_validate(current_user, from_attributes=True)


@router.delete("/me")
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_current_user),
) -> dict[str, str]:
    db.delete(current_user)
    db.commit()
    return {"status": "deleted"}


if __name__ == "__main__":
    from backend.database import SessionLocal, init_db

    init_db()
    with SessionLocal() as db:
        users_count = len(db.scalars(select(User)).all())
    print("users.py smoke test passed.")
    print(f"users in database: {users_count}")

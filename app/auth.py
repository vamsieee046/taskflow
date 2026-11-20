from dataclasses import dataclass

from fastapi import Header, HTTPException

from .db import get_client


@dataclass
class CurrentUser:
    id: str
    token: str


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """Validate the Supabase JWT from the `Authorization: Bearer <token>` header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        user = get_client().auth.get_user(token).user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return CurrentUser(id=user.id, token=token)

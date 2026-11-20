"""Supabase access. Clients are created lazily so tests can import the app without credentials."""
import os
from functools import lru_cache

from supabase import Client, create_client


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


@lru_cache
def get_client() -> Client:
    """Shared anon-key client, used for sign-up, sign-in and token verification."""
    return create_client(_env("SUPABASE_URL"), _env("SUPABASE_KEY"))


def user_client(token: str) -> Client:
    """Per-request client that carries the user's JWT, so Postgres Row Level Security applies."""
    client = create_client(_env("SUPABASE_URL"), _env("SUPABASE_KEY"))
    client.postgrest.auth(token)
    return client


class TaskRepo:
    """All task persistence lives here, which keeps the routes thin and easy to fake in tests."""

    def __init__(self, client: Client, user_id: str):
        self.client = client
        self.user_id = user_id

    def _table(self):
        return self.client.table("tasks")

    def list(self) -> list[dict]:
        res = self._table().select("*").eq("user_id", self.user_id).order("created_at", desc=True).execute()
        return res.data

    def create(self, title: str, done: bool) -> dict:
        row = {"title": title, "done": done, "user_id": self.user_id}
        return self._table().insert(row).execute().data[0]

    def update(self, task_id: str, changes: dict) -> dict | None:
        res = self._table().update(changes).eq("id", task_id).eq("user_id", self.user_id).execute()
        return res.data[0] if res.data else None

    def delete(self, task_id: str) -> bool:
        res = self._table().delete().eq("id", task_id).eq("user_id", self.user_id).execute()
        return bool(res.data)

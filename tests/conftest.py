import itertools

import pytest
from fastapi.testclient import TestClient

from app.auth import CurrentUser, get_current_user
from app.main import app, get_repo


class FakeRepo:
    """In-memory stand-in for TaskRepo, so tests never touch Supabase."""

    def __init__(self, user_id="user-1"):
        self.user_id = user_id
        self.rows: list[dict] = []
        self._ids = itertools.count(1)

    def list(self):
        return [r for r in self.rows if r["user_id"] == self.user_id]

    def create(self, title, done):
        row = {"id": str(next(self._ids)), "title": title, "done": done, "user_id": self.user_id}
        self.rows.append(row)
        return row

    def update(self, task_id, changes):
        for r in self.list():
            if r["id"] == task_id:
                r.update(changes)
                return r
        return None

    def delete(self, task_id):
        before = len(self.rows)
        self.rows = [r for r in self.rows if not (r["id"] == task_id and r["user_id"] == self.user_id)]
        return len(self.rows) < before


@pytest.fixture
def repo():
    return FakeRepo()


@pytest.fixture
def client(repo):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id="user-1", token="t")
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()

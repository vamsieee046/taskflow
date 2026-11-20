from fastapi.testclient import TestClient

from app.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_metrics_exposed():
    res = TestClient(app).get("/metrics")
    assert res.status_code == 200
    assert "http_requests_total" in res.text or "python_info" in res.text


def test_index_served():
    res = TestClient(app).get("/")
    assert res.status_code == 200
    assert "TaskFlow" in res.text


def test_tasks_require_auth():
    assert TestClient(app).get("/tasks").status_code == 401


def test_create_and_list(client):
    created = client.post("/tasks", json={"title": "write report"})
    assert created.status_code == 201
    assert created.json()["title"] == "write report"
    assert [t["title"] for t in client.get("/tasks").json()] == ["write report"]


def test_update_and_delete(client):
    task_id = client.post("/tasks", json={"title": "ship it"}).json()["id"]
    assert client.patch(f"/tasks/{task_id}", json={"done": True}).json()["done"] is True
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get("/tasks").json() == []


def test_missing_task_returns_404(client):
    assert client.patch("/tasks/nope", json={"done": True}).status_code == 404
    assert client.delete("/tasks/nope").status_code == 404


def test_validation(client):
    assert client.post("/tasks", json={"title": ""}).status_code == 422
    assert client.post("/tasks", json={}).status_code == 422
    task_id = client.post("/tasks", json={"title": "x"}).json()["id"]
    assert client.patch(f"/tasks/{task_id}", json={}).status_code == 422


def test_users_are_isolated(client, repo):
    client.post("/tasks", json={"title": "mine"})
    repo.user_id = "someone-else"
    assert client.get("/tasks").json() == []

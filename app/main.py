import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from .auth import CurrentUser, get_current_user
from .db import TaskRepo, get_client, user_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("taskflow")

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="TaskFlow", version="1.0.0")

# Exposes Prometheus metrics at /metrics (request count, latency histogram, in-flight requests).
Instrumentator(excluded_handlers=["/metrics", "/health"]).instrument(app).expose(
    app, include_in_schema=False
)


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


def get_repo(user: CurrentUser = Depends(get_current_user)) -> TaskRepo:
    return TaskRepo(user_client(user.token), user.id)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}


@app.post("/auth/signup", status_code=201, tags=["auth"])
def signup(body: Credentials):
    try:
        res = get_client().auth.sign_up({"email": body.email, "password": body.password})
    except Exception as exc:
        log.warning("signup failed: %s", exc)
        raise HTTPException(status_code=400, detail="Sign-up failed. Check the email and password.") from None
    if res.session is None:
        return {"message": "Account created. Confirm your email, then log in."}
    return {"access_token": res.session.access_token}


@app.post("/auth/login", tags=["auth"])
def login(body: Credentials):
    try:
        res = get_client().auth.sign_in_with_password({"email": body.email, "password": body.password})
    except Exception:
        raise HTTPException(status_code=401, detail="Incorrect email or password.") from None
    return {"access_token": res.session.access_token}


@app.get("/tasks", tags=["tasks"])
def list_tasks(repo: TaskRepo = Depends(get_repo)):
    return repo.list()


@app.post("/tasks", status_code=201, tags=["tasks"])
def create_task(task: TaskIn, repo: TaskRepo = Depends(get_repo)):
    return repo.create(task.title, task.done)


@app.patch("/tasks/{task_id}", tags=["tasks"])
def update_task(task_id: str, patch: TaskPatch, repo: TaskRepo = Depends(get_repo)):
    changes = patch.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Nothing to update")
    updated = repo.update(task_id, changes)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.delete("/tasks/{task_id}", status_code=204, tags=["tasks"])
def delete_task(task_id: str, repo: TaskRepo = Depends(get_repo)):
    if not repo.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

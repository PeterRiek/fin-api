import os
import tempfile

# Must happen before anything imports app.dependencies (which reads .env and
# would otherwise point tests at the real sqlite file used by the app).
# A real (temp) file is used instead of "sqlite:///:memory:" because an
# in-memory sqlite database is per-connection, and TestClient dispatches sync
# routes across a threadpool, so each request would otherwise see an empty DB.
_tmp_dir = tempfile.TemporaryDirectory()
os.environ["DATABASE_URI"] = f"sqlite:///{_tmp_dir.name}/test.db"

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.database import Database
from app.dependencies import get_db
from app.models import Base


@pytest.fixture(autouse=True)
def reset_db():
    db = get_db()
    Base.metadata.drop_all(db.engine)
    Base.metadata.create_all(db.engine)
    yield


@pytest.fixture
def db() -> Database:
    return get_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def register_and_login(client: TestClient):
    def _make(username: str = "alice", password: str = "hunter2"):
        client.post(
            "/auth/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": password,
            },
        )
        response = client.post(
            "/auth/login",
            data={"username": username, "password": password},
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make

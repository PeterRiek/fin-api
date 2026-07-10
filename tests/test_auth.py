def test_register_returns_user_without_password(client):
    response = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "hunter2"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username_fails(client):
    payload = {"username": "alice", "email": "alice@example.com", "password": "hunter2"}
    client.post("/auth/register", json=payload)
    response = client.post(
        "/auth/register",
        json={"username": "alice", "email": "other@example.com", "password": "x"},
    )
    assert response.status_code == 400


def test_login_success(client):
    client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "hunter2"},
    )
    response = client.post(
        "/auth/login", data={"username": "alice", "password": "hunter2"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_fails(client):
    client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "hunter2"},
    )
    response = client.post(
        "/auth/login", data={"username": "alice", "password": "wrong"}
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    response = client.get("/split/persons")
    assert response.status_code == 401

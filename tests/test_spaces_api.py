def test_create_space_makes_creator_the_owner(client, register_and_login):
    headers = register_and_login("alice")
    response = client.post(
        "/split/spaces",
        json={"name": "Trip", "description": "Ski trip"},
        headers=headers,
    )
    assert response.status_code == 201
    space = response.json()

    users = client.get(f"/split/spaces/{space['id']}/users", headers=headers).json()
    assert [u["username"] for u in users] == ["alice"]


def test_list_get_update_delete_space(client, register_and_login):
    headers = register_and_login("alice")
    space = client.post("/split/spaces", json={"name": "Trip"}, headers=headers).json()

    assert [s["id"] for s in client.get("/split/spaces", headers=headers).json()] == [
        space["id"]
    ]

    response = client.get(f"/split/spaces/{space['id']}", headers=headers)
    assert response.status_code == 200

    response = client.put(
        f"/split/spaces/{space['id']}", json={"name": "Trip 2026"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Trip 2026"

    response = client.delete(f"/split/spaces/{space['id']}", headers=headers)
    assert response.status_code == 204
    assert (
        client.get(f"/split/spaces/{space['id']}", headers=headers).status_code == 404
    )


def test_space_not_visible_to_unrelated_user(client, register_and_login):
    alice_headers = register_and_login("alice")
    space = client.post(
        "/split/spaces", json={"name": "Trip"}, headers=alice_headers
    ).json()

    bob_headers = register_and_login("bob")
    assert (
        client.get(f"/split/spaces/{space['id']}", headers=bob_headers).status_code
        == 404
    )
    assert (
        client.delete(f"/split/spaces/{space['id']}", headers=bob_headers).status_code
        == 404
    )


def test_add_and_remove_user_from_space(client, register_and_login):
    alice_headers = register_and_login("alice")
    space = client.post(
        "/split/spaces", json={"name": "Trip"}, headers=alice_headers
    ).json()

    bob_token_response = client.post(
        "/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "hunter2"},
    )
    bob_id = bob_token_response.json()["id"]

    response = client.post(
        f"/split/spaces/{space['id']}/users",
        params={"user_id": bob_id},
        headers=alice_headers,
    )
    assert response.status_code == 201

    users = client.get(
        f"/split/spaces/{space['id']}/users", headers=alice_headers
    ).json()
    assert {u["username"] for u in users} == {"alice", "bob"}

    response = client.delete(
        f"/split/spaces/{space['id']}/users/{bob_id}", headers=alice_headers
    )
    assert response.status_code == 204
    users = client.get(
        f"/split/spaces/{space['id']}/users", headers=alice_headers
    ).json()
    assert {u["username"] for u in users} == {"alice"}


def test_add_and_remove_person_from_space(client, register_and_login):
    headers = register_and_login("alice")
    space = client.post("/split/spaces", json={"name": "Trip"}, headers=headers).json()
    person = client.post(
        "/split/persons", json={"name": "Grace"}, headers=headers
    ).json()

    response = client.post(
        f"/split/spaces/{space['id']}/persons",
        params={"person_id": person["id"]},
        headers=headers,
    )
    assert response.status_code == 201

    people = client.get(f"/split/spaces/{space['id']}/persons", headers=headers).json()
    assert [p["id"] for p in people] == [person["id"]]

    response = client.delete(
        f"/split/spaces/{space['id']}/persons/{person['id']}", headers=headers
    )
    assert response.status_code == 204
    people = client.get(f"/split/spaces/{space['id']}/persons", headers=headers).json()
    assert people == []


def test_space_transactions_list(client, register_and_login):
    headers = register_and_login("alice")
    space = client.post("/split/spaces", json={"name": "Trip"}, headers=headers).json()

    response = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Hotel", "date": "2026-01-01"},
        headers=headers,
    )
    assert response.status_code == 201

    transactions = client.get(
        f"/split/spaces/{space['id']}/transactions", headers=headers
    ).json()
    assert [t["title"] for t in transactions] == ["Hotel"]

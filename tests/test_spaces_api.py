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


def register_and_login_with_id(client, username):
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "hunter2",
        },
    )
    user_id = response.json()["id"]
    login = client.post(
        "/auth/login", data={"username": username, "password": "hunter2"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return headers, user_id


def test_cannot_add_user_already_in_space(client, register_and_login):
    alice_headers, alice_id = register_and_login_with_id(client, "alice")
    space = client.post(
        "/split/spaces", json={"name": "Trip"}, headers=alice_headers
    ).json()

    # Owner is already a member; adding herself should fail cleanly.
    response = client.post(
        f"/split/spaces/{space['id']}/users",
        params={"user_id": alice_id},
        headers=alice_headers,
    )
    assert response.status_code == 400

    bob_headers, bob_id = register_and_login_with_id(client, "bob")
    response = client.post(
        f"/split/spaces/{space['id']}/users",
        params={"user_id": bob_id},
        headers=alice_headers,
    )
    assert response.status_code == 201

    # Adding Bob again should also fail cleanly, not 500.
    response = client.post(
        f"/split/spaces/{space['id']}/users",
        params={"user_id": bob_id},
        headers=alice_headers,
    )
    assert response.status_code == 400


def test_non_owner_cannot_delete_space(client, register_and_login):
    alice_headers = register_and_login("alice")
    space = client.post(
        "/split/spaces", json={"name": "Trip"}, headers=alice_headers
    ).json()
    bob_headers, bob_id = register_and_login_with_id(client, "bob")
    client.post(
        f"/split/spaces/{space['id']}/users",
        params={"user_id": bob_id},
        headers=alice_headers,
    )

    response = client.delete(f"/split/spaces/{space['id']}", headers=bob_headers)
    assert response.status_code == 403

    response = client.delete(f"/split/spaces/{space['id']}", headers=alice_headers)
    assert response.status_code == 204


def test_non_owner_cannot_add_user_to_space(client, register_and_login):
    alice_headers = register_and_login("alice")
    space = client.post(
        "/split/spaces", json={"name": "Trip"}, headers=alice_headers
    ).json()
    bob_headers, bob_id = register_and_login_with_id(client, "bob")
    client.post(
        f"/split/spaces/{space['id']}/users",
        params={"user_id": bob_id},
        headers=alice_headers,
    )
    _, carol_id = register_and_login_with_id(client, "carol")

    response = client.post(
        f"/split/spaces/{space['id']}/users",
        params={"user_id": carol_id},
        headers=bob_headers,
    )
    assert response.status_code == 403


def test_non_owner_can_leave_but_not_remove_others(client, register_and_login):
    alice_headers = register_and_login("alice")
    space = client.post(
        "/split/spaces", json={"name": "Trip"}, headers=alice_headers
    ).json()
    bob_headers, bob_id = register_and_login_with_id(client, "bob")
    _, carol_id = register_and_login_with_id(client, "carol")
    for user_id in (bob_id, carol_id):
        client.post(
            f"/split/spaces/{space['id']}/users",
            params={"user_id": user_id},
            headers=alice_headers,
        )

    # Bob cannot remove Carol, another non-owner member.
    response = client.delete(
        f"/split/spaces/{space['id']}/users/{carol_id}", headers=bob_headers
    )
    assert response.status_code == 403

    # Bob can remove himself (leave the space).
    response = client.delete(
        f"/split/spaces/{space['id']}/users/{bob_id}", headers=bob_headers
    )
    assert response.status_code == 204


def test_space_owner_cannot_be_removed(client, register_and_login):
    alice_headers, alice_id = register_and_login_with_id(client, "alice")
    space = client.post(
        "/split/spaces", json={"name": "Trip"}, headers=alice_headers
    ).json()
    bob_headers, bob_id = register_and_login_with_id(client, "bob")
    client.post(
        f"/split/spaces/{space['id']}/users",
        params={"user_id": bob_id},
        headers=alice_headers,
    )

    # Neither the owner herself nor another member can remove the owner.
    response = client.delete(
        f"/split/spaces/{space['id']}/users/{alice_id}", headers=alice_headers
    )
    assert response.status_code == 403

    response = client.delete(
        f"/split/spaces/{space['id']}/users/{alice_id}", headers=bob_headers
    )
    assert response.status_code == 403


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

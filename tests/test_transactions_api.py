def _space_person_account(client, headers, name="Grace"):
    space = client.post(
        "/split/spaces", json={"name": "Household"}, headers=headers
    ).json()
    person = client.post("/split/persons", json={"name": name}, headers=headers).json()
    client.post(
        f"/split/spaces/{space['id']}/persons",
        params={"person_id": person["id"]},
        headers=headers,
    )
    account = client.post(
        "/split/accounts",
        json={"name": f"{name}'s account", "person_id": person["id"]},
        headers=headers,
    ).json()
    return space, person, account


def test_create_transaction_requires_owned_space(client, register_and_login):
    alice_headers = register_and_login("alice")
    space, _, _ = _space_person_account(client, alice_headers)

    bob_headers = register_and_login("bob")
    response = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=bob_headers,
    )
    assert response.status_code == 403


def test_get_update_delete_transaction(client, register_and_login):
    headers = register_and_login("alice")
    space, _, _ = _space_person_account(client, headers)
    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=headers,
    ).json()

    assert (
        client.get(
            f"/split/transactions/{transaction['id']}", headers=headers
        ).status_code
        == 200
    )

    response = client.put(
        f"/split/transactions/{transaction['id']}",
        json={"space_id": space["id"], "title": "Groceries v2", "date": "2026-01-02"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Groceries v2"

    response = client.delete(
        f"/split/transactions/{transaction['id']}", headers=headers
    )
    assert response.status_code == 204
    assert (
        client.get(
            f"/split/transactions/{transaction['id']}", headers=headers
        ).status_code
        == 404
    )


def test_transaction_not_visible_to_unrelated_user(client, register_and_login):
    alice_headers = register_and_login("alice")
    space, _, _ = _space_person_account(client, alice_headers)
    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=alice_headers,
    ).json()

    bob_headers = register_and_login("bob")
    response = client.get(
        f"/split/transactions/{transaction['id']}", headers=bob_headers
    )
    assert response.status_code == 403


# ---------- Contributions ----------


def test_create_contribution_requires_owned_account(client, register_and_login):
    alice_headers = register_and_login("alice")
    space, _, _ = _space_person_account(client, alice_headers)
    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=alice_headers,
    ).json()

    bob_headers = register_and_login("bob")
    _, _, bobs_account = _space_person_account(client, bob_headers, name="Bob")

    response = client.post(
        f"/split/transactions/{transaction['id']}/contributions",
        json={
            "account_id": bobs_account["id"],
            "transaction_id": transaction["id"],
            "amount_requested": 10.0,
            "amount_paid": 0.0,
        },
        headers=alice_headers,
    )
    assert response.status_code == 403


def test_contribution_crud(client, register_and_login):
    headers = register_and_login("alice")
    space, _, account = _space_person_account(client, headers)
    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=headers,
    ).json()

    response = client.post(
        f"/split/transactions/{transaction['id']}/contributions",
        json={
            "account_id": account["id"],
            "transaction_id": transaction["id"],
            "amount_requested": 50.0,
            "amount_paid": 50.0,
            "is_initial": True,
        },
        headers=headers,
    )
    assert response.status_code == 201

    contributions = client.get(
        f"/split/transactions/{transaction['id']}/contributions", headers=headers
    ).json()
    assert len(contributions) == 1

    response = client.get(
        f"/split/transactions/{transaction['id']}/contributions/{account['id']}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["amount_requested"] == 50.0

    response = client.put(
        f"/split/transactions/{transaction['id']}/contributions/{account['id']}",
        json={
            "account_id": account["id"],
            "transaction_id": transaction["id"],
            "amount_requested": 75.0,
            "amount_paid": 25.0,
            "is_initial": False,
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["amount_requested"] == 75.0

    response = client.delete(
        f"/split/transactions/{transaction['id']}/contributions/{account['id']}",
        headers=headers,
    )
    assert response.status_code == 204
    assert (
        client.get(
            f"/split/transactions/{transaction['id']}/contributions/{account['id']}",
            headers=headers,
        ).status_code
        == 404
    )


# ---------- Categories ----------


def test_link_and_unlink_transaction_category(client, register_and_login):
    headers = register_and_login("alice")
    space, _, _ = _space_person_account(client, headers)
    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=headers,
    ).json()
    category = client.post(
        "/split/categories", json={"name": "Groceries"}, headers=headers
    ).json()

    response = client.post(
        f"/split/transactions/{transaction['id']}/categories",
        params={"category_id": category["id"]},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json() == {
        "transaction_id": transaction["id"],
        "category_id": category["id"],
    }

    categories = client.get(
        f"/split/transactions/{transaction['id']}/categories", headers=headers
    ).json()
    assert [c["id"] for c in categories] == [category["id"]]

    detail = client.get(
        f"/split/transactions/{transaction['id']}", headers=headers
    ).json()
    assert [c["id"] for c in detail["categories"]] == [category["id"]]

    response = client.delete(
        f"/split/transactions/{transaction['id']}/categories/{category['id']}",
        headers=headers,
    )
    assert response.status_code == 204
    assert (
        client.get(
            f"/split/transactions/{transaction['id']}/categories", headers=headers
        ).json()
        == []
    )


def test_link_unknown_category_is_404(client, register_and_login):
    headers = register_and_login("alice")
    space, _, _ = _space_person_account(client, headers)
    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=headers,
    ).json()

    response = client.post(
        f"/split/transactions/{transaction['id']}/categories",
        params={"category_id": 999},
        headers=headers,
    )
    assert response.status_code == 404


def test_unlink_missing_link_is_404(client, register_and_login):
    headers = register_and_login("alice")
    space, _, _ = _space_person_account(client, headers)
    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=headers,
    ).json()
    category = client.post(
        "/split/categories", json={"name": "Groceries"}, headers=headers
    ).json()

    response = client.delete(
        f"/split/transactions/{transaction['id']}/categories/{category['id']}",
        headers=headers,
    )
    assert response.status_code == 404

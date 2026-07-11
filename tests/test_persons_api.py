def _create_space(client, headers, name="Household"):
    response = client.post("/split/spaces", json={"name": name}, headers=headers)
    return response.json()


def _create_person_in_space(client, headers, space_id, name="Grace"):
    person = client.post("/split/persons", json={"name": name}, headers=headers).json()
    client.post(
        f"/split/spaces/{space_id}/persons",
        params={"person_id": person["id"]},
        headers=headers,
    )
    return person


def test_create_person_not_visible_until_added_to_a_space(client, register_and_login):
    headers = register_and_login("alice")
    client.post("/split/persons", json={"name": "Grace"}, headers=headers)

    response = client.get("/split/persons", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_person_visible_after_added_to_space(client, register_and_login):
    headers = register_and_login("alice")
    space = _create_space(client, headers)
    person = _create_person_in_space(client, headers, space["id"])

    response = client.get("/split/persons", headers=headers)
    assert [p["id"] for p in response.json()] == [person["id"]]

    response = client.get(f"/split/persons/{person['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Grace"


def test_update_and_delete_person(client, register_and_login):
    headers = register_and_login("alice")
    space = _create_space(client, headers)
    person = _create_person_in_space(client, headers, space["id"])

    response = client.put(
        f"/split/persons/{person['id']}", json={"name": "Grace H."}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Grace H."

    response = client.delete(f"/split/persons/{person['id']}", headers=headers)
    assert response.status_code == 204
    assert (
        client.get(f"/split/persons/{person['id']}", headers=headers).status_code == 404
    )


def test_person_not_visible_to_unrelated_user(client, register_and_login):
    alice_headers = register_and_login("alice")
    space = _create_space(client, alice_headers)
    person = _create_person_in_space(client, alice_headers, space["id"])

    bob_headers = register_and_login("bob")
    response = client.get(f"/split/persons/{person['id']}", headers=bob_headers)
    assert response.status_code == 404

    response = client.put(
        f"/split/persons/{person['id']}", json={"name": "hijacked"}, headers=bob_headers
    )
    assert response.status_code == 404


def test_get_person_missing_returns_404(client, register_and_login):
    headers = register_and_login("alice")
    response = client.get("/split/persons/999", headers=headers)
    assert response.status_code == 404


def _contribute(client, headers, transaction_id, account_id, requested, paid):
    client.post(
        f"/split/transactions/{transaction_id}/contributions",
        json={
            "account_id": account_id,
            "transaction_id": transaction_id,
            "amount_requested": requested,
            "amount_paid": paid,
        },
        headers=headers,
    )


def test_person_transactions_and_summary_scoped_to_shared_spaces(
    client, register_and_login
):
    # Anyone can add an existing person to their own space (by design), but a
    # user must only see that person's activity in spaces they share with them.
    alice_headers = register_and_login("alice")
    alice_space = _create_space(client, alice_headers, "Alice's household")
    grace = _create_person_in_space(client, alice_headers, alice_space["id"])
    grace_account = client.post(
        "/split/accounts",
        json={"name": "Grace's account", "person_id": grace["id"]},
        headers=alice_headers,
    ).json()
    alice_transaction = client.post(
        "/split/transactions",
        json={
            "space_id": alice_space["id"],
            "title": "Rent",
            "date": "2026-01-01",
        },
        headers=alice_headers,
    ).json()
    _contribute(
        client, alice_headers, alice_transaction["id"], grace_account["id"], 20.0, 0.0
    )

    bob_headers = register_and_login("bob")
    bob_space = _create_space(client, bob_headers, "Bob's household")
    client.post(
        f"/split/spaces/{bob_space['id']}/persons",
        params={"person_id": grace["id"]},
        headers=bob_headers,
    )
    bob_transaction = client.post(
        "/split/transactions",
        json={
            "space_id": bob_space["id"],
            "title": "Bob's trip",
            "date": "2026-02-01",
        },
        headers=bob_headers,
    ).json()
    _contribute(
        client, bob_headers, bob_transaction["id"], grace_account["id"], 500.0, 0.0
    )

    response = client.get(
        f"/split/persons/{grace['id']}/transactions", headers=alice_headers
    )
    assert [t["id"] for t in response.json()] == [alice_transaction["id"]]

    summary = client.get(
        f"/split/persons/{grace['id']}/summary", headers=alice_headers
    ).json()
    assert summary["transaction_count"] == 1
    assert summary["net_balance"] == -20.0

    response = client.get(
        f"/split/persons/{grace['id']}/transactions", headers=bob_headers
    )
    assert [t["id"] for t in response.json()] == [bob_transaction["id"]]

    summary = client.get(
        f"/split/persons/{grace['id']}/summary", headers=bob_headers
    ).json()
    assert summary["transaction_count"] == 1
    assert summary["net_balance"] == -500.0

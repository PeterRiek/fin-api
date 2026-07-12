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


# ---------- Simple income/expense ----------


def test_create_expense_reduces_balance(client, register_and_login):
    headers = register_and_login("alice")
    space, _, account = _space_person_account(client, headers)

    response = client.post(
        f"/split/accounts/{account['id']}/transactions",
        json={
            "space_id": space["id"],
            "title": "Miete",
            "date": "2026-01-01",
            "type": "expense",
            "amount": 800.0,
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "expense"
    assert body["contributions"][0]["real_amount"] == -800.0

    balance = client.get(
        f"/split/accounts/{account['id']}/balance", headers=headers
    ).json()
    assert balance["balance"] == -800.0


def test_create_income_increases_balance(client, register_and_login):
    headers = register_and_login("alice")
    space, _, account = _space_person_account(client, headers)

    response = client.post(
        f"/split/accounts/{account['id']}/transactions",
        json={
            "space_id": space["id"],
            "title": "Gehalt",
            "date": "2026-01-01",
            "type": "income",
            "amount": 3000.0,
        },
        headers=headers,
    )
    assert response.status_code == 201

    balance = client.get(
        f"/split/accounts/{account['id']}/balance", headers=headers
    ).json()
    assert balance["balance"] == 3000.0


def test_default_transaction_type_is_expense(client, register_and_login):
    headers = register_and_login("alice")
    space, _, account = _space_person_account(client, headers)

    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=headers,
    ).json()
    assert transaction["type"] == "expense"
    assert transaction["linked_transaction_id"] is None


def test_create_account_transaction_requires_owned_space(client, register_and_login):
    alice_headers = register_and_login("alice")
    _, _, alices_account = _space_person_account(client, alice_headers)

    bob_headers = register_and_login("bob")
    bobs_space, _, _ = _space_person_account(client, bob_headers, name="Bob")

    response = client.post(
        f"/split/accounts/{alices_account['id']}/transactions",
        json={
            "space_id": bobs_space["id"],
            "title": "hijack",
            "date": "2026-01-01",
            "type": "income",
            "amount": 100.0,
        },
        headers=alice_headers,
    )
    assert response.status_code == 403


def test_create_account_transaction_requires_owned_account(client, register_and_login):
    alice_headers = register_and_login("alice")
    space, _, _ = _space_person_account(client, alice_headers)

    bob_headers = register_and_login("bob")
    _, _, bobs_account = _space_person_account(client, bob_headers, name="Bob")

    response = client.post(
        f"/split/accounts/{bobs_account['id']}/transactions",
        json={
            "space_id": space["id"],
            "title": "hijack",
            "date": "2026-01-01",
            "type": "income",
            "amount": 100.0,
        },
        headers=alice_headers,
    )
    assert response.status_code == 404


# ---------- Transfers ----------


def test_transfer_moves_balance_between_accounts(client, register_and_login):
    headers = register_and_login("alice")
    space, person, checking = _space_person_account(client, headers, name="Grace")
    savings = client.post(
        "/split/accounts",
        json={"name": "Grace's savings", "person_id": person["id"]},
        headers=headers,
    ).json()

    client.post(
        f"/split/accounts/{checking['id']}/transactions",
        json={
            "space_id": space["id"],
            "title": "Gehalt",
            "date": "2026-01-01",
            "type": "income",
            "amount": 1000.0,
        },
        headers=headers,
    )

    response = client.post(
        f"/split/accounts/{checking['id']}/transfers",
        json={
            "space_id": space["id"],
            "to_account_id": savings["id"],
            "amount": 400.0,
            "date": "2026-01-02",
            "title": "Sparen",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["out_transaction"]["type"] == "expense"
    assert body["in_transaction"]["type"] == "income"
    assert (
        body["out_transaction"]["linked_transaction_id"] == body["in_transaction"]["id"]
    )
    assert (
        body["in_transaction"]["linked_transaction_id"] == body["out_transaction"]["id"]
    )

    checking_balance = client.get(
        f"/split/accounts/{checking['id']}/balance", headers=headers
    ).json()
    savings_balance = client.get(
        f"/split/accounts/{savings['id']}/balance", headers=headers
    ).json()
    assert checking_balance["balance"] == 600.0
    assert savings_balance["balance"] == 400.0


def test_transfer_to_same_account_is_rejected(client, register_and_login):
    headers = register_and_login("alice")
    space, _, account = _space_person_account(client, headers)

    response = client.post(
        f"/split/accounts/{account['id']}/transfers",
        json={
            "space_id": space["id"],
            "to_account_id": account["id"],
            "amount": 10.0,
            "date": "2026-01-01",
            "title": "invalid",
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_transfer_to_unknown_account_is_404(client, register_and_login):
    headers = register_and_login("alice")
    space, _, account = _space_person_account(client, headers)

    response = client.post(
        f"/split/accounts/{account['id']}/transfers",
        json={
            "space_id": space["id"],
            "to_account_id": 999,
            "amount": 10.0,
            "date": "2026-01-01",
            "title": "invalid",
        },
        headers=headers,
    )
    assert response.status_code == 404


def test_deleting_one_transfer_leg_deletes_both(client, register_and_login):
    headers = register_and_login("alice")
    space, person, checking = _space_person_account(client, headers, name="Grace")
    savings = client.post(
        "/split/accounts",
        json={"name": "Grace's savings", "person_id": person["id"]},
        headers=headers,
    ).json()

    transfer = client.post(
        f"/split/accounts/{checking['id']}/transfers",
        json={
            "space_id": space["id"],
            "to_account_id": savings["id"],
            "amount": 100.0,
            "date": "2026-01-01",
            "title": "Sparen",
        },
        headers=headers,
    ).json()

    out_id = transfer["out_transaction"]["id"]
    in_id = transfer["in_transaction"]["id"]

    response = client.delete(f"/split/transactions/{out_id}", headers=headers)
    assert response.status_code == 204

    assert (
        client.get(f"/split/transactions/{out_id}", headers=headers).status_code == 404
    )
    assert (
        client.get(f"/split/transactions/{in_id}", headers=headers).status_code == 404
    )

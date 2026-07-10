def _household_with_two_people(client, headers):
    space = client.post("/split/spaces", json={"name": "Household"}, headers=headers).json()

    def _add_person(name):
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
        return person, account

    grace, grace_account = _add_person("Grace")
    frank, frank_account = _add_person("Frank")
    return space, (grace, grace_account), (frank, frank_account)


def _add_split_transaction(client, headers, space, payer_account, other_account, total=50.0):
    transaction = client.post(
        "/split/transactions",
        json={"space_id": space["id"], "title": "Groceries", "date": "2026-01-01"},
        headers=headers,
    ).json()
    share = total / 2
    client.post(
        f"/split/transactions/{transaction['id']}/contributions",
        json={
            "account_id": payer_account["id"],
            "transaction_id": transaction["id"],
            "amount_requested": share,
            "amount_paid": total,
            "is_initial": True,
        },
        headers=headers,
    )
    client.post(
        f"/split/transactions/{transaction['id']}/contributions",
        json={
            "account_id": other_account["id"],
            "transaction_id": transaction["id"],
            "amount_requested": share,
            "amount_paid": 0.0,
            "is_initial": False,
        },
        headers=headers,
    )
    return transaction


def test_transaction_detail_embeds_contributions_with_person_names(
    client, register_and_login
):
    headers = register_and_login("alice")
    space, (grace, grace_account), (frank, frank_account) = _household_with_two_people(
        client, headers
    )
    transaction = _add_split_transaction(
        client, headers, space, grace_account, frank_account
    )

    response = client.get(f"/split/transactions/{transaction['id']}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Groceries"
    names = {c["person_name"] for c in body["contributions"]}
    assert names == {"Grace", "Frank"}
    grace_contribution = next(
        c for c in body["contributions"] if c["person_name"] == "Grace"
    )
    assert grace_contribution["amount_paid"] == 50.0
    assert grace_contribution["amount_requested"] == 25.0


def test_space_balances_reflect_who_owes_whom(client, register_and_login):
    headers = register_and_login("alice")
    space, (grace, grace_account), (frank, frank_account) = _household_with_two_people(
        client, headers
    )
    _add_split_transaction(client, headers, space, grace_account, frank_account, total=50.0)

    response = client.get(f"/split/spaces/{space['id']}/balances", headers=headers)
    assert response.status_code == 200
    balances = {b["name"]: b["net_balance"] for b in response.json()}
    assert balances == {"Grace": 25.0, "Frank": -25.0}


def test_space_overview_contains_users_persons_and_recent_transactions(
    client, register_and_login
):
    headers = register_and_login("alice")
    space, (grace, grace_account), (frank, frank_account) = _household_with_two_people(
        client, headers
    )
    _add_split_transaction(client, headers, space, grace_account, frank_account)

    response = client.get(f"/split/spaces/{space['id']}/overview", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert [u["username"] for u in body["users"]] == ["alice"]
    assert {p["name"] for p in body["persons"]} == {"Grace", "Frank"}
    assert body["transaction_count"] == 1
    assert [t["title"] for t in body["recent_transactions"]] == ["Groceries"]


def test_person_summary_returns_balance_and_accounts(client, register_and_login):
    headers = register_and_login("alice")
    space, (grace, grace_account), (frank, frank_account) = _household_with_two_people(
        client, headers
    )
    _add_split_transaction(client, headers, space, grace_account, frank_account)

    response = client.get(f"/split/persons/{grace['id']}/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Grace"
    assert body["net_balance"] == 25.0
    assert body["transaction_count"] == 1
    assert [a["id"] for a in body["accounts"]] == [grace_account["id"]]


def test_spaces_list_includes_member_and_transaction_counts(client, register_and_login):
    headers = register_and_login("alice")
    space, (grace, grace_account), (frank, frank_account) = _household_with_two_people(
        client, headers
    )
    _add_split_transaction(client, headers, space, grace_account, frank_account)

    response = client.get("/split/spaces", headers=headers)
    assert response.status_code == 200
    [summary] = response.json()
    assert summary["id"] == space["id"]
    assert summary["member_count"] == 1
    assert summary["transaction_count"] == 1

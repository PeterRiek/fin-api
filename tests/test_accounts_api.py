def _owned_person(client, headers, name="Grace"):
    space = client.post(
        "/split/spaces", json={"name": "Household"}, headers=headers
    ).json()
    person = client.post("/split/persons", json={"name": name}, headers=headers).json()
    client.post(
        f"/split/spaces/{space['id']}/persons",
        params={"person_id": person["id"]},
        headers=headers,
    )
    return person


def test_create_account_requires_owned_person(client, register_and_login):
    headers = register_and_login("alice")
    person = _owned_person(client, headers)

    response = client.post(
        "/split/accounts",
        json={"name": "Grace's checking", "person_id": person["id"]},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["person_id"] == person["id"]


def test_create_account_for_unowned_person_is_forbidden(client, register_and_login):
    alice_headers = register_and_login("alice")
    person = _owned_person(client, alice_headers)

    bob_headers = register_and_login("bob")
    response = client.post(
        "/split/accounts",
        json={"name": "hijacked", "person_id": person["id"]},
        headers=bob_headers,
    )
    assert response.status_code == 403


def test_list_get_update_delete_account(client, register_and_login):
    headers = register_and_login("alice")
    person = _owned_person(client, headers)
    account = client.post(
        "/split/accounts",
        json={"name": "checking", "person_id": person["id"]},
        headers=headers,
    ).json()

    assert [a["id"] for a in client.get("/split/accounts", headers=headers).json()] == [
        account["id"]
    ]
    assert (
        client.get(f"/split/accounts/{account['id']}", headers=headers).status_code
        == 200
    )

    response = client.put(
        f"/split/accounts/{account['id']}",
        json={"name": "savings", "person_id": person["id"]},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "savings"

    response = client.delete(f"/split/accounts/{account['id']}", headers=headers)
    assert response.status_code == 204
    assert (
        client.get(f"/split/accounts/{account['id']}", headers=headers).status_code
        == 404
    )


def test_account_not_visible_to_unrelated_user(client, register_and_login):
    alice_headers = register_and_login("alice")
    person = _owned_person(client, alice_headers)
    account = client.post(
        "/split/accounts",
        json={"name": "checking", "person_id": person["id"]},
        headers=alice_headers,
    ).json()

    bob_headers = register_and_login("bob")
    assert (
        client.get(f"/split/accounts/{account['id']}", headers=bob_headers).status_code
        == 404
    )

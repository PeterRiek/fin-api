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

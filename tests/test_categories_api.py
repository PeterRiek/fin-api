def test_create_category_requires_auth(client):
    response = client.post("/split/categories", json={"name": "Groceries"})
    assert response.status_code == 401


def test_list_get_update_delete_category(client, register_and_login):
    headers = register_and_login("alice")
    category = client.post(
        "/split/categories", json={"name": "Groceries"}, headers=headers
    ).json()

    assert [
        c["id"] for c in client.get("/split/categories", headers=headers).json()
    ] == [category["id"]]
    assert (
        client.get(f"/split/categories/{category['id']}", headers=headers).status_code
        == 200
    )

    response = client.put(
        f"/split/categories/{category['id']}",
        json={"name": "Rent"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Rent"

    response = client.delete(f"/split/categories/{category['id']}", headers=headers)
    assert response.status_code == 204
    assert (
        client.get(f"/split/categories/{category['id']}", headers=headers).status_code
        == 404
    )


def test_get_unknown_category_is_404(client, register_and_login):
    headers = register_and_login("alice")
    assert client.get("/split/categories/999", headers=headers).status_code == 404

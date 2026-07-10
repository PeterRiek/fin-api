from app.security import hash_password, verify_password


def test_hash_password_is_not_plaintext():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert "$" in hashed


def test_hash_password_is_salted():
    first = hash_password("same-password")
    second = hash_password("same-password")
    assert first != second


def test_verify_password_accepts_correct_password():
    hashed = hash_password("swordfish")
    assert verify_password("swordfish", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("swordfish")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_rejects_malformed_hash():
    assert verify_password("swordfish", "not-a-valid-hash") is False

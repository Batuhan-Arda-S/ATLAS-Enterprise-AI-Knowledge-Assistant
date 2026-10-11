from app.core.security import hash_password,verify_password

def test_hash_password_does_not_return_plain_password():
    password="secret123"

    hashed_password=hash_password(password)

    assert password != hashed_password


def test_verify_password_returns_true_for_correct_password():
    password="secret123"
    hashed_password=hash_password(password)

    result =verify_password(password,hashed_password)

    assert result is True

def test_verify_password_returns_false_for_wrong_password():
    password="secret123"
    hashed_password=hash_password(password)

    result =verify_password("wrong-password",hashed_password)

    assert result is False

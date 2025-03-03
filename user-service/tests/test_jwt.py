from ..user_service import generate_jwt, decode_jwt
import jwt
import datetime


def test_generate_and_decode_jwt():
    user_id = "test-user-id"
    token = generate_jwt(user_id)
    payload = decode_jwt(token)
    assert payload["user_id"] == user_id


def test_expired_jwt():
    expired_token = jwt.encode({
        "user_id": "test-user-id",
        "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    }, 'test-secret-key', algorithm='HS256')
    assert decode_jwt(expired_token) is None


def test_invalid_jwt():
    assert decode_jwt("invalid-token") is None

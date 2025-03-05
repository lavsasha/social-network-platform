from unittest.mock import patch, MagicMock
import pytest
import jwt
from ..user_service import app, User, generate_jwt, decode_jwt


@pytest.fixture
def client(app_context):
    with app.test_client() as client:
        yield client


@pytest.fixture
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_db(app_context):
    with patch('user_service.db.session.add') as mock_add, \
            patch('user_service.db.session.commit') as mock_commit, \
            patch('user_service.db.session.delete') as mock_delete, \
            patch('user_service.User.query') as mock_user_query, \
            patch('user_service.UserProfile.query') as mock_profile_query, \
            patch('user_service.UserRole.query') as mock_role_query:
        yield {
            "mock_add": mock_add,
            "mock_commit": mock_commit,
            "mock_delete": mock_delete,
            "mock_user_query": mock_user_query,
            "mock_profile_query": mock_profile_query,
            "mock_role_query": mock_role_query,
        }


def test_register_user_success(mock_db):
    mock_db["mock_user_query"].filter_by.return_value.first.return_value = None
    response = app.test_client().post('/register', json={
        "login": "john_doe",
        "password": "Password123!",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    })

    assert response.status_code == 201
    assert response.json == {"message": "User registered successfully."}


def test_register_user_duplicate_login(mock_db):
    mock_user = MagicMock()
    mock_user.first.return_value = User(login="john_doe")
    mock_db["mock_user_query"].filter_by.return_value = mock_user

    response = app.test_client().post('/register', json={
        "login": "john_doe",
        "password": "Password123!",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    })

    assert response.status_code == 400
    assert response.json == {"message": "Login is already taken."}


def test_login_user_invalid_password(mock_db):
    mock_user = MagicMock()
    mock_user.first.return_value = User(
        user_id="123",
        login="john_doe",
        hashed_password="hashed_password",
        is_active=True
    )
    mock_db["mock_user_query"].filter_by.return_value = mock_user

    with patch('user_service.check_password_hash', return_value=False):
        response = app.test_client().post('/login', json={
            "login": "john_doe",
            "password": "WrongPassword!"
        })

    assert response.status_code == 401
    assert response.json == {"message": "Invalid credentials."}


def test_login_user_not_found(mock_db):
    mock_db["mock_user_query"].filter_by.return_value.first.return_value = None

    response = app.test_client().post('/login', json={
        "login": "non_existent_user",
        "password": "Password123!"
    })

    assert response.status_code == 401
    assert response.json == {"message": "Invalid credentials."}


@patch('user_service.jwt.encode')
def test_generate_jwt(mock_encode):
    user_id = "123"
    mock_encode.return_value = "mocked_token"
    token = generate_jwt(user_id)
    assert token == "mocked_token"


@patch('user_service.jwt.decode')
def test_decode_jwt_valid_token(mock_decode):
    user_id = "123"
    mock_decode.return_value = {"user_id": user_id, "exp": 1234567890}
    payload = decode_jwt("valid_token")
    assert payload["user_id"] == user_id


@patch('user_service.jwt.decode')
def test_decode_jwt_expired_token(mock_decode):
    mock_decode.side_effect = jwt.ExpiredSignatureError
    payload = decode_jwt("expired_token")
    assert payload is None


@patch('user_service.jwt.decode')
def test_decode_jwt_invalid_token(mock_decode):
    mock_decode.side_effect = jwt.InvalidTokenError
    payload = decode_jwt("invalid_token")
    assert payload is None


def test_get_profile_missing_token(client):
    response = client.get('/profile')
    assert response.status_code == 401
    assert response.json == {"message": "Token is missing."}


@patch('user_service.decode_jwt')
def test_get_profile_invalid_token(mock_decode, client):
    mock_decode.return_value = None
    response = client.get('/profile', headers={"Authorization": "invalid_token"})
    assert response.status_code == 401
    assert response.json == {"message": "Invalid or expired token."}

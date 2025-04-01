import pytest
import jwt
from datetime import datetime, timedelta
from ..app import app


def pytest_configure():
    pytest.marker_dependency = pytest.mark.dependency


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.mark.dependency()
def test_register_api(client):
    response = client.post('/register', json={
        "login": "john_2005",
        "password": "J0hnD03!2025",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe"
    })

    assert response.json == {"message": "User registered successfully."}
    assert response.status_code == 201

    response = client.post('/register', json={
        "login": "john_2005",
        "password": "J0hnSm5!2025",
        "email": "john.smith@example.com",
        "first_name": "John",
        "last_name": "Smith"
    })
    assert response.status_code == 400
    assert response.json == {"message": "Login is already taken."}

    response = client.post('/register', json={
        "login": "john_doe",
        "password": "J0hnD06!2025",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe"
    })
    assert response.status_code == 400
    assert response.json == {"message": "Email is already registered."}


@pytest.mark.dependency(depends=["test_register_api"])
def test_login_api(client):
    login_response = client.post('/login', json={
        "login": "john_2005",
        "password": "J0hnD03!2025"
    })
    assert login_response.status_code == 200
    assert login_response.json == {
        "token": login_response.json["token"],
        "message": "User successfully authenticated!"
    }
    token = login_response.json["token"]
    assert client.get('/profile', headers={"Authorization": token}).json['first_name'] == "John"

    login_response = client.post('/login', json={
        "login": "john_doue",
        "password": "J0hnD03!2025"
    })
    assert login_response.status_code == 401
    assert login_response.json == {"message": "Invalid credentials."}


@pytest.mark.dependency(depends=["test_login_api"])
def test_profile_api(client):
    login_response = client.post('/login', json={
        "login": "john_2005",
        "password": "J0hnD03!2025"
    })
    token = login_response.json["token"]

    update_response = client.put('/profile', headers={"Authorization": token}, json={
        "first_name": "George",
        "profile": {
            "avatar_url": "http://example.com/avatar.jpg",
            "about_me": "I'm keen on football."
        }
    })
    assert update_response.status_code == 200
    assert update_response.json == {"message": "Profile updated successfully."}
    assert client.get('/profile', headers={"Authorization": token}).json['first_name'] == "George"

    update_response = client.put('/profile', headers={"Authorization": token}, json={
        "login": "george_doe",
        "password": "Je0rgD03!2025"
    })
    assert update_response.status_code == 400
    assert update_response.json == {"message": "Updating login or password is not allowed."}
    assert client.get('/profile', headers={"Authorization": token}).json['login'] == "john_2005"


def test_token_is_missing(client):
    response = client.get('/profile')
    assert response.status_code == 401
    assert response.json == {"message": "Token is missing."}


def test_invalid_or_expired_token(client):
    invalid_token = "invalid_token"
    response = client.get('/profile', headers={"Authorization": invalid_token})
    assert response.status_code == 401
    assert response.json == {"message": "Invalid or expired token."}
    expired_token = jwt.encode({
        "user_id": "john_2005",
        "exp": datetime.utcnow() - timedelta(hours=1)
    }, app.config['JWT_SECRET'], algorithm='HS256')
    response = client.get('/profile', headers={"Authorization": expired_token})
    assert response.status_code == 401
    assert response.json == {"message": "Invalid or expired token."}


def test_user_not_found(client):
    non_existent_user_token = jwt.encode({
        "user_id": "alice",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }, app.config['JWT_SECRET'], algorithm='HS256')
    response = client.get('/profile', headers={"Authorization": non_existent_user_token})
    assert response.status_code == 404
    assert response.json == {"message": "User not found."}


@pytest.mark.dependency()
def test_register_with_weak_password(client):
    response = client.post('/register', json={
        "login": "alice_wonderland",
        "password": "weak",
        "email": "alice.wonderland@example.com",
        "first_name": "Alice",
        "last_name": "Wonderland",
        "date_of_birth": "1986-03-05"
    })
    assert response.status_code == 400
    assert response.json == {"message": "Password must be at least 8 characters long."}


@pytest.mark.dependency()
def test_register_with_invalid_email(client):
    response = client.post('/register', json={
        "login": "bob_marley",
        "password": "Str0ngP@ssword",
        "email": "invalid-email",
        "first_name": "Bob",
        "last_name": "Marley",
        "date_of_birth": "1996-02-10"
    })
    assert response.status_code == 400
    assert response.json == {"message": "Invalid email format."}


@pytest.mark.dependency()
def test_register_with_invalid_name(client):
    response = client.post('/register', json={
        "login": "diana_princess",
        "password": "Str0ngP@ssword",
        "email": "diana.princess@example.com",
        "first_name": "Diana123",
        "last_name": "Princess",
        "date_of_birth": "1993-09-08"
    })
    assert response.status_code == 400
    assert response.json == {"message": "Name can only contain letters, hyphens, and apostrophes."}


@pytest.mark.dependency(depends=["test_login_api"])
def test_update_profile_with_invalid_date_of_birth(client):
    response = client.post('/register', json={
        "login": "charliee_chaplin",
        "password": "Str0ngP@ssword",
        "email": "charliee.chaplin@example.com",
        "first_name": "Charliee",
        "last_name": "Chaplin",
    })
    assert response.status_code == 201

    login_response = client.post('/login', json={
        "login": "charliee_chaplin",
        "password": "Str0ngP@ssword"
    })
    assert login_response.status_code == 200
    token = login_response.json["token"]

    update_response = client.put('/profile', headers={"Authorization": token}, json={
        "profile": {
            "date_of_birth": "2125-04-16"
        }
    })
    assert update_response.status_code == 400
    assert update_response.json == {"message": "Date of birth cannot be in the future."}


@pytest.mark.dependency(depends=["test_login_api"])
def test_update_profile_with_invalid_phone_number(client):
    response = client.post('/register', json={
        "login": "edward_sciissorhands",
        "password": "Str0ngP@ssword",
        "email": "edward.sciissorhands@example.com",
        "first_name": "Edward",
        "last_name": "Sciissorhands"
    })
    assert response.status_code == 201

    login_response = client.post('/login', json={
        "login": "edward_sciissorhands",
        "password": "Str0ngP@ssword"
    })
    assert login_response.status_code == 200
    token = login_response.json["token"]
    update_response = client.put('/profile', headers={"Authorization": token}, json={
        "profile": {
            "phone_number": "123"
        }
    })
    assert update_response.status_code == 400
    assert update_response.json == {"message": "Phone number must contain 10 to 15 digits."}


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    yield
    app.config['TESTING'] = False

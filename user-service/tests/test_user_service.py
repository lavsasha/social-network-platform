import pytest
from ..user_service import app, db, User, UserProfile, UserRole
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


@pytest.fixture
def test_user(client):
    user = User(
        user_id="test-id",
        role_id="test-role-id",
        login="testuser",
        email="test@example.com",
        hashed_password=generate_password_hash("testpass"),
        first_name="Test",
        last_name="User"
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_register_user(client):
    response = client.post('/register', json={
        "login": "testuser",
        "password": "testpass",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    })
    assert response.status_code == 201
    assert response.json == {"message": "User registered successfully."}

    response = client.post('/register', json={
        "login": "testuser",
        "password": "testpass",
        "email": "test2@example.com",
        "first_name": "Test",
        "last_name": "User"
    })
    assert response.status_code == 400
    assert response.json == {"message": "Login is already taken."}

    response = client.post('/register', json={
        "login": "testuser2",
        "password": "testpass",
        "email": "invalid-email",
        "first_name": "Test",
        "last_name": "User"
    })
    assert response.status_code == 400
    assert response.json == {"message": "Email is already registered."}


def test_update_profile(client, test_user):
    login_response = client.post('/login', json={
        "login": "testuser",
        "password": "testpass"
    })
    token = login_response.json["token"]

    update_response = client.put('/profile', headers={"Authorization": token}, json={
        "first_name": "Updated",
        "profile": {
            "avatar_url": "http://example.com/avatar.jpg",
            "about_me": "Updated about me"
        }
    })
    assert update_response.status_code == 200
    assert update_response.json == {"message": "Profile updated successfully"}

    update_response = client.put('/profile', headers={"Authorization": token}, json={
        "login": "newlogin",
        "password": "newpassword"
    })
    assert update_response.status_code == 400
    assert update_response.json == {"message": "Updating login or password is not allowed"}

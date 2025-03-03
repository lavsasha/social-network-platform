import pytest
from ..user_service import app, db, User, UserProfile, UserRole
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET'] = 'test-secret-key'

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

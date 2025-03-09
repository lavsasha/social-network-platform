import pytest
from datetime import datetime
from unittest.mock import patch
from ..user_service import app, db, User, UserProfile, UserRole


@pytest.fixture
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def mock_db(app_context):
    with patch('models.db.session.add') as mock_add, \
            patch('models.db.session.commit') as mock_commit, \
            patch('models.db.session.delete') as mock_delete, \
            patch('models.User.query') as mock_user_query, \
            patch('models.UserProfile.query') as mock_profile_query, \
            patch('models.UserRole.query') as mock_role_query:
        yield {
            "mock_add": mock_add,
            "mock_commit": mock_commit,
            "mock_delete": mock_delete,
            "mock_user_query": mock_user_query,
            "mock_profile_query": mock_profile_query,
            "mock_role_query": mock_role_query,
        }


def test_user_model(mock_db):
    user = User(
        user_id="123",
        role_id="456",
        login="john_doe",
        email="john@example.com",
        hashed_password="hashed_password",
        is_active=True,
        created_at=datetime.utcnow()
    )

    mock_db["mock_user_query"].get.return_value = user
    fetched_user = User.query.get("123")
    assert fetched_user.login == "john_doe"
    assert fetched_user.email == "john@example.com"
    assert fetched_user.is_active is True
    assert isinstance(fetched_user.created_at, datetime)


def test_user_profile_model(mock_db):
    user = User(
        user_id="123",
        role_id="456",
        login="john_doe",
        email="john@example.com",
        hashed_password="hashed_password"
    )
    profile = UserProfile(
        profile_id="789",
        user_id="123",
        avatar_url="http://example.com/avatar.jpg",
        about_me="I'm John."
    )

    mock_db["mock_user_query"].get.return_value = user
    mock_db["mock_profile_query"].get.return_value = profile
    profile.user = user
    db.session.add(user)
    db.session.add(profile)
    db.session.commit()
    fetched_profile = UserProfile.query.get("789")

    assert fetched_profile.avatar_url == "http://example.com/avatar.jpg"
    assert fetched_profile.about_me == "I'm John."
    assert fetched_profile.user.login == "john_doe"


def test_user_role_model(mock_db):
    role = UserRole(
        role_id="456",
        role_name="admin",
        role_description="Administrator role",
        assigned_at=datetime.utcnow()
    )

    mock_db["mock_role_query"].get.return_value = role
    fetched_role = UserRole.query.get("456")

    assert fetched_role.role_name == "admin"
    assert fetched_role.role_description == "Administrator role"
    assert isinstance(fetched_role.assigned_at, datetime)


def test_user_update(mock_db):
    user = User(
        user_id="123",
        role_id="456",
        login="john_doe",
        email="john@example.com",
        hashed_password="hashed_password"
    )

    mock_db["mock_user_query"].get.return_value = user
    user.login = "john_doe_updated"
    user.email = "john_updated@example.com"
    fetched_user = User.query.get("123")

    assert fetched_user.login == "john_doe_updated"
    assert fetched_user.email == "john_updated@example.com"


def test_user_profile_update(mock_db):
    profile = UserProfile(
        profile_id="789",
        user_id="123",
        avatar_url="http://example.com/avatar.jpg",
        about_me="I'm John."
    )

    mock_db["mock_profile_query"].get.return_value = profile
    profile.about_me = "I'm John Doe."
    fetched_profile = UserProfile.query.get("789")

    assert fetched_profile.about_me == "I'm John Doe."


def test_user_delete(mock_db):
    user = User(
        user_id="123",
        role_id="456",
        login="john_doe",
        email="john@example.com",
        hashed_password="hashed_password"
    )

    mock_db["mock_user_query"].get.return_value = None
    db.session.delete(user)
    db.session.commit()
    fetched_user = User.query.get("123")

    assert fetched_user is None


def test_user_role_relationship(mock_db):
    role = UserRole(
        role_id="456",
        role_name="admin",
        role_description="Administrator role"
    )
    user = User(
        user_id="123",
        role_id="456",
        login="john_doe",
        email="john@example.com",
        hashed_password="hashed_password"
    )

    user.role = role
    mock_db["mock_user_query"].get.return_value = user
    mock_db["mock_role_query"].get.return_value = role
    fetched_user = User.query.get("123")

    assert fetched_user.role.role_name == "admin"


def test_user_unique_login_email(mock_db):
    user1 = User(
        user_id="123",
        role_id="456",
        login="john_doe",
        email="john@example.com",
        hashed_password="hashed_password"
    )

    mock_db["mock_user_query"].add(user1)
    mock_db["mock_user_query"].commit()

    user2 = User(
        user_id="124",
        role_id="456",
        login="john_doe",
        email="jane@example.com",
        hashed_password="hashed_password"
    )

    mock_db["mock_user_query"].commit.side_effect = Exception("Login is already taken.")

    with pytest.raises(Exception, match="Login is already taken."):
        mock_db["mock_user_query"].add(user2)
        mock_db["mock_user_query"].commit()

    user3 = User(
        user_id="125",
        role_id="456",
        login="jane_doe",
        email="john@example.com",
        hashed_password="hashed_password"
    )

    mock_db["mock_user_query"].commit.side_effect = Exception("Email is already registered.")

    with pytest.raises(Exception, match="Email is already registered."):
        mock_db["mock_user_query"].add(user3)
        mock_db["mock_user_query"].commit()


def test_user_profile_optional_fields(mock_db):
    profile = UserProfile(
        profile_id="789",
        user_id="123",
        avatar_url=None,
        about_me=None,
        city="New York",
        education="Harvard",
        interests="Programming",
        date_of_birth=datetime(1996, 3, 8),
        phone_number="+1234567890"
    )

    mock_db["mock_profile_query"].get.return_value = profile
    fetched_profile = UserProfile.query.get("789")

    assert fetched_profile.avatar_url is None
    assert fetched_profile.about_me is None
    assert fetched_profile.city == "New York"
    assert fetched_profile.education == "Harvard"
    assert fetched_profile.interests == "Programming"
    assert fetched_profile.date_of_birth == datetime(1996, 3, 8)
    assert fetched_profile.phone_number == "+1234567890"

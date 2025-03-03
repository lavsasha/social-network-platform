from ..user_service import db, User, UserProfile, UserRole
from datetime import datetime


def test_user_model():
    user = User(
        user_id="test-id",
        role_id="test-role-id",
        login="testuser",
        email="test@example.com",
        hashed_password="hashedpass",
        first_name="Test",
        last_name="User"
    )
    assert user.login == "testuser"
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"


def test_user_profile_model():
    profile = UserProfile(
        profile_id="test-profile-id",
        user_id="test-id",
        avatar_url="http://example.com/avatar.jpg",
        about_me="About me",
        city="Test City",
        education="Test Education",
        interests="Test Interests",
        date_of_birth=datetime.utcnow(),
        phone_number="1234567890"
    )
    assert profile.avatar_url == "http://example.com/avatar.jpg"
    assert profile.phone_number == "1234567890"

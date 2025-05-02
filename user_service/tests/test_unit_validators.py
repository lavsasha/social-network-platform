import pytest
from ..validators.validators import (
    validate_email_format, validate_date_of_birth, validate_name,
    validate_phone_number, validate_login, validate_password, validate_city
)


def test_validate_email_format():
    assert validate_email_format("test@example.com") == (True, "")
    assert validate_email_format("invalid-email") == (False, "Invalid email format.")


def test_validate_date_of_birth():
    assert validate_date_of_birth("1990-01-01") == (True, "")
    assert validate_date_of_birth("3023-01-01") == (False, "Date of birth cannot be in the future.")
    assert validate_date_of_birth("invalid-date") == (False, "Invalid date format. Use YYYY-MM-DD.")


def test_validate_name():
    assert validate_name("John") == (True, "")
    assert validate_name("John123") == (False, "Name can only contain letters, hyphens, and apostrophes.")


def test_validate_phone_number():
    assert validate_phone_number("+1234567890") == (True, "")
    assert validate_phone_number("123") == (False, "Phone number must contain 10 to 15 digits.")
    assert validate_phone_number("invalid-phone") == (False, "Invalid phone number format.")


def test_validate_login():
    assert validate_login("john_doe") == (True, "")
    assert validate_login("jo") == (False,
                                    "Login can only contain letters, numbers, underscores, and hyphens, and must be between 3 and 20 characters long.")


def test_validate_password():
    assert validate_password("Password123!") == (True, "")
    assert validate_password("weak") == (False, "Password must be at least 8 characters long.")
    assert validate_password("password") == (False, "Password must contain at least one uppercase letter.")
    assert validate_password("Password") == (False, "Password must contain at least one digit.")
    assert validate_password("Password123") == (False, "Password must contain at least one special character.")


def test_validate_city():
    assert validate_city("New York") == (True, "")
    assert validate_city("New York 123") == (False, "City name can only contain letters, spaces, and hyphens.")

import re
from datetime import datetime
from email_validator import validate_email, EmailNotValidError


def validate_email_format(email):
    try:
        validate_email(email, check_deliverability=False)
        return True, ""
    except EmailNotValidError as e:
        return False, "Invalid email format."


def validate_date_of_birth(date_str):
    try:
        date_of_birth = datetime.fromisoformat(date_str)
        if date_of_birth > datetime.now():
            return False, "Date of birth cannot be in the future."
        return True, ""
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD."


def validate_name(name):
    if not re.match(r"^[A-Za-z'-]+$", name):
        return False, "Name can only contain letters, hyphens, and apostrophes."
    return True, ""


def validate_phone_number(phone_number):
    if not re.match(r"^\+?[0-9\s-]*(?:\([0-9]{3,4}\))?[0-9\s-]*$", phone_number):
        return False, "Invalid phone number format."
    digits_only = re.sub(r"[^0-9]", "", phone_number)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False, "Phone number must contain 10 to 15 digits."
    return True, ""


def validate_login(login):
    if not re.match(r"^[A-Za-z0-9_-]{3,20}$", login):
        return False, "Login can only contain letters, numbers, underscores, and hyphens, and must be between 3 and 20 characters long."
    return True, ""


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""


def validate_city(city):
    if not re.match(r"^[A-Za-z\s-]+$", city):
        return False, "City name can only contain letters, spaces, and hyphens."
    return True, ""

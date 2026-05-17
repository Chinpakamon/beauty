import re

def validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("The password must be at least 8 characters long")
    if len(value) > 128:
        raise ValueError("The password is too long")

    if not re.search(r"[A-Z]", value):
        raise ValueError("The password must contain a capital letter")

    if not re.search(r"[a-z]", value):
        raise ValueError("The password must contain a lowercase letter")

    if not re.search(r"\d", value):
        raise ValueError("The password must contain a number")

    return value

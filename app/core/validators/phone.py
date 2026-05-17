import re

PHONE_REGEX = re.compile(r"^7\d{10}$")


def validate_phone_number(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    if len(value) > 20:
        raise ValueError("The phone number is too long")

    digits = re.sub(r"\D", "", value)

    if len(digits) != 11:
        raise ValueError("The number must contain 11 digits")

    if digits.startswith("8"):
        digits = "7" + digits[1:]

    if not PHONE_REGEX.match(digits):
        raise ValueError("Incorrect phone number")

    return digits

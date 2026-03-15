from __future__ import annotations


def validate_au_email(value: str) -> tuple[bool, str]:
    """Validate an AU student email local-part and normalize it."""
    normalized = value.strip().lower()
    if not normalized:
        return False, ""
    if len(normalized) == 8 and normalized.startswith("au") and normalized[2:].isdigit():
        return True, f"{normalized}@uni.au.dk"
    return False, "Must be au + 6 digits"


def validate_password(password: str, confirm: str) -> tuple[bool, str]:
    """Validate password length and confirmation state."""
    if not password:
        return False, ""
    if len(password) < 4:
        return False, "Too short"
    if password != confirm:
        return False, "Passwords don't match"
    if len(password) >= 8:
        return True, "Strong"
    return True, "OK"


def validate_package_selection(selected: list[str]) -> tuple[bool, str]:
    """Validate that at least one interest package is selected."""
    if not selected:
        return False, "Select at least one topic"
    return True, f"{len(selected)} selected"


def validate_keyword_weight(weight: int) -> tuple[bool, str]:
    """Validate a keyword weight and map it to a label."""
    if weight < 0 or weight > 10:
        return False, "Weight must be 0-10"
    if weight <= 2:
        return True, "loosely follow"
    if weight <= 5:
        return True, "interested"
    if weight <= 8:
        return True, "main interest"
    return True, "everything"

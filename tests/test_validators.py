from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from setup.validators import (
    validate_au_email,
    validate_keyword_weight,
    validate_package_selection,
    validate_password,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("au612345", (True, "au612345@uni.au.dk")),
        ("AU612345", (True, "au612345@uni.au.dk")),
        (" au612345 ", (True, "au612345@uni.au.dk")),
        ("au12345", (False, "Must be au + 6 digits")),
        ("au1234567", (False, "Must be au + 6 digits")),
        ("xx612345", (False, "Must be au + 6 digits")),
        ("au61234x", (False, "Must be au + 6 digits")),
        ("", (False, "")),
    ],
)
def test_validate_au_email(value: str, expected: tuple[bool, str]) -> None:
    assert validate_au_email(value) == expected


@pytest.mark.parametrize(
    ("password", "confirm", "expected"),
    [
        ("", "", (False, "")),
        ("abc", "abc", (False, "Too short")),
        ("abcd", "abcx", (False, "Passwords don't match")),
        ("abcd", "abcd", (True, "OK")),
        ("abcdefgh", "abcdefgh", (True, "Strong")),
    ],
)
def test_validate_password(
    password: str, confirm: str, expected: tuple[bool, str]
) -> None:
    assert validate_password(password, confirm) == expected


@pytest.mark.parametrize(
    ("selected", "expected"),
    [
        ([], (False, "Select at least one topic")),
        (["Stars"], (True, "1 selected")),
        (["Stars", "Exoplanets"], (True, "2 selected")),
    ],
)
def test_validate_package_selection(
    selected: list[str], expected: tuple[bool, str]
) -> None:
    assert validate_package_selection(selected) == expected


@pytest.mark.parametrize(
    ("weight", "expected"),
    [
        (-1, (False, "Weight must be 0-10")),
        (11, (False, "Weight must be 0-10")),
        (0, (True, "loosely follow")),
        (5, (True, "interested")),
        (7, (True, "main interest")),
        (10, (True, "everything")),
    ],
)
def test_validate_keyword_weight(weight: int, expected: tuple[bool, str]) -> None:
    assert validate_keyword_weight(weight) == expected

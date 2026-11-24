"""Unit tests for the arithmetic functions and schema validation (no database)."""
import pytest
from pydantic import ValidationError

from app.operations import compute
from app.schemas import CalculationCreate, UserCreate
from app.security import create_access_token, decode_access_token, hash_password, verify_password


@pytest.mark.parametrize(
    "t,a,b,expected",
    [("add", 1, 2, 3), ("subtract", 1, 2, -1), ("multiply", -2, 3, -6), ("divide", 9, 3, 3)],
)
def test_compute(t, a, b, expected):
    assert compute(t, a, b) == expected


def test_compute_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        compute("divide", 1, 0)


def test_calculation_create_rejects_divide_by_zero():
    with pytest.raises(ValidationError):
        CalculationCreate(type="divide", a=1, b=0)


def test_user_create_rejects_weak_password():
    with pytest.raises(ValidationError):
        UserCreate(username="alice", email="a@example.com", password="password")


def test_password_hashing_roundtrip():
    h = hash_password("Secret123")
    assert h != "Secret123"
    assert verify_password("Secret123", h)
    assert not verify_password("wrong", h)


def test_token_roundtrip():
    assert decode_access_token(create_access_token(42)) == 42
    assert decode_access_token("not.a.token") is None

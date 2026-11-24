"""Integration tests for calculation BREAD endpoints."""
import pytest
from sqlalchemy import select

from app.models import Calculation
from tests.conftest import login_headers, register


def create(client, headers, type_="add", a=10, b=5):
    return client.post("/calculations", json={"type": type_, "a": a, "b": b}, headers=headers)


@pytest.mark.parametrize(
    "type_,a,b,expected",
    [("add", 10, 5, 15), ("subtract", 10, 5, 5), ("multiply", 10, 5, 50), ("divide", 10, 4, 2.5)],
)
def test_add_calculation_computes_result(client, auth_headers, type_, a, b, expected):
    r = create(client, auth_headers, type_, a, b)
    assert r.status_code == 201
    body = r.json()
    assert body["type"] == type_
    assert body["result"] == expected
    assert body["user_id"] == 1


def test_full_bread_lifecycle(client, auth_headers, db_session):
    # Add
    created = create(client, auth_headers, "add", 2, 3).json()
    calc_id = created["id"]
    assert created["result"] == 5

    # Read
    r = client.get(f"/calculations/{calc_id}", headers=auth_headers)
    assert r.status_code == 200 and r.json()["result"] == 5

    # Browse
    create(client, auth_headers, "multiply", 4, 5)
    r = client.get("/calculations", headers=auth_headers)
    assert r.status_code == 200
    assert [c["id"] for c in r.json()] == [calc_id, calc_id + 1]

    # Edit (PUT) - result is recomputed
    r = client.put(f"/calculations/{calc_id}", json={"type": "multiply", "a": 6, "b": 7},
                   headers=auth_headers)
    assert r.status_code == 200 and r.json()["result"] == 42

    # Edit (PATCH) - partial update
    r = client.patch(f"/calculations/{calc_id}", json={"b": 10}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["b"] == 10 and r.json()["result"] == 60

    # The database reflects the edit
    row = db_session.get(Calculation, calc_id)
    assert (row.type, row.a, row.b, row.result) == ("multiply", 6, 10, 60)

    # Delete
    assert client.delete(f"/calculations/{calc_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/calculations/{calc_id}", headers=auth_headers).status_code == 404
    db_session.expire_all()
    assert db_session.scalar(select(Calculation).where(Calculation.id == calc_id)) is None


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "divide", "a": 1, "b": 0},      # divide by zero
        {"type": "power", "a": 2, "b": 3},       # unknown operation
        {"type": "add", "a": "abc", "b": 3},     # not a number
        {"type": "add", "a": 1},                 # missing b
        {},                                      # empty body
    ],
)
def test_add_invalid_data_returns_422(client, auth_headers, payload):
    r = client.post("/calculations", json=payload, headers=auth_headers)
    assert r.status_code == 422
    assert "detail" in r.json()


def test_edit_to_divide_by_zero_returns_422(client, auth_headers):
    calc_id = create(client, auth_headers, "divide", 10, 2).json()["id"]
    r = client.patch(f"/calculations/{calc_id}", json={"b": 0}, headers=auth_headers)
    assert r.status_code == 422
    # Original row is unchanged
    assert client.get(f"/calculations/{calc_id}", headers=auth_headers).json()["result"] == 5


def test_edit_with_empty_body_returns_422(client, auth_headers):
    calc_id = create(client, auth_headers).json()["id"]
    assert client.patch(f"/calculations/{calc_id}", json={}, headers=auth_headers).status_code == 422


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_missing_calculation_returns_404(client, auth_headers, method):
    kwargs = {"json": {"a": 1}} if method in ("put", "patch") else {}
    r = getattr(client, method)("/calculations/9999", headers=auth_headers, **kwargs)
    assert r.status_code == 404


def test_endpoints_require_authentication(client):
    assert client.get("/calculations").status_code == 401
    assert client.post("/calculations", json={"type": "add", "a": 1, "b": 2}).status_code == 401
    assert client.get("/calculations/1").status_code == 401
    assert client.delete("/calculations/1").status_code == 401


def test_users_cannot_access_each_others_calculations(client, auth_headers):
    calc_id = create(client, auth_headers).json()["id"]

    register(client, username="bob", email="bob@example.com")
    bob = login_headers(client, "bob")

    assert client.get("/calculations", headers=bob).json() == []
    assert client.get(f"/calculations/{calc_id}", headers=bob).status_code == 404
    assert client.patch(f"/calculations/{calc_id}", json={"a": 1}, headers=bob).status_code == 404
    assert client.delete(f"/calculations/{calc_id}", headers=bob).status_code == 404
    # Alice still has it
    assert client.get(f"/calculations/{calc_id}", headers=auth_headers).status_code == 200

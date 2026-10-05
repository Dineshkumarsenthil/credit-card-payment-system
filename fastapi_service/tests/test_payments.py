"""FastAPI payment service tests (run from the fastapi_service folder).

    pip install pytest httpx
    python -m pytest -v
"""
import os

os.environ["JWT_SECRET_KEY"] = "test-secret"  # must be set before the app is imported

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base, Card

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=engine)
client = TestClient(app)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def auth(user_id=1, kind="access"):
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode(
        {"user_id": user_id, "token_type": kind, "exp": exp},
        "test-secret",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr("app.main.time.sleep", lambda s: None)  # skip the 1s delay
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        db.add(Card(id=1, user_id=1, expiry_month=12, expiry_year=2035))   # valid card
        db.add(Card(id=2, user_id=1, expiry_month=1, expiry_year=2020))    # expired card
        db.commit()
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(engine)


def pay(card_id=1, amount="250.50", headers=None):
    return client.post(
        "/payments",
        json={"card_id": card_id, "amount": amount},
        headers=auth() if headers is None else headers,
    )


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_payment_requires_token():
    r = client.post("/payments", json={"card_id": 1, "amount": "10"})
    assert r.status_code in (401, 403)


def test_refresh_token_is_rejected():
    assert pay(headers=auth(kind="refresh")).status_code == 401


def test_other_users_card_returns_404():
    assert pay(headers=auth(user_id=2)).status_code == 404


def test_unknown_card_returns_404():
    assert pay(card_id=999).status_code == 404


def test_expired_card_is_rejected():
    assert pay(card_id=2).status_code == 400


@pytest.mark.parametrize("amount", ["0", "-5", "1000001", "abc"])
def test_invalid_amount_returns_422(amount):
    assert pay(amount=amount).status_code == 422


def test_payment_success(monkeypatch):
    monkeypatch.setattr("app.main.random.random", lambda: 0.0)
    r = pay()
    assert r.status_code == 201
    assert r.json()["status"] == "SUCCESS"


def test_payment_failed_has_reason(monkeypatch):
    monkeypatch.setattr("app.main.random.random", lambda: 0.99)
    r = pay()
    assert r.status_code == 201
    assert r.json()["status"] == "FAILED"
    assert r.json()["failure_reason"]


def test_list_returns_only_own_payments(monkeypatch):
    monkeypatch.setattr("app.main.random.random", lambda: 0.0)
    pay()
    pay()
    assert len(client.get("/payments", headers=auth()).json()) == 2
    assert client.get("/payments", headers=auth(user_id=2)).json() == []
"""A fake payment provider (httpx MockTransport) and an app wired to it."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_client, get_store
from app.payments.client import PaymentClient
from app.payments.idempotency import IdempotencyStore


class FakeProvider:
    """Charges succeed unless the source is "tok_declined"; deduplicates on Idempotency-Key."""

    def __init__(self):
        self.charges: dict[str, dict] = {}
        self.by_key: dict[str, str] = {}
        self.requests: list[httpx.Request] = []
        self.fail_next: list[Exception | int] = []  # queued transport errors or status codes

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.fail_next:
            failure = self.fail_next.pop(0)
            if isinstance(failure, Exception):
                raise failure
            return httpx.Response(failure, json={"error": {"message": "unavailable"}})
        if request.method == "POST" and request.url.path.endswith("/charges"):
            body = json.loads(request.content)
            key = request.headers["Idempotency-Key"]
            if body["source"] == "tok_declined":
                return httpx.Response(
                    402, json={"error": {"code": "card_declined", "message": "Card declined"}}
                )
            if key not in self.by_key:
                charge_id = f"ch_{len(self.charges) + 1}"
                self.charges[charge_id] = {
                    "id": charge_id,
                    "status": "succeeded",
                    "amount": body["amount"],
                    "currency": body["currency"],
                }
                self.by_key[key] = charge_id
            return httpx.Response(200, json=self.charges[self.by_key[key]])
        if request.method == "GET":
            charge = self.charges.get(request.url.path.rsplit("/", 1)[-1])
            return httpx.Response(200, json=charge) if charge else httpx.Response(404)
        return httpx.Response(405)


@pytest.fixture(autouse=True)
def no_backoff_sleep(monkeypatch):
    monkeypatch.setattr("app.payments.client.time.sleep", lambda s: None)


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def payment_client(provider) -> PaymentClient:
    return PaymentClient(
        "https://api.provider.test/v1", "sk_test", transport=httpx.MockTransport(provider.handler)
    )


@pytest.fixture
def api(payment_client):
    store = IdempotencyStore()
    app.dependency_overrides[get_client] = lambda: payment_client
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

import httpx
import pytest

from app.payments.client import ChargeNotFound, ProviderDeclined, ProviderError


def test_create_charge_sends_the_idempotency_key(payment_client, provider):
    charge = payment_client.create_charge(
        amount=500, currency="usd", source="tok_visa", idempotency_key="key-123456"
    )
    assert charge.status == "succeeded"
    assert provider.requests[0].headers["Idempotency-Key"] == "key-123456"
    assert provider.requests[0].headers["Authorization"] == "Bearer sk_test"


def test_decline_raises_provider_declined(payment_client):
    with pytest.raises(ProviderDeclined) as exc:
        payment_client.create_charge(
            amount=500, currency="usd", source="tok_declined", idempotency_key="key-123456"
        )
    assert exc.value.code == "card_declined"


def test_timeout_raises_provider_error(payment_client, provider):
    provider.fail_next = [httpx.ReadTimeout("slow")]
    with pytest.raises(ProviderError):
        payment_client.create_charge(
            amount=500, currency="usd", source="tok_visa", idempotency_key="key-123456"
        )


def test_get_unknown_charge(payment_client):
    with pytest.raises(ChargeNotFound):
        payment_client.get_charge("ch_nope")

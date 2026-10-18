import httpx
import pytest

from app.payments.client import (
    CHARGE_MAX_ATTEMPTS,
    ChargeNotFound,
    ProviderDeclined,
    ProviderError,
)


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


def test_timeout_is_retried_with_the_same_key(payment_client, provider):
    provider.fail_next = [httpx.ReadTimeout("slow"), 503]
    charge = payment_client.create_charge(
        amount=500, currency="usd", source="tok_visa", idempotency_key="key-123456"
    )
    assert charge.status == "succeeded" and len(provider.requests) == 3
    assert {r.headers["Idempotency-Key"] for r in provider.requests} == {"key-123456"}


def test_gives_up_after_max_attempts(payment_client, provider):
    provider.fail_next = [httpx.ReadTimeout("slow")] * CHARGE_MAX_ATTEMPTS
    with pytest.raises(ProviderError):
        payment_client.create_charge(
            amount=500, currency="usd", source="tok_visa", idempotency_key="key-123456"
        )
    assert len(provider.requests) == CHARGE_MAX_ATTEMPTS


def test_client_errors_are_not_retried(payment_client, provider):
    provider.fail_next = [400]
    with pytest.raises(ProviderError):
        payment_client.create_charge(
            amount=500, currency="usd", source="tok_visa", idempotency_key="key-123456"
        )
    assert len(provider.requests) == 1


def test_get_unknown_charge(payment_client):
    with pytest.raises(ChargeNotFound):
        payment_client.get_charge("ch_nope")

import pytest

from app.payments.idempotency import (
    IDEMPOTENCY_KEY_TTL_SECONDS,
    IdempotencyConflict,
    IdempotencyStore,
    fingerprint,
)


class Clock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


def test_fingerprint_ignores_key_order():
    assert fingerprint({"a": 1, "b": 2}) == fingerprint({"b": 2, "a": 1})


def test_stored_response_is_returned_until_it_expires():
    clock = Clock()
    store = IdempotencyStore(clock)
    store.put("k", "h", 201, {"id": "ch_1"})
    clock.now += IDEMPOTENCY_KEY_TTL_SECONDS - 1
    assert store.get("k", "h").body == {"id": "ch_1"}
    clock.now += 2
    assert store.get("k", "h") is None and len(store) == 0


def test_conflicting_body_raises():
    store = IdempotencyStore(Clock())
    store.put("k", "h1", 201, {})
    with pytest.raises(IdempotencyConflict):
        store.get("k", "h2")


def test_purge_expired():
    clock = Clock()
    store = IdempotencyStore(clock)
    store.put("old", "h", 201, {})
    clock.now += IDEMPOTENCY_KEY_TTL_SECONDS + 1
    store.put("new", "h", 201, {})
    assert store.purge_expired() == 1 and len(store) == 1

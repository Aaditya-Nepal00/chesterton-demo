"""Idempotency keys for POST /payments.

The first response for a key is stored and replayed for any later request with the same
key and body. The same key with a different body is a client bug and is rejected.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

IDEMPOTENCY_KEY_TTL_SECONDS = 24 * 60 * 60


class IdempotencyConflict(Exception):
    """The key was already used for a request with a different body."""


@dataclass(frozen=True)
class StoredResponse:
    request_hash: str
    status_code: int
    body: dict
    stored_at: float


def fingerprint(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class IdempotencyStore:
    """In-process store. Each instance behind the load balancer has its own; the provider
    also deduplicates on the key, so a request that lands on the other instance still
    produces one charge."""

    def __init__(self, clock: Callable[[], float] = time.time):
        self._clock = clock
        self._items: dict[str, StoredResponse] = {}
        self._lock = threading.Lock()

    def get(self, key: str, request_hash: str) -> StoredResponse | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            if self._clock() - item.stored_at > IDEMPOTENCY_KEY_TTL_SECONDS:
                del self._items[key]
                return None
            if item.request_hash != request_hash:
                raise IdempotencyConflict(key)
            return item

    def put(self, key: str, request_hash: str, status_code: int, body: dict) -> None:
        with self._lock:
            self._items[key] = StoredResponse(request_hash, status_code, body, self._clock())

    def purge_expired(self) -> int:
        now = self._clock()
        with self._lock:
            expired = [
                k for k, v in self._items.items() if now - v.stored_at > IDEMPOTENCY_KEY_TTL_SECONDS
            ]
            for k in expired:
                del self._items[k]
        return len(expired)

    def __len__(self) -> int:
        return len(self._items)

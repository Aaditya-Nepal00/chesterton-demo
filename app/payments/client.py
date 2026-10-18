"""Client for the payment provider's charge API."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

CHARGE_TIMEOUT_SECONDS = 4
CHARGE_MAX_ATTEMPTS = 3
CHARGE_BACKOFF_SECONDS = 0.5


class ProviderError(Exception):
    """The provider could not be reached or failed; the charge may not have happened."""


class ProviderDeclined(ProviderError):
    """The provider answered and refused the charge (card declined)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ChargeNotFound(ProviderError):
    pass


@dataclass(frozen=True)
class Charge:
    id: str
    status: str
    amount: int
    currency: str


def _charge(data: dict) -> Charge:
    return Charge(
        id=data["id"], status=data["status"], amount=data["amount"], currency=data["currency"]
    )


class PaymentClient:
    def __init__(
        self, base_url: str, api_key: str, *, transport: httpx.BaseTransport | None = None
    ):
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=CHARGE_TIMEOUT_SECONDS,
            transport=transport,
        )

    def close(self) -> None:
        self._http.close()

    def create_charge(
        self, *, amount: int, currency: str, source: str, idempotency_key: str
    ) -> Charge:
        """Charge `source`. The provider deduplicates on `idempotency_key`.

        Timeouts, connection errors and 5xx are retried with the same key.
        """
        error = ProviderError("no attempt made")
        for attempt in range(1, CHARGE_MAX_ATTEMPTS + 1):
            try:
                resp = self._http.post(
                    "/charges",
                    json={"amount": amount, "currency": currency, "source": source},
                    headers={"Idempotency-Key": idempotency_key},
                )
            except httpx.TransportError as exc:
                log.warning("charge request failed: %s (attempt %d)", exc, attempt)
                error = ProviderError(f"provider unreachable: {type(exc).__name__}")
            else:
                if resp.status_code == 402:
                    err = resp.json().get("error", {})
                    raise ProviderDeclined(err.get("code", "card_declined"), err.get("message", ""))
                if resp.status_code < 400:
                    return _charge(resp.json())
                if resp.status_code < 500:
                    raise ProviderError(f"provider returned HTTP {resp.status_code}")
                log.warning("provider returned %s (attempt %d)", resp.status_code, attempt)
                error = ProviderError(f"provider returned HTTP {resp.status_code}")
            if attempt < CHARGE_MAX_ATTEMPTS:
                time.sleep(CHARGE_BACKOFF_SECONDS * attempt)
        raise error

    def get_charge(self, charge_id: str) -> Charge:
        try:
            resp = self._http.get(f"/charges/{charge_id}")
        except httpx.TransportError as exc:
            raise ProviderError(f"provider unreachable: {type(exc).__name__}") from exc
        if resp.status_code == 404:
            raise ChargeNotFound(charge_id)
        if resp.status_code >= 400:
            raise ProviderError(f"provider returned HTTP {resp.status_code}")
        return _charge(resp.json())

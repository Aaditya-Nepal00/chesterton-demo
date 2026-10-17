"""Client for the payment provider's charge API."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

CHARGE_TIMEOUT_SECONDS = 30


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
        """Charge `source`. The provider deduplicates on `idempotency_key`."""
        try:
            resp = self._http.post(
                "/charges",
                json={"amount": amount, "currency": currency, "source": source},
                headers={"Idempotency-Key": idempotency_key},
            )
        except httpx.TransportError as exc:
            log.warning("charge request failed: %s", exc)
            raise ProviderError(f"provider unreachable: {type(exc).__name__}") from exc
        if resp.status_code == 402:
            err = resp.json().get("error", {})
            raise ProviderDeclined(err.get("code", "card_declined"), err.get("message", ""))
        if resp.status_code >= 400:
            raise ProviderError(f"provider returned HTTP {resp.status_code}")
        return _charge(resp.json())

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

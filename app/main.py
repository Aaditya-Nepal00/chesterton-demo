"""Payments API used by the checkout."""

from __future__ import annotations

import os
from functools import lru_cache

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.payments import webhook
from app.payments.client import ChargeNotFound, PaymentClient, ProviderDeclined, ProviderError
from app.payments.idempotency import IdempotencyConflict, IdempotencyStore, fingerprint

app = FastAPI(title="chesterton-demo payments")


class PaymentRequest(BaseModel):
    amount: int = Field(gt=0, description="Amount in minor units (cents).")
    currency: str = Field(min_length=3, max_length=3)
    source: str = Field(min_length=1, description="Card token from the checkout.")
    merchant_webhook_url: str | None = None


class Payment(BaseModel):
    id: str
    status: str
    amount: int
    currency: str


@lru_cache
def get_client() -> PaymentClient:
    return PaymentClient(
        os.environ.get("PROVIDER_BASE_URL", "https://api.provider.test/v1"),
        os.environ["PROVIDER_API_KEY"],
    )


_store = IdempotencyStore()


def get_store() -> IdempotencyStore:
    return _store


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/payments", status_code=201, response_model=Payment)
def create_payment(
    body: PaymentRequest,
    background: BackgroundTasks,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=255),
    client: PaymentClient = Depends(get_client),
    store: IdempotencyStore = Depends(get_store),
):
    request_hash = fingerprint(body.model_dump())
    try:
        replay = store.get(idempotency_key, request_hash)
    except IdempotencyConflict:
        raise HTTPException(422, "Idempotency-Key was already used with a different body") from None
    if replay is not None:
        return JSONResponse(
            replay.body, status_code=replay.status_code, headers={"Idempotent-Replayed": "true"}
        )

    try:
        charge = client.create_charge(
            amount=body.amount,
            currency=body.currency.lower(),
            source=body.source,
            idempotency_key=idempotency_key,
        )
    except ProviderDeclined as exc:
        declined = {"error": {"code": exc.code, "message": str(exc)}}
        store.put(idempotency_key, request_hash, 402, declined)
        return JSONResponse(declined, status_code=402)
    except ProviderError:
        # Not stored: the client retries with the same key and we try the provider again.
        raise HTTPException(502, "payment provider unavailable") from None

    payment = Payment(
        id=charge.id, status=charge.status, amount=charge.amount, currency=charge.currency
    ).model_dump()
    store.put(idempotency_key, request_hash, 201, payment)
    if body.merchant_webhook_url:
        background.add_task(
            webhook.deliver,
            body.merchant_webhook_url,
            {"type": "payment.succeeded", "data": payment},
        )
    return payment


@app.get("/payments/{payment_id}", response_model=Payment)
def get_payment(payment_id: str, client: PaymentClient = Depends(get_client)):
    try:
        charge = client.get_charge(payment_id)
    except ChargeNotFound:
        raise HTTPException(404, "payment not found") from None
    except ProviderError:
        raise HTTPException(502, "payment provider unavailable") from None
    return Payment(
        id=charge.id, status=charge.status, amount=charge.amount, currency=charge.currency
    )

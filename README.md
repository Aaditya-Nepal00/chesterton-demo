# chesterton-demo: payments service

A small payments API used by the checkout. It takes a card token from the checkout,
charges it through the payment provider, and tells the merchant about the result with a
signed webhook.

```
checkout ──POST /payments──▶ payments API ──POST /charges──▶ payment provider
                                  │
                                  └── payment.succeeded webhook ──▶ merchant endpoint
```

## API

| Method | Path | What it does |
|---|---|---|
| `POST` | `/payments` | Charge a card. Requires an `Idempotency-Key` header. |
| `GET` | `/payments/{id}` | Read a payment back from the provider. |
| `GET` | `/healthz` | Liveness check. |

`POST /payments` body:

```json
{"amount": 1999, "currency": "usd", "source": "tok_visa", "merchant_webhook_url": "https://merchant.example/hooks"}
```

`amount` is in minor units (cents). A successful charge returns `201` with the payment;
a declined card returns `402`; a provider outage returns `502` and nothing is stored, so
the same request can be retried.

## Idempotency

Every `POST /payments` must carry an `Idempotency-Key`. The first response for a key is
stored (`app/payments/idempotency.py`) and replayed for any later request with the same
key and the same body, with the header `Idempotent-Replayed: true`. The same key with a
different body is rejected with `422`. The key is also forwarded to the provider, so two
concurrent requests with one key still produce a single charge.

## Clients

The checkout web and mobile apps queue a payment that fails with a network error or a
`5xx` and retry it with the **same** `Idempotency-Key` for up to **48 hours** (the mobile
app keeps the queue while the device is offline).

## Deployment

Two instances behind the load balancer. The load balancer cuts any request that takes
longer than **15 seconds** and returns `504` to the client, even if the handler is still
running.

Merchant webhooks (`app/payments/webhook.py`) are delivered after the response is sent,
in the same worker process (a FastAPI background task); there is no separate queue yet.
See `decisions/0001-webhook-retry-cap-of-3.md`.

## Configuration

| Variable | Default | |
|---|---|---|
| `PROVIDER_BASE_URL` | `https://api.provider.test/v1` | Payment provider API |
| `PROVIDER_API_KEY` | (required) | Secret key for the provider |

## Develop

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
PROVIDER_API_KEY=test uvicorn app.main:app --reload
```

## Decisions

Why things are the way they are lives in [`decisions/`](decisions/). Chesterton asks the
author of a merged PR about choices that have no written reason and records the answer
there; a later PR that touches one of those lines gets the reason as a comment.
Decisions are recorded by Chesterton.

from app.payments import webhook

BODY = {"amount": 1999, "currency": "USD", "source": "tok_visa"}
KEY = {"Idempotency-Key": "order-1001-attempt"}


def test_create_and_read_payment(api, provider):
    resp = api.post("/payments", json=BODY, headers=KEY)
    assert resp.status_code == 201
    payment = resp.json()
    assert payment["status"] == "succeeded" and payment["currency"] == "usd"
    assert provider.requests[0].headers["Idempotency-Key"] == KEY["Idempotency-Key"]
    assert api.get(f"/payments/{payment['id']}").json() == payment


def test_same_key_replays_the_first_response(api, provider):
    first = api.post("/payments", json=BODY, headers=KEY)
    second = api.post("/payments", json=BODY, headers=KEY)
    assert second.json() == first.json()
    assert second.headers["Idempotent-Replayed"] == "true"
    assert len(provider.requests) == 1


def test_same_key_with_another_body_is_rejected(api):
    api.post("/payments", json=BODY, headers=KEY)
    resp = api.post("/payments", json={**BODY, "amount": 2999}, headers=KEY)
    assert resp.status_code == 422


def test_missing_key_is_rejected(api):
    assert api.post("/payments", json=BODY).status_code == 422


def test_declined_card_is_402_and_replayed(api, provider):
    body = {**BODY, "source": "tok_declined"}
    assert api.post("/payments", json=body, headers=KEY).status_code == 402
    assert api.post("/payments", json=body, headers=KEY).status_code == 402
    assert len(provider.requests) == 1


def test_provider_outage_is_502_and_not_stored(api, provider):
    provider.fail_next = [503]
    assert api.post("/payments", json=BODY, headers=KEY).status_code == 502
    assert api.post("/payments", json=BODY, headers=KEY).status_code == 201


def test_unknown_payment_is_404(api):
    assert api.get("/payments/ch_missing").status_code == 404


def test_webhook_is_sent_after_a_successful_charge(api, monkeypatch):
    sent = []
    monkeypatch.setattr(webhook, "deliver", lambda url, event: sent.append((url, event)))
    body = {**BODY, "merchant_webhook_url": "https://merchant.example/hooks"}
    payment = api.post("/payments", json=body, headers=KEY).json()
    assert sent == [
        ("https://merchant.example/hooks", {"type": "payment.succeeded", "data": payment})
    ]


def test_healthz(api):
    assert api.get("/healthz").json() == {"status": "ok"}

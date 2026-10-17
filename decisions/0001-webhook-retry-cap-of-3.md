---
id: "0001"
title: "Webhook retry cap of 3"
status: recorded
owner: "@Aaditya-Nepal00"
paths:
  - "app/payments/webhook.py"
symbols:
  - "WEBHOOK_MAX_RETRIES"
source_pr: "https://github.com/Aaditya-Nepal00/chesterton-demo/pull/1"
answer_url: "https://github.com/Aaditya-Nepal00/chesterton-demo/pull/1#issuecomment-6233259860"
recorded: 2026-10-17
---

# 0001. Webhook retry cap of 3

## Decision

WEBHOOK_MAX_RETRIES is set to 3 for payment webhook delivery attempts in app/payments/webhook.py.

## Why

> Delivery runs inline in the payment worker, so 3 attempts caps how long a dead merchant endpoint can block a worker to about a minute.

— @Aaditya-Nepal00, [answer on #1](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/1#issuecomment-6233259860)

Delivery runs inline in the payment worker, so capping retries at three prevents dead merchant endpoints from blocking worker execution for more than a minute.

## Safe to change when

Once delivery moves to the background queue.

## Evidence

- Source PR: [#1 Add payment webhook delivery](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/1)
- Change: [`app/payments/webhook.py:10`](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/1/files#diff-8d0f1791f001875b7d59fc79bb079608ad7bd15f7c37bcc0b79f499ed1801cb6R10)
- Answer: [comment by @Aaditya-Nepal00](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/1#issuecomment-6233259860)
- Question asked: Why `WEBHOOK_MAX_RETRIES = 3` in `app/payments/webhook.py`? When would it be safe to change?

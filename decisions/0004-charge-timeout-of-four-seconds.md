---
id: "0004"
title: "Charge timeout of four seconds"
status: recorded
owner: "@Aaditya-Nepal00"
paths:
  - "app/payments/client.py"
symbols:
  - "CHARGE_TIMEOUT_SECONDS"
source_pr: "https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7"
answer_url: "https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617"
recorded: 2026-10-18
---

# 0004. Charge timeout of four seconds

## Decision

CHARGE_TIMEOUT_SECONDS in app/payments/client.py is set to 4 seconds.

## Why

> The load balancer cuts requests at 15s, so a 30s provider call got a 504 at the checkout while the charge still went through; 3 tries × 4s plus 1.5s backoff is 13.5s and fits.

— @Aaditya-Nepal00, [answer on #7](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617)

Constraints:
- load balancer cuts requests at 15s

## Alternatives considered

- 30s provider call

## Safe to change when

only if the load balancer timeout goes up

## Evidence

- Source PR: [#7 Retry provider charge calls and keep idempotency keys for 72h](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7)
- Change: [`app/payments/client.py:13`](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7/files#diff-d3d4f26ec3fbe6a4a28d5323b1440613947428b9caea8cc23212bdfa20bd0e17R13)
- Answer: [comment by @Aaditya-Nepal00](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617)
- Question asked: Why `CHARGE_TIMEOUT_SECONDS = 4`? When would it be safe to change?

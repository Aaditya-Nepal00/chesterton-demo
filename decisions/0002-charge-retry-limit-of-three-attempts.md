---
id: "0002"
title: "Charge retry limit of three attempts"
status: recorded
owner: "@Aaditya-Nepal00"
paths:
  - "app/payments/client.py"
symbols:
  - "CHARGE_MAX_ATTEMPTS"
source_pr: "https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7"
answer_url: "https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617"
recorded: 2026-10-18
---

# 0002. Charge retry limit of three attempts

## Decision

CHARGE_MAX_ATTEMPTS is set to 3 in app/payments/client.py.

## Why

> Retrying is safe because every attempt sends the same Idempotency-Key and the provider deduplicates on it, and 3 is the most attempts that fit under the 15s load balancer cutoff with a 4s timeout.

— @Aaditya-Nepal00, [answer on #7](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617)

Constraints:
- 15s load balancer cutoff

## Safe to change when

if attempts × timeout + backoff stays under 15s

## Evidence

- Source PR: [#7 Retry provider charge calls and keep idempotency keys for 72h](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7)
- Change: [`app/payments/client.py:14`](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7/files#diff-d3d4f26ec3fbe6a4a28d5323b1440613947428b9caea8cc23212bdfa20bd0e17R14)
- Answer: [comment by @Aaditya-Nepal00](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617)
- Question asked: Why `CHARGE_MAX_ATTEMPTS = 3` in `app/payments/client.py`? When would it be safe to change?

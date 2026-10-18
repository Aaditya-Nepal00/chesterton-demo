---
id: "0003"
title: "Idempotency key TTL of 72 hours"
status: recorded
owner: "@Aaditya-Nepal00"
paths:
  - "app/payments/idempotency.py"
symbols:
  - "IDEMPOTENCY_KEY_TTL_SECONDS"
source_pr: "https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7"
answer_url: "https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617"
recorded: 2026-10-18
---

# 0003. Idempotency key TTL of 72 hours

## Decision

IDEMPOTENCY_KEY_TTL_SECONDS is set to 72 hours in app/payments/idempotency.py.

## Why

> The checkout apps retry a failed payment with the same Idempotency-Key for up to 48 hours, so with 24h a late retry from an offline phone could charge twice; 72h covers that with a day of margin.

— @Aaditya-Nepal00, [answer on #7](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617)

Constraints:
- checkout apps retry for up to 48 hours

## Alternatives considered

- 24h

## Safe to change when

only if the client retry window gets shorter

## Evidence

- Source PR: [#7 Retry provider charge calls and keep idempotency keys for 72h](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7)
- Change: [`app/payments/idempotency.py:16`](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7/files#diff-8cc9d126a1053f6819c6cf7244293fe28cc0087af55ac99c436346f8d04d9798R16)
- Answer: [comment by @Aaditya-Nepal00](https://github.com/Aaditya-Nepal00/chesterton-demo/pull/7#issuecomment-6249828617)
- Question asked: Why `IDEMPOTENCY_KEY_TTL_SECONDS = 72 * 60 * 60`? When would it be safe to change?

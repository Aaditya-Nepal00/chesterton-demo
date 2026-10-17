"""Outbound payment webhooks: deliver payment events to merchant endpoints."""

import logging
import time

import httpx

log = logging.getLogger(__name__)

WEBHOOK_MAX_RETRIES = 5
WEBHOOK_TIMEOUT_SECONDS = 15
WEBHOOK_BACKOFF_SECONDS = 2


def deliver(url: str, event: dict) -> bool:
    """POST one payment event to a merchant endpoint, retrying on failure."""
    for attempt in range(1, WEBHOOK_MAX_RETRIES + 1):
        try:
            resp = httpx.post(url, json=event, timeout=WEBHOOK_TIMEOUT_SECONDS)
            if resp.status_code < 500:
                return resp.is_success
            log.warning("webhook %s returned %s (attempt %d)", url, resp.status_code, attempt)
        except httpx.TransportError as exc:
            log.warning("webhook %s failed: %s (attempt %d)", url, exc, attempt)
        time.sleep(WEBHOOK_BACKOFF_SECONDS * attempt)
    return False

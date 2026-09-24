# Event lifecycle

Reliable Webhook API separates receipt, processing, and retry state so callers can inspect what happened to an event without relying on transient worker logs.

```text
signed request
    |
    v
 received
    |
    v
 processing
   /   \
  v     v
processed failed
           |
           | retryable + attempts remain
           v
     retry_scheduled
           |
           v
       processing
           |
           +----> processed
           |
           +----> failed ----> dead_letter
```

## Receipt

`POST /webhooks/events` verifies the HMAC-SHA256 signature against the exact request-body bytes before accepting the event. A valid new event is persisted with status `received`. PostgreSQL uniqueness on `event_id` is the final idempotency authority.

Submitting an already stored `event_id` returns a duplicate result instead of creating a second event. Invalid signatures are rejected before persistence and never enter the retry flow.

## Processing

Processing claims an eligible event before invoking the configured processor. Attempts and sanitized failure metadata are persisted for operational inspection. Successful processing ends in `processed`.

## Retries

Only explicitly retryable failures may be scheduled. Retry timing uses bounded exponential backoff and the configured maximum attempt count. Due retries are claimed atomically so concurrent workers cannot both process the same claim.

`processed` and `dead_letter` are terminal states. The service does not claim exactly-once delivery across arbitrary downstream systems.

## Operational inspection

Use `GET /events/{event_id}` to inspect one event, `GET /events` to filter/paginate events, and `POST /events/{event_id}/retry` to request a retry when the current state and retry policy allow it.

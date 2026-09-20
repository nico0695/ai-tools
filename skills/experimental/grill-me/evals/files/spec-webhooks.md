# Spec: Outbound webhooks for order events

## Goal
Let merchants subscribe an HTTPS endpoint to order events (`order.created`, `order.paid`, `order.cancelled`) so their systems get notified without polling.

## Decided
- Delivery is async, via a background job queue (we already run BullMQ on Redis for emails).
- Payload is JSON with a top-level `event`, `id`, `created_at`, `data`.
- Each merchant can register up to 5 endpoints.
- Endpoints are managed from the existing merchant settings page (no new UI surface).

## Open
- Signing: probably HMAC-SHA256 with a per-endpoint secret. TBD whether we rotate secrets and how.
- Retries: for now retry on any non-2xx. Backoff schedule to be defined.
- Ordering: not guaranteed for now. Should we promise per-order ordering?
- Event history / redelivery UI: out of scope for v1, revisit later.
- Timeouts: TODO - 5s? 10s?

## Non-goals
- Inbound webhooks.
- Filtering by order attributes.

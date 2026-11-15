<!-- Backend profile. Give each lens only its own section (## structure, ## quality or ## risk), through {profile_sections}.
     For a `backend (cli)` package, prepend to each section: "This is a CLI, not a server: skip HTTP, health, shutdown and request-transaction items." -->

## structure

Backend:
- Responsibilities, not layer names: do not require controller/service/repository. Look for request
  handlers that hold business rules, data access that enforces business rules, and services that mix
  orchestration with persistence and external calls.
- Domain boundaries: modules or domains calling each other's data access directly; shared database
  tables written by several domains with no single owner in code.
- External services: SDK clients created and called throughout the code instead of behind a module
  that owns the integration.
- Background jobs and queues: job handlers duplicating logic that request handlers also implement.

## quality

Backend:
- API contracts: inconsistent response and error shapes across routes; HTTP status codes that
  contradict the outcome (200 on errors, 500 for validation failures).
- Error handling: a central error handler vs per-route ad-hoc handling; async errors that escape it.
- Transactions: multi-step writes that must succeed together performed without a transaction.
- Idempotency and retries: handlers or jobs that can run twice (retries, webhooks, queue redelivery)
  with no idempotency guard on side effects.
- Data access performance (potential unless measured): queries in loops, missing pagination,
  N+1 through ORM relations.
- Tests: business rules and error paths of central flows; integration tests that exist but were not
  executed are noted, not assumed to pass.

## risk

Backend:
- Validation and sanitization at every route and message consumer; a schema library used on some
  routes and absent on siblings.
- Authorization on data access by id (ownership checks), not only authentication.
- Timeouts on outbound HTTP and database calls; retries with backoff only where safe.
- Logging: structured logs on request and job paths, request or correlation ids when flows span
  services or jobs; sensitive data kept out of logs.
- Health and readiness endpoints and graceful shutdown when the service is deployed as a long-running
  process.
- Configuration validated at startup; required env variables documented.

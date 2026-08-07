---
template:
  id: api
  name: API Reference
  description: Documents a callable contract - endpoints, requests, responses, errors and examples - so a consumer can integrate without reading the implementation.
  audience: [API consumers, integrators, frontend developers]
  use_when:
    - documenting endpoints, an SDK surface, or a service contract
    - someone outside the owning team has to call it
    - a contract changed and consumers need the new shape
  required: [overview, base-information, authentication, endpoints, errors, summary]
  optional: [pagination, rate-limits, examples, versioning, sequence-flow]
  visuals: [sequence]
  toc: required
---

# [API name] — Reference

> [One or two lines: what this API exposes and who calls it.]

## Table of Contents

- [Overview](#overview)
- [Base Information](#base-information)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Errors](#errors)
- [Pagination](#pagination)
- [Rate Limits](#rate-limits)
- [Versioning](#versioning)
- [Summary](#summary)

## Overview

[What this API is for, what it operates on, and what it does not cover.]

## Base Information

| | |
|---|---|
| Base URL | `https://...` |
| Format | JSON |
| Encoding | UTF-8 |

## Authentication

[How a caller authenticates, where the credential goes, what happens when it is missing or expired.
Only what the sources confirm — an invented auth scheme sends integrators down a dead end.]

```http
Authorization: Bearer <token>
```

## Endpoints

| Method | Path | Purpose | Auth |
|---|---|---|---|

### `[METHOD] [/path]`

[What it does, in one line.]

**Parameters**

| Name | In | Type | Required | Description |
|---|---|---|---|---|

**Request**

```json
{}
```

**Response** `200 OK`

```json
{}
```

**Errors**

| Status | Condition |
|---|---|

[Repeat per endpoint. Every endpoint gets at least one real example — a schema without one gets the
shape right and the semantics wrong. Use real field names and realistic values; never invent a field
to make an example look complete.]

## Errors

[The error envelope shared across endpoints, plus the codes a caller must handle.]

```json
{ "error": { "code": "...", "message": "..." } }
```

| Code | Meaning | Caller action |
|---|---|---|

## Pagination

[Strategy, parameters, and how a caller knows there is more.]

## Rate Limits

[Limits, the headers that report them, and the behavior on exhaustion.]

## Versioning

[How versions are expressed, what counts as breaking, and the deprecation path.]

## Summary

[What this API exposes, the parts that need care when integrating, and where the contract is likely
to change.]

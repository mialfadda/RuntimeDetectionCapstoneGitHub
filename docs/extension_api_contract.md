# Extension ↔ Backend API Contract

Owner: A1 · Consumers: A1 (extension), A2 (dashboard), B1/B2 (test fixtures)
Scope: stable contract the browser extension and any external client uses. Breaking changes require a version bump and coordination with A1/A2.

## Base

- Base URL (dev): `http://127.0.0.1:5000`
- Base URL (prod): `https://<host>` — HTTP requests are 301-redirected.
- Content-Type: `application/json; charset=utf-8` on every request with a body.
- API version: `v1` (implicit; first breaking change introduces `/v2/...`).

## Authentication

Two modes; a request uses exactly one.

| Mode | Header | Used by |
| --- | --- | --- |
| JWT bearer | `Authorization: Bearer <access_token>` | Browser extension (interactive users) |
| API key | `X-API-Key: msk_<token>` | Headless clients, CI |

Tokens are obtained via `POST /auth/login` (JWT) or `POST /admin/api-keys` (key). Refresh flow: `POST /auth/refresh` with the refresh token. Clients MUST store the refresh token in `chrome.storage.local` (encrypted at rest by Chrome), never in `localStorage`.

## Required request headers

```
Authorization: Bearer <access_token>
Content-Type:  application/json
X-Client:      extension/<semver>            # e.g. extension/0.1.0
X-Request-Id:  <uuid v4>                     # optional; echoed back for tracing
```

## Standard response envelope

Success responses are the resource itself — no envelope. Errors always use:

```json
{ "error": "<machine_code>", "detail": "<human explanation, optional>" }
```

## Error codes

| HTTP | `error` code | Meaning |
| --- | --- | --- |
| 400 | validation errors (e.g. `"url scheme must be http or https"`) | Malformed input |
| 401 | `unauthorized`, `invalid_token`, `token_expired` | Auth missing/bad |
| 401 | `invalid credentials` | Login failure |
| 403 | `forbidden` | Role check failed |
| 404 | `not found`, `scan not found`, `report not found` | Resource missing |
| 409 | `email already registered`, `version already exists` | Conflict |
| 413 | `model file exceeds size limit` | Payload too large |
| 429 | `rate_limited` | Rate limit hit (see headers below) |
| 501 | `not_implemented` | Stubbed endpoint |

## Rate-limit headers

Flask-Limiter attaches these on every response when limits apply:

```
X-RateLimit-Limit:      60
X-RateLimit-Remaining:  57
X-RateLimit-Reset:      1776196000   # unix seconds
Retry-After:            23           # only on 429
```

Extension MUST back off when `X-RateLimit-Remaining` ≤ 1 and pause queued scans for `Retry-After` seconds on 429.

## Endpoints used by the extension

### `POST /auth/login`
Request:
```json
{ "email": "user@example.com", "password": "…" }
```
Response 200: `{ "user_id": 1, "access_token": "…", "refresh_token": "…", "role": "user" }`

### `POST /auth/refresh`
Headers: `Authorization: Bearer <refresh_token>`
Response 200: `{ "access_token": "…" }`

### `POST /auth/logout`
Revokes the access JWT. Response 200: `{ "message": "logged out" }`

### `POST /scan/analyze`
Primary detection call. Triggered on every navigation.
Limits: 60/min, 1000/hour per user.

Request (`schemas/scan_request.json`):
```json
{
  "url": "https://example.com/login",
  "source": "extension",
  "runtime_evidence": {
    "js_api_calls": ["document.write", "eval"],
    "dom_mutations": [{"type": "script_inject", "count": 2}],
    "network_requests": [{"url": "https://evil.example/beacon", "method": "POST"}],
    "timing_ms": 420.5
  }
}
```

Response 200 (`schemas/scan_result.json`):
```json
{
  "scan_id": 42,
  "url": "https://example.com/login",
  "risk_level": "medium",
  "confidence": 0.612,
  "threat_category": "phishing",
  "model_contributions": [
    {"model_name": "decision_tree", "version": "1.2.0", "score": 0.58, "confidence": 0.58},
    {"model_name": "lstm",          "version": "0.9.1", "score": 0.64, "confidence": 0.64},
    {"model_name": "svm",           "version": "1.0.0", "score": 0.61, "confidence": 0.61}
  ],
  "inference_time_ms": 137.2,
  "created_at": "2026-04-15T10:12:33.001Z"
}
```

`risk_level` ∈ `safe | low | medium | high | critical`
`threat_category` ∈ `benign | phishing | malware | defacement | spam | unknown`

### `POST /scan/batch`
Up to 50 URLs. 10/min per user. Response: `{ "results": [ScanResult | {url, error}] }`.

### `GET /explanations/{scan_id}`
Returns SHAP/LIME/LLM payload for a scan. Schema: `schemas/explanation_result.json`.

### `POST /explanations/generate`
Body: `{ "scan_id": 42 }`. Returns `ExplanationResult`.

### `GET /detections?limit=50`
User's scan history. Admin sees all.

### `GET /detections/{id}`
Single scan detail.

## Extension flow

1. **Install** → popup shows login form.
2. **Login** → `POST /auth/login`; stash `access_token` + `refresh_token` in `chrome.storage.local`.
3. **Navigation** (`chrome.webNavigation.onBeforeNavigate`) → background worker calls `POST /scan/analyze` with `{url, runtime_evidence}`. Treat `risk_level ∈ {high, critical}` as blocking: interstitial page with "proceed / go back".
4. **Token expiry** (401 `token_expired`) → call `/auth/refresh`, retry once.
5. **429** → honor `Retry-After`; surface "slow down" toast if ≥ 3 in 60 s.

## Reference schemas

Machine-readable JSON Schemas live under `docs/schemas/`:
- `scan_request.json`
- `scan_result.json`
- `explanation_result.json`
- `error.json`

The extension's TypeScript types SHOULD be generated from these via `json-schema-to-typescript` during its build (Phase II).

# IP-SAKTI Sahayak — User-Managed External Connector Credentials

## CONTEXT

External connectors (WIPO PATENTSCOPE, WIPO Pearl, and future paid sources
like Manupatra) currently authenticate using platform-wide credentials in
`.env`. This task adds a per-user flow: a logged-in user visits a
Connections/Integrations page, enters their own credentials for a given
external source, the system tests the connection and reports the specific
error if it fails, and — once connected — that user's chat sessions use
their own credentials for live lookups against that source, instead of (or
in addition to) any platform-wide default.

This does not change the connector interface built previously
(`ExternalSourceConnector.search()`/`get_status()`/`is_available()`) — it
changes WHERE credentials come from at call time: per-user stored
credentials when present, falling back to platform `.env` defaults for
sources that don't require per-user auth (e.g. PATENTSCOPE's free search).

---

## 1. DATA MODEL

New table: `user_external_connections`

```
id                  UUID PK
user_id             FK -> users.id
connector_name      str          # "wipo_patentscope" | "wipo_pearl" | ...
encrypted_credentials  bytea      # see Section 2 — NEVER plaintext
status              enum         # "connected" | "error" | "disconnected"
last_tested_at       timestamp
last_error_code      str | null   # structured error type, see Section 4
last_error_message   str | null   # human-readable, safe to show in UI
created_at / updated_at
```

One row per (user, connector) pair. A user can have zero or more active
connections.

---

## 2. CREDENTIAL ENCRYPTION — MANDATORY, NOT OPTIONAL

- Encrypt credentials at rest using a server-side master key (e.g. Fernet
  symmetric encryption via the `cryptography` library), with the master
  key itself stored in `.env`/a secrets manager, never in the database or
  code.
- Credentials are **write-only** from the API's perspective after saving:
  once stored, no endpoint should ever return the decrypted value to the
  frontend. The UI shows only a masked state ("Connected" / last 4
  characters of a key if genuinely useful for user recognition, nothing
  more).
- Decrypt only in-memory, at the moment of making the actual external API
  call, never log the decrypted value anywhere (not in request logs, not
  in error messages, not in the `last_error_message` field — sanitize
  before storing that).
- Add this to the existing `AuditLog`: log connection-added,
  connection-tested, connection-removed events (who, when, which
  connector) — never log the credential value itself in the audit trail.

---

## 3. BACKEND ENDPOINTS

`ai/src/connectors/` gets a new `credential_resolver.py`:
```python
async def resolve_credentials(user_id: str, connector_name: str) -> dict | None:
    """Returns decrypted per-user credentials if the user has an active
    connection for this connector, else None (caller falls back to
    platform .env defaults if the connector supports that)."""
```

New endpoints in `backend/app/api/v1/connectors.py`:

- `GET /api/v1/connectors` — list all available connector types
  (name, display_name, requires_api_key, is_paid, what credential fields
  it needs — e.g. PATENTSCOPE needs nothing, WIPO Pearl needs
  client_id+client_secret) plus the current user's connection status for
  each.
- `POST /api/v1/connectors/{connector_name}/test` — body contains the
  credentials to test (NOT yet saved). Calls the connector's
  `is_available()` (or a dedicated lightweight auth-check method) using
  these candidate credentials. Returns a structured result:
  ```json
  { "success": false,
    "error_code": "AUTH_FAILED",
    "error_message": "The client ID or secret was rejected by the provider." }
  ```
  Never save credentials on a failed test.
- `POST /api/v1/connectors/{connector_name}/connect` — body contains
  credentials already confirmed via `/test`; encrypts and saves them,
  sets `status: "connected"`.
- `DELETE /api/v1/connectors/{connector_name}` — removes the stored
  connection (hard delete the encrypted credential row, don't just flag
  it disconnected while retaining the secret).
- `POST /api/v1/connectors/{connector_name}/retest` — re-run the test
  against already-stored credentials (for a user checking "is my
  connection still working" without re-entering credentials), update
  `status`/`last_error_*` accordingly.

---

## 4. STRUCTURED ERROR TYPES — REQUIRED FOR "WHAT IS THE ERROR"

The connector's test/auth-check path must distinguish failure causes, not
just return a generic failure boolean:

```python
class ConnectorErrorCode(str, Enum):
    AUTH_FAILED = "auth_failed"                # bad key/secret
    NETWORK_TIMEOUT = "network_timeout"         # provider unreachable in time
    SERVICE_UNAVAILABLE = "service_unavailable" # provider returned 5xx
    RATE_LIMITED = "rate_limited"               # provider returned 429
    INVALID_CONFIG = "invalid_config"           # missing required field, malformed input
    UNKNOWN = "unknown"                         # anything not classified above — log
                                                 # full detail server-side, still return
                                                 # a generic safe message to the user
```

Each connector implementation catches its own provider-specific
exceptions/status codes and maps them to one of these, with a short,
user-safe `error_message` per code (no raw stack traces or provider
internals surfaced to the frontend).

---

## 5. FRONTEND — CONNECTIONS PAGE

New page/section: `frontend/src/app/ConnectionsPage.tsx` (or a tab within
existing Settings).

- List of available connectors as cards: name, short description of what
  it adds, and current status.
- **Not connected**: a "Connect" button opens a credential form specific
  to that connector (rendered from the field list the `GET /connectors`
  response describes — don't hardcode per-connector forms if avoidable,
  drive the form fields from the API response so adding a new connector
  later doesn't require a new frontend form).
- On submit: call `/test` first. Show a loading state, then either a
  success confirmation (with a "Save Connection" button to actually
  persist it) or the specific error message from `error_code`/
  `error_message` — e.g. "Authentication failed — check your client ID
  and secret" rather than a generic "Something went wrong."
- **Connected**: show status, `last_tested_at`, a "Test Connection" button
  (calls `/retest`), and a "Disconnect" button (calls `DELETE`, with a
  confirmation prompt).
- Never render the actual credential value anywhere after it's saved.

---

## 6. WIRING INTO CHAT

In the live-lookup dispatch logic (already built), when a connector needs
credentials:
1. Call `resolve_credentials(current_user_id, connector_name)`.
2. If present, use them for this call.
3. If absent AND the connector has a usable platform-wide `.env` default
   (e.g. free PATENTSCOPE search), fall back to that.
4. If absent AND the connector requires per-user credentials with no
   platform default (e.g. WIPO Pearl, or any paid source with no shared
   org-wide subscription) — skip that connector silently for this query
   (same graceful-degradation behavior already built), and optionally
   surface a one-time, non-blocking UI hint like "Connect WIPO Pearl in
   Settings for enriched terminology results" rather than failing or
   nagging on every message.

---

## 7. TESTING

- Encryption: confirm credentials are never retrievable in plaintext via
  any endpoint, and confirm they're actually encrypted at rest (query the
  DB directly in a test and assert the stored value isn't the plaintext
  input).
- Error classification: unit test each `ConnectorErrorCode` path with
  mocked provider responses (401 → AUTH_FAILED, timeout → NETWORK_TIMEOUT,
  500 → SERVICE_UNAVAILABLE, 429 → RATE_LIMITED).
- End-to-end: connect a test credential, confirm a chat query that needs
  that connector actually uses the per-user credential (not the platform
  default) — verify via a mock that asserts which credential value was
  passed to the outbound call.
- Regression: confirm users with NO connections configured see identical
  chat behavior to before this feature (falling back correctly, no new
  errors, no blocking UI).
- Security: confirm `last_error_message` stored for a failed auth attempt
  never contains the attempted credential value itself.

## DELIVERABLE
- `user_external_connections` table + encrypted credential storage
- `GET/POST/DELETE /api/v1/connectors...` endpoints with structured error
  codes
- Connections/Settings page with per-connector test → save → status flow
- Per-user credential resolution wired into the existing live-lookup
  dispatch, falling back to platform defaults where applicable
- Audit logging for connect/test/disconnect events (never logging secret
  values)

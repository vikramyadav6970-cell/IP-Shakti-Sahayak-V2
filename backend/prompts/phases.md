# backend/prompts/phases.md

Ready-to-paste prompts for an AI coding agent, one per task. Manual/human steps
are called out explicitly.

---

## Phase 0 — Environment & setup

### T0.1 — Dev infra: cloud-hosted (recommended) or local

**Recommended path — cloud-hosted, no local services at all:**

**Manual prerequisites (human, ~10 minutes):**
1. Create a free **Supabase** project (supabase.com) → Database → Extensions →
   enable `vector`. This gives Postgres+pgvector with zero local install.
   Copy the **Session pooler** connection string (Settings → Database) — not
   Transaction pooler mode, which doesn't support the prepared statements
   SQLAlchemy+asyncpg use by default.
2. In the same Supabase project, Storage → create a bucket (e.g. `documents`).
   This replaces MinIO/S3 for both dev and prod — no separate object storage
   service needed. Copy the S3-compatible endpoint from Settings → Storage.
3. Create a free **Upstash Redis** database (upstash.com) → copy the `rediss://`
   connection URL.

**Prompt:**
```
Read /context.md, /process.md, and /backend/coding_conventions.md in full first.

Task: Create backend/.env.example listing every var needed to connect to the
project's cloud-hosted dev infra: DATABASE_URL (Supabase Postgres, Session
pooler mode), REDIS_URL (Upstash, rediss:// scheme), and S3_ENDPOINT/
S3_ACCESS_KEY/S3_SECRET_KEY/S3_BUCKET (Supabase Storage's S3-compatible
credentials, found under Settings > Storage > S3 Access Keys in the Supabase
dashboard) — plus placeholders for vars needed later (LLM_API_KEY, JWT_SECRET),
each with a one-line comment on where a human gets that value (reference
README.md §3). Do not commit real values, only placeholders.

Write app/config.py's Settings class (this may overlap with T0.2 — if so, do
both together) to read these and fail loudly at startup with a clear message if
a required var is missing, rather than failing later with an opaque connection
error.

Since there's no local docker-compose to bring up, verify connectivity instead
by writing a small script or the /health endpoint (T0.2) that pings Postgres,
Redis, and Storage using the configured credentials, and confirm all three
succeed against the human's actual Supabase/Upstash project before moving on.

When done: update /backend/status.md (note this project uses cloud-hosted dev
infra, not local Postgres/Redis, so future agents don't assume a
docker-compose file exists) and flip T0.1 to [x] in /process.md.
```

**Local/native alternative (only if you specifically want offline dev or your
own local instances):** run Postgres 16 + the `pgvector` extension and Redis
natively (see OS-specific install notes — ask if you need these written out for
your OS), or via Docker Compose if you prefer containers. Either works with the
exact same `.env` var names above, just pointed at `localhost` instead of a
cloud host. Skip MinIO in this case too — see "Storage without MinIO" below.

**If you skip Supabase Storage too** (e.g. staying fully local): implement a
third storage backend, `LocalFilesystemStorage`, alongside the S3-compatible
one, writing to `backend/local_storage/` — the storage interface from T2.2
already calls for this to be swappable, so add this as one more implementation
rather than a special case.


### T0.2 — FastAPI project scaffold

**Prompt:**
```
Read /context.md, /process.md, and /backend/coding_conventions.md first.

Task: Scaffold the FastAPI project inside `backend/` following the exact folder
structure in backend/coding_conventions.md. Include:
- app/config.py: a pydantic-settings `Settings` class reading from `.env`, with
  every var from T0.1's .env.example represented and typed.
- app/main.py: FastAPI app instance, CORS configured for the frontend's dev origin
  (read from an env var, not hardcoded), a `/health` endpoint returning DB/Redis
  connectivity status, and the `/api/v1` router mounted (empty router is fine for
  now).
- requirements.txt / pyproject.toml pinning exact versions of every dependency
  named in coding_conventions.md's Stack section — do not add anything beyond
  that list without flagging it.
- A minimal Dockerfile for the backend service itself (separate from the infra
  compose file — this is for eventually deploying the API).

When done: update /backend/status.md and flip T0.2 to [x] in /process.md.
```

### T0.3 — Alembic setup

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Wire up Alembic against the SQLAlchemy setup from T0.2 (async engine —
confirm Alembic's async migration template is used, not the sync default). Create
and apply an initial empty migration to prove the pipeline works end to end
against the Postgres container from T0.1.

When done: update /backend/status.md and flip T0.3 to [x] in /process.md.
```

---

## Phase 1 — Data model + auth

### T1.1 — Core SQLAlchemy models

**Prompt:**
```
Read /context.md (especially §2 and §5) and /backend/coding_conventions.md first.

Task: Define SQLAlchemy models for the following entities (use UUID primary keys,
created_at/updated_at timestamps on all, and appropriate foreign keys/indexes):

- User: id, name, email (unique), hashed_password, language, organization, role
  (enum: USER/ADMIN/IP_FACILITATOR/CONTENT_MANAGER/RESEARCHER), created_at.
- Conversation: id, user_id (FK), created_at.
- Message: id, conversation_id (FK), role (user/assistant), content, jurisdiction,
  confidence_score, confidence_label, requires_human_review, created_at.
- Citation: id, message_id (FK), document_title, section_ref, source_url,
  jurisdiction, document_type.
- Document: id, title, jurisdiction, document_type (enum: STATUTE/RULE/TREATY/
  REGISTRY_RECORD/CASE_LAW/GUIDELINE), authority, language, source_url.
- DocumentVersion: id, document_id (FK), version_label, effective_from,
  object_storage_key (points to the original file in S3/MinIO), is_current (bool).
- Product: id, user_id (FK), name/description, raw ingredients (jsonb).
- Classification: id, product_id (FK), category, regulatory_pathway, rules_fired
  (jsonb — for auditability of the deterministic rules engine per context.md §2
  rule 6), created_at.
- IPAssessment: id, product_id (FK), ip_type, relevance_label, reasoning,
  legal_provisions (jsonb), created_at.
- ABSAssessment: id, product_id (FK), biological_resources (jsonb), origin,
  purpose, relevance_label, next_steps (jsonb), created_at.
- AuditLog: id, user_id (FK, nullable), action, resource_type, resource_id,
  metadata (jsonb), created_at. (This must be append-only in practice — don't
  build any update/delete path for this table.)
- Feedback: id, message_id (FK), user_id (FK), rating, comment, created_at.
- ExpertRequest: id, user_id (FK), message_id (FK, nullable), status (enum:
  OPEN/IN_PROGRESS/RESOLVED), context, created_at.

Write the corresponding Alembic migration. Add indexes on all foreign keys and on
any column that will be filtered on frequently (jurisdiction, document_type, role).

When done: update /backend/status.md with the final schema (or a link to where
it's documented) and flip T1.1 to [x] in /process.md.
```

### T1.2 — JWT auth + RBAC

**Manual prerequisite:** none, but the human must generate a strong `JWT_SECRET`
value for `.env` (not committed) — a placeholder in `.env.example` is fine.

**Prompt:**
```
Read /backend/coding_conventions.md (rule 8 — don't reinvent auth/crypto) first.

Task: Implement JWT-based authentication:
- Password hashing via passlib/bcrypt.
- `/api/v1/auth/register`, `/api/v1/auth/login` (returns access + refresh token),
  `/api/v1/auth/refresh` endpoints.
- A FastAPI dependency (`get_current_user`) that validates the JWT and loads the
  User, and a `require_role(*roles)` dependency factory for RBAC-gated endpoints.
- Rate-limit the login endpoint specifically (use Redis) to blunt brute-force
  attempts.

Write tests covering: successful register/login, wrong password rejected, expired/
invalid token rejected, role-gated endpoint rejects wrong role.

When done: update /backend/status.md with the exact request/response shape for
each auth endpoint (this is a contract the frontend depends on — see
coding_conventions.md "API contract discipline"), and flip T1.2 to [x] in
/process.md. Add a Cross-part note in /process.md so frontend knows auth is ready.
```

### T1.3 — User management endpoints

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Implement `/api/v1/users/me` (get current user profile) and
`/api/v1/users` (admin-only list, RBAC-gated to ADMIN) with pagination.

When done: update /backend/status.md with the contract shapes and flip T1.3 to
[x] in /process.md.
```

---

## Phase 2 — Documents & ingestion trigger

### T2.1 — Document metadata endpoints

**Prompt:**
```
Read /context.md §5 (known source list) and /backend/coding_conventions.md first.

Task: Implement `/api/v1/documents` (CRUD, RBAC-gated to CONTENT_MANAGER/ADMIN for
write, open read for listing/browsing — this backs the frontend's Source
Explorer) and `/api/v1/documents/{id}/versions`. Support filtering by jurisdiction
and document_type on the list endpoint, matching what frontend T4.2 needs.

When done: update /backend/status.md with the contract shape (flag clearly that
this is what Source Explorer consumes) and flip T2.1 to [x] in /process.md. Add a
Cross-part note.
```

### T2.2 — Object storage integration

**Manual prerequisite:** none for local dev (MinIO from T0.1 covers it). For
production, an AWS S3 bucket + IAM credentials scoped to that bucket only.

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Implement a storage service interface (`app/services/storage.py`) with a
single abstraction (`upload`, `get_url`, `delete`) implemented against
S3-compatible APIs (boto3), configured via env vars so MinIO (dev) and real S3
(prod) both work without code changes. Wire document upload into the
DocumentVersion creation flow from T2.1: uploading a new version stores the raw
file in object storage and records the storage key.

When done: update /backend/status.md and flip T2.2 to [x] in /process.md.
```

### T2.3 — Ingestion trigger endpoint

**Prompt:**
```
Read /context.md (build order §4 — corpus/ingestion comes before retrieval) and
/backend/coding_conventions.md first.

Task: Implement `/api/v1/documents/{version_id}/ingest` (RBAC-gated to
CONTENT_MANAGER/ADMIN), which enqueues a Celery task calling into the `ai/`
ingestion pipeline (the actual parsing/chunking/embedding logic lives in `ai/` —
see ai/prompts/phases.md Phase 1; this task is only the trigger + status tracking
on the backend side). Track ingestion status on DocumentVersion (add a status
column via migration if not already present: PENDING/PROCESSING/INDEXED/FAILED)
and expose `/api/v1/documents/{version_id}/ingest/status`.

Coordinate with whoever is doing ai/prompts/phases.md Phase 1 on the exact task
signature the Celery worker expects — document the agreed interface in both
backend/status.md and ai/status.md.

When done: update /backend/status.md and flip T2.3 to [x] in /process.md.
```

---

## Phase 3 — Chat / query API

### T3.1 — `/api/v1/chat` endpoint

**Prompt:**
```
Read /context.md §2 (hard constraints — this endpoint is where they get enforced
end-to-end) and /backend/coding_conventions.md first.

Task: Implement `POST /api/v1/chat`:
- Request: `{ question: str, jurisdiction: str, language: str, conversation_id:
  str | None }`.
- The service layer calls into the `ai/` layer's query pipeline (check
  ai/status.md for the current function signature/interface — if it's not ready
  yet, build against a documented interface and mock it, matching the pattern
  frontend used in T2.1, and note the mock clearly).
- Persist the Message + Citations + Conversation (create one if
  conversation_id is null) per the models from T1.1.
- Response shape must match exactly what's documented for frontend in
  frontend/coding_conventions.md's Phase 2 section (answer, confidence,
  confidence_label, classification, citations[], requires_human_review).
- If the AI layer returns zero citations or below-threshold confidence, ensure
  requires_human_review is true — never let a low-confidence answer look
  confident on the wire.

Write tests covering the persistence side (mock the AI layer call).

When done: update /backend/status.md with the final, confirmed contract (mark it
CONFIRMED, not draft) and flip T3.1 to [x] in /process.md. Add a Cross-part note —
this unblocks frontend T2.3.
```

### T3.2 — Conversation history endpoints

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Implement `GET /api/v1/chat/conversations` (list current user's
conversations) and `GET /api/v1/chat/conversations/{id}` (full message + citation
history for one conversation), both scoped to the authenticated user (users can
never see others' conversations except ADMIN).

When done: update /backend/status.md and flip T3.2 to [x] in /process.md.
```

### T3.3 — Feedback endpoint

**Prompt:**
```
Task: Implement `POST /api/v1/feedback` accepting message_id, rating, optional
comment, persisting to the Feedback model from T1.1.

When done: update /backend/status.md and flip T3.3 to [x] in /process.md.
```

### T3.4 — Classification and intent context threading

**Prompt:**
```
Read /ARCHITECTURE.md §5 (the 3-step onboarding flow) and §6, and
/context.md §8 first.

Task: Add `active_classification_id` and `active_intent` fields (nullable) to
the Conversation model — the first a foreign key to a Classification record,
the second a simple enum (PATENT/RESEARCH/SELL_BUSINESS/AYUSH_APPLICATION/
EXPORT/OTHER) matching the frontend's step-3 options. Both get set when the
3-step onboarding flow (frontend Phase 3) completes for a conversation.
Modify `/api/v1/chat` to: (1) load both if set, (2) pass both as parameters
to the AI layer's query pipeline call (see ai/prompts/phases.md T3.5 for the
AI-layer side consuming these), (3) allow either to be updated mid-conversation
if the user re-describes a different product or changes their stated intent.

VERIFICATION:
1. Test: create a conversation, set both active_classification and
   active_intent, send a chat message, confirm both were actually included
   in the payload sent to the AI layer (mock the AI layer call and assert on
   its arguments).
2. Test: confirm a conversation with neither set still works normally (both
   AI layer parameters are optional — this shouldn't break the case of a
   direct question with no onboarding completed, if that path is ever
   reachable).
3. Manual end-to-end check once the frontend onboarding flow exists: complete
   all 3 steps through the actual UI, then ask a follow-up question in the
   same conversation, and confirm (via logs or a debug endpoint) that both
   values were actually passed through — not just persisted in the DB but
   actually used in the request.

When done: update /backend/status.md with the field/contract details and flip
T3.4 to [x] in /process.md. Add a Cross-part note — AI layer T3.5 depends on
receiving both parameters correctly.
```

---

## Phase 4 — Classification / IP / ABS / sources / expert

### T4.1 — `/api/v1/classification`

**Prompt:**
```
Read /context.md §2 rule 6 (classification must be deterministic/auditable) and
/backend/coding_conventions.md first.

Task: Implement `POST /api/v1/classification` accepting the wizard answers from
frontend T3.1 (product type, derived-from-authoritative-text, formulation novelty,
biological resources used). This endpoint should call a rules-engine function in
the `ai/` layer (see ai/prompts/phases.md Phase 3, T3.3) rather than embedding
classification logic in the backend itself — the backend's job is to persist the
Classification record (including `rules_fired` for auditability) and shape the
response. If the ai/ rules engine isn't ready, stub it behind a clearly-marked
interface matching the documented contract, and note it in status.md.

When done: update /backend/status.md with the finalized contract and flip T4.1 to
[x] in /process.md. Add a Cross-part note — this unblocks frontend T3.1/T3.2.
```

### T4.2 — `/api/v1/ip` and `/api/v1/abs`

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Implement `POST /api/v1/ip` (returns per-IP-type relevance assessment for a
classified product, backing frontend's "IP protection map" in T3.2) and
`POST /api/v1/abs` (backing frontend's ABS wizard, T4.1). Both persist to
IPAssessment/ABSAssessment respectively and call into the AI layer for the actual
reasoning (see ai/prompts/phases.md Phase 3, T3.4 for ABS).

When done: update /backend/status.md with both contracts and flip T4.2 to [x] in
/process.md.
```

### T4.3 — `/api/v1/sources`

**Prompt:**
```
Task: If not already fully covered by T2.1's `/api/v1/documents` endpoint, add
whatever's missing to fully back the frontend Source Explorer (T4.2 in
frontend/prompts/phases.md) — e.g. full-text search across document titles/
sections if not already present. Otherwise, confirm in status.md that T2.1 already
covers this and this task is a no-op.

When done: update /backend/status.md and flip T4.3 to [x] in /process.md.
```

### T4.4 — Expert escalation + audit log wiring

**Prompt:**
```
Read /context.md §2 (escalation is a hard requirement, not optional) and
/backend/coding_conventions.md first.

Task: Implement `POST /api/v1/expert` (creates an ExpertRequest, RBAC-open to any
authenticated USER; list/resolve endpoints RBAC-gated to IP_FACILITATOR/ADMIN).
Then do a pass across every endpoint built so far in Phases 1–4 and ensure each
one that reads or writes sensitive/substantive data (chat answers, classification
results, document access, expert requests) writes an AuditLog entry — this is a
DPDP-alignment requirement from context.md, not a nice-to-have. Write a short test
asserting an AuditLog row is created for at least the chat and classification
flows.

When done: update /backend/status.md and flip T4.4 to [x] in /process.md.
```

---

## Phase 5 — Security, ops, deploy

### T5.1 — Rate limiting & input hardening

**Prompt:**
```
Read /backend/coding_conventions.md first.

Task: Add Redis-backed rate limiting to all public-facing endpoints (not just
login), tuned per endpoint sensitivity (chat/classification lower limits than
read-only listing endpoints). Review every Pydantic schema for missing length/
format constraints on free-text fields (question text, feedback comments) to
prevent abuse (e.g. absurdly long payloads). Add basic request size limits at the
ASGI/middleware level.

When done: update /backend/status.md and flip T5.1 to [x] in /process.md.
```

### T5.2 — Structured audit logging pass

**Prompt:**
```
Task: Review the AuditLog coverage from T4.4 for completeness against DPDP-style
principles referenced in context.md: log who accessed what, when, and why (action
type), without logging sensitive payload contents unnecessarily (e.g. log that a
chat query happened and its citations, not necessarily store duplicate raw PII).
Document the audit log's retention/rotation plan (even if just a comment/README
note for now — a full retention job is out of scope for the SIH MVP).

When done: update /backend/status.md and flip T5.2 to [x] in /process.md.
```

### T5.3 — Monitoring & health checks

**Manual prerequisite:** a free Sentry account + DSN.

**Prompt:**
```
Task: Integrate Sentry for error tracking (DSN from env var, never hardcoded).
Expand the `/health` endpoint from T0.2 to check DB, Redis, and object storage
connectivity individually, returning per-dependency status so ops can see exactly
what's down.

When done: update /backend/status.md and flip T5.3 to [x] in /process.md.
```

### T5.4 — Deploy + CI

**Manual prerequisite:** a Render or Railway account (or equivalent), a managed
Postgres instance with pgvector support enabled, and a managed Redis instance.

**Prompt:**
```
Task: Add a GitHub Actions workflow running lint + tests on every push. Prepare
deployment config for the chosen host (Render/Railway) including how migrations
run on deploy (a release/pre-deploy step running `alembic upgrade head`, not a
manual step). Document required production env vars in README.md. Do a final
smoke test against the deployed instance once the human has provisioned the
managed DB/Redis and set the env vars.

When done: update /backend/status.md, flip T5.4 to [x] in /process.md, and update
README.md §5 with the real deployed URL.
```

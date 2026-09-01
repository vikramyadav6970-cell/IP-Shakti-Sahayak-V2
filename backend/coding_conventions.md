# backend/coding_conventions.md

Read `/context.md` and `/process.md` before this file. This file governs how code
is written inside `backend/` specifically.

## Stack (authoritative)

- **Python 3.11+**, **FastAPI**, **Pydantic v2** for schemas/validation.
- **SQLAlchemy 2.0** (async) + **Alembic** for migrations.
- **PostgreSQL** with the **pgvector** extension as the MVP vector store — do not
  introduce a separate vector DB (Qdrant/Pinecone/Weaviate) until `context.md` is
  updated to reflect that decision. **Default: hosted on Supabase** (free tier,
  pgvector enabled via one click in the dashboard) — no local Postgres install
  required. Use the Session pooler connection string, not Transaction mode
  (breaks SQLAlchemy+asyncpg's prepared statements).
- **Redis** for caching, rate limiting, and as the Celery broker. **Default:
  hosted on Upstash** (free tier) — no local Redis install required.
- **Celery** for background jobs (document ingestion, embedding generation).
- **JWT** (via `python-jose` or `PyJWT`) for auth; RBAC roles: `USER`, `ADMIN`,
  `IP_FACILITATOR`, `CONTENT_MANAGER`, `RESEARCHER`.
- Object storage: **Supabase Storage** (S3-compatible) as the default — reuses
  the same Supabase project as the database, no separate service. Behind a
  single storage interface so swapping to raw AWS S3 later, or to a
  `LocalFilesystemStorage` implementation for fully-offline dev, is a config
  change, not a code change. (MinIO is an acceptable alternative if you
  specifically want a local S3-compatible service instead, but is not the
  default — see backend/prompts/phases.md T0.1.)

## Hard rules

1. **Layered architecture, always:** `api/` (route handlers — thin, no business
   logic) → `services/` (business logic) → `repositories/` (DB access). A route
   handler should read like: validate input (Pydantic does this), call a service,
   return the service's result. If you find yourself writing SQLAlchemy queries
   directly inside a route handler, stop and move it to a repository.
2. **Never hardcode secrets.** Every credential (LLM API key, DB URL, S3 keys, JWT
   secret) comes from environment variables via a single `Settings` object
   (pydantic-settings). `.env.example` must list every var with a comment on where
   to obtain it, and must never contain a real secret.
3. **Every schema change ships with an Alembic migration** in the same task/commit
   — never let models.py drift from the actual DB schema.
4. **No raw string-concatenated SQL, ever.** Use SQLAlchemy's query builder/ORM or
   parameterized `text()` calls only.
5. **Structured, not print-based, logging.** Use Python's `logging` module with a
   JSON formatter in production; every request that touches an AI answer must log
   enough to reconstruct what evidence/citations were used (this feeds the audit
   log requirement in context.md).
6. **Production-grade only:** every endpoint has explicit error handling (don't
   let an unhandled exception 500 silently — return a structured error body), input
   validation via Pydantic (reject, don't sanitize-and-hope), and a docstring
   explaining what it does. No endpoint should be left half-implemented and
   presented as done — mark it `[~]` in status.md instead.
7. **No unnecessary dependencies.** Before adding a library, check if the Stack
   list above already covers the need. If you genuinely need something new,
   name it explicitly in your task summary and in status.md with a one-line
   justification.
8. **Don't build your own auth, crypto, or password hashing.** Use established
   libraries (`passlib`/`bcrypt`, `python-jose`) — this is exactly the kind of
   "don't reinvent a library" case that matters most for security.
9. **API versioning:** all routes under `/api/v1/...` as already specified in
   `context.md`'s architecture notes. Don't introduce a differently-versioned or
   unversioned route.
10. **Tests required for every service function with real logic** (not simple
    passthroughs) — pytest, with a test DB (SQLite in-memory is fine for unit
    tests; use a real Postgres+pgvector test container for anything vector-related
    since SQLite can't emulate pgvector).

## Folder structure

```
backend/
├── coding_conventions.md
├── status.md
├── prompts/
│   └── phases.md
├── .env.example
├── requirements.txt / pyproject.toml
├── docker-compose.yml        # Postgres+pgvector, Redis, MinIO — shared dev infra
├── alembic/
├── app/
│   ├── main.py
│   ├── config.py             # Settings object
│   ├── api/                  # route handlers, one router module per resource
│   ├── schemas/               # Pydantic request/response models
│   ├── models/                # SQLAlchemy ORM models
│   ├── repositories/
│   ├── services/
│   ├── security/               # auth, RBAC, rate limiting
│   └── workers/                # Celery task definitions
└── tests/
```

## API contract discipline

Whenever you finalize or change a request/response schema for an endpoint the
frontend or AI layer depends on, **immediately update `backend/status.md` with the
exact JSON shape** and add a line under `process.md` → Cross-part notes. Don't make
the other tracks reverse-engineer your Pydantic models from source.

## Definition of done for any backend task

- `alembic upgrade head` runs clean from a fresh DB.
- New/changed endpoints documented (FastAPI's auto-generated OpenAPI docs count,
  but also update `status.md` with the shape for cross-team visibility).
- Relevant tests pass (`pytest`).
- No secrets committed, `.env.example` updated if new vars were introduced.
- `status.md` and `process.md` updated.

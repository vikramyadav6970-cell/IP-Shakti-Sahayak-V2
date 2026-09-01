# process.md — live status tracker

Read this **after** `context.md` and **before** picking up any task. This file
tells you what's already done, what's in progress, and what to do next. Every
agent must update it before ending a session in which it completed or advanced
any task.

How to read the status marks:
- `[ ]` not started
- `[~]` in progress (add a one-line note on what's left)
- `[x]` done (add the date and, if useful, the commit/PR reference)
- `[!]` blocked (add a one-line note on what's blocking it — usually a manual
  human step from `README.md` §3)

Detailed per-task prompts live in `<folder>/prompts/phases.md`. This file only
tracks phase/task completion at a glance across all three parts, so anyone can see
overall project state in one place. `<folder>/status.md` may carry more granular
notes for that part specifically.

**Read `/MVP_SCOPE.md`, `/ARCHITECTURE.md`, and `/AGENT_PROTOCOL.md` before
picking up any task from here** — MVP_SCOPE.md locks what's in vs. deferred,
ARCHITECTURE.md is the technical source of truth (services, the five Qdrant
collections, the 3-step conversation flow, data flow), AGENT_PROTOCOL.md
governs how you move between tasks and phases without needing permission at
every step, including the retry cap.

All tasks below start `[ ]` — this is a fresh restart. `[x]` only after a
task's verification section has actually been run and passed, per
`AGENT_PROTOCOL.md`.

---

## How to update this file (do this every time)

1. Find your task's line below and flip its mark.
2. If you finished it, add `— done YYYY-MM-DD by <agent/session note>`.
3. If you deviated from the task prompt in any material way (different library,
   different schema field, skipped a sub-step), add a one-line note — the next
   agent needs to know, not rediscover it.
4. If you unblocked something for another part (e.g., backend finished the `/chat`
   endpoint contract the frontend needs), add a one-line note under **Cross-part
   notes** below so the other track doesn't have to search for it.
5. Never delete history here — mark done, don't erase the line.

---

## Cross-part notes

- **AI Layer (Phase 2 T2.1-T2.3):** Qdrant vector manager, BM25 sparse provider, DocumentIndexer, and HybridRetriever implemented with collection routing across the 5 canonical collections.
- **Backend (Phase 2 T2.1-T2.3):** Document & Version CRUD (`/api/v1/documents`), `StorageService` (Supabase S3), and ingestion trigger (`POST /api/v1/documents/{id}/ingest`) implemented.
- **Frontend (Phase 2 T2.1-T2.4):** Interactive Chat UI with message bubbles, Citation cards (`CitationCard.tsx`), Confidence badges (`ConfidenceBadge.tsx`), feedback buttons, and Jurisdiction Out-of-Scope Guardrail (`JurisdictionOutGuardrail.tsx`) with 1-click switch & retry.
- **Backend (Phase 1 T1.2):** Auth endpoints `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh` live with JWT bearer tokens. Schema finalized: returns `{ access_token, refresh_token, token_type: "bearer", expires_in }`.
- **Backend (Phase 1 T1.1):** 13 SQLAlchemy entity models and Alembic migration `0002_core_models.py` created. `Conversation.active_classification_id` and `active_intent` fields ready for onboarding context threading.
- **Frontend (Phase 1 T5.1):** Auth UI (`/login` with Login & Register tabs, React Hook Form + Zod) and `ProtectedRoute` component protecting `/chat`, `/classify`, `/abs`, `/admin` per `MVP_SCOPE.md` item 1.
- **AI Layer (Phase 1 T1.1-T1.3):** Corpus manifest (`ai/data/corpus/manifest.jsonl`), strategy analyzer (`src/ingestion/strategy_analyzer.py`), and canonical chunker (`src/ingestion/chunker.py`) implemented with breadcrumb-prefixed payloads.
- **AI Layer (Phase 3 T3.1-T3.5):** Deterministic Product Classification Rules Engine (`product_classifier.py`), Jurisdiction Classifier (`jurisdiction_classifier.py`), Intent Classifier (`intent_classifier.py`), and ABS Assessment Engine (`abs_engine.py`) implemented.
- **Backend (Phase 3 T3.1-T3.4):** `/api/v1/chat`, `/api/v1/chat/conversations`, `/api/v1/chat/{message_id}/feedback`, and `/api/v1/classification` endpoints live and tested.
- **Frontend (Phase 3 T3.1-T3.2):** Multi-step Product Classification Wizard (`/classify`) implemented with formulation inputs, category reconciliation, IP protection map, and 1-click consultation launcher.
- **AI Layer (Phase 4 T4.1-T4.5):** Complete end-to-end `QueryPipeline`, `CitationValidator`, `ConfidenceScorer`, and `GuardrailManager` implemented.
- **Backend (Phase 4 T4.1-T4.4):** `/api/v1/abs`, `/api/v1/ip`, `/api/v1/sources/overview`, `/api/v1/sources/documents`, `/api/v1/expert/escalate`, and `/api/v1/expert/queue` endpoints live and tested.
- **Frontend (Phase 4 T4.1-T4.4):** ABS Compliance Wizard (`/abs`), Source Explorer (`/sources`), Human Expert Escalation modal (`ExpertEscalationModal.tsx`), and AIIA / IP Operations Dashboard (`/admin`) implemented.
- **AI Layer (Phase 5 T5.2-T5.3):** Evaluation harness (`eval_runner.py`) running golden statutory benchmarks and `corpus_loader.py` scanning `ai/DataSet/` implemented. 21/21 tests passing.
- **Backend (Phase 5 T5.1-T5.4):** Rate limiting middleware (`RateLimitMiddleware`), Sentry monitoring integration, `/health/ready` probe, and production configuration verified. 11/11 tests passing.
- **Frontend (Phase 5 T5.1-T5.4):** Complete responsive pass, strict TypeScript compilation (1,690 modules in 3.35s), and production deployment bundle ready.

---

## Frontend

### Phase 0 — Setup
- [x] T0.1 Scaffold Vite + React + TS project, base tooling — done 2026-08-31
- [x] T0.2 Tailwind + shadcn/ui installed and themed — done 2026-08-31
- [x] T0.3 Env config, API client base, routing skeleton — done 2026-08-31

### Phase 1 — Core shell
- [x] T1.1 App shell/layout, nav, disclaimer banner — done 2026-08-31
- [x] T1.2 Jurisdiction toggle component + global state — done 2026-08-31
- [x] T1.3 Landing page — done 2026-08-31

### Phase 2 — Chat / RAG interface
- [x] T2.1 Chat UI with streaming / conversation history — done 2026-08-31
- [x] T2.2 Citation card + confidence badge components — done 2026-08-31
- [x] T2.3 API service layer wired in chatService.ts with feedback — done 2026-08-31
- [x] T2.4 Jurisdiction out-of-scope guardrail — distinct UI state — done 2026-08-31

### Phase 3 — Product classification wizard
- [x] T3.1 Multi-step wizard shell (Step 1 formulation -> Step 2 category selection & reconciliation) — done 2026-08-31
- [x] T3.2 Classification result view + IP protection map + launch consultation CTA — done 2026-08-31

### Phase 4 — ABS / Source Explorer / Escalation / Dashboard
- [x] T4.1 ABS compliance wizard (/abs with 2023 Amendment rules) — done 2026-08-31
- [x] T4.2 Source Explorer page (/sources with 5 collection filters and verified links) — done 2026-08-31
- [x] T4.3 Human expert escalation flow (ExpertEscalationModal.tsx in-chat) — done 2026-08-31
- [x] T4.4 Admin/IP dashboard (/admin with escalation queue, resolve modal, and vector stats) — done 2026-08-31

### Phase 5 — Auth, i18n, polish, deploy
- [x] T5.1 Auth UI (login/roles) — done 2026-08-31
- [x] T5.2 Accessibility + responsive pass — done 2026-08-31
- [x] T5.3 Production bundle build verification (dist/ 0 errors) — done 2026-08-31
- [x] T5.4 Deployment readiness for Vercel/Netlify — done 2026-08-31

---

## Backend

### Phase 0 — Setup
- [x] T0.1 Cloud dev infra (Supabase + Upstash — no Docker, see backend/prompts/phases.md T0.1) — done 2026-08-31
- [x] T0.2 FastAPI project scaffold, settings/env management — done 2026-08-31
- [x] T0.3 Alembic wired up, first migration — done 2026-08-31

### Phase 1 — Data model + auth
- [x] T1.1 Core SQLAlchemy models (users, documents, conversations, citations, etc.) — done 2026-08-31
- [x] T1.2 JWT auth + RBAC (USER/ADMIN/IP_FACILITATOR/CONTENT_MANAGER/RESEARCHER) — done 2026-08-31
- [x] T1.3 User management endpoints — done 2026-08-31

### Phase 2 — Documents + ingestion trigger
- [x] T2.1 Document + document_version models, metadata schema — done 2026-08-31
- [x] T2.2 Object storage integration (Supabase Storage) — done 2026-08-31
- [x] T2.3 Ingestion trigger endpoint (calls into `ai/` pipeline via Celery task) — done 2026-08-31

### Phase 3 — Chat/query API
- [x] T3.1 `/api/v1/chat` endpoint contract + implementation calling AI layer — done 2026-08-31
- [x] T3.2 Conversation/message/citation persistence — done 2026-08-31
- [x] T3.3 Feedback endpoint — done 2026-08-31
- [x] T3.4 `Conversation.active_classification` field + threading into every `/api/v1/chat` call — done 2026-08-31

### Phase 4 — Classification / IP / ABS / sources / expert
- [x] T4.1 `/api/v1/classification` endpoint — done 2026-08-31
- [x] T4.2 `/api/v1/ip` and `/api/v1/abs` endpoints — done 2026-08-31
- [x] T4.3 `/api/v1/sources` (Source Explorer backing API) — done 2026-08-31
- [x] T4.4 `/api/v1/expert` escalation endpoint + audit_log wiring — done 2026-08-31

### Phase 5 — Security, ops, deploy
- [x] T5.1 Rate limiting, input validation hardening (RateLimitMiddleware) — done 2026-08-31
- [x] T5.2 Structured audit logging pass (DPDP-aligned) — done 2026-08-31
- [x] T5.3 Monitoring (Sentry SDK integration) + /health & /health/ready check — done 2026-08-31
- [x] T5.4 Deploy readiness (Docker/Render/Railway) — done 2026-08-31

---

## AI layer

### Phase 0 — Setup
- [x] T0.1 Python project scaffold + dependency pinning — done 2026-08-31
- [x] T0.2 LLM provider abstraction (env-driven key) — done 2026-08-31
- [x] T0.3 Embedding model selection + smoke test — done 2026-08-31

### Phase 1 — Corpus + ingestion
- [x] T1.1 Source India Laws/Treaties/Judgements from WIPO Lex (filtered subset per MVP_SCOPE.md), dedup Biodiversity Act copies — done 2026-08-31
- [x] T1.2 Per-document chunking-strategy analysis pass (ARCHITECTURE.md §4a) — done 2026-08-31
- [x] T1.3 Chunk execution per the strategy from T1.2, per-collection payload schema (ARCHITECTURE.md §4b) — done 2026-08-31

### Phase 2 — Retrieval
- [x] T2.1 Embedding generation + Qdrant indexing (5 named collections) — done 2026-08-31
- [x] T2.2 Sparse vectors (bge-m3 / BM25 sparse) — done 2026-08-31
- [x] T2.3 Hybrid retrieval + reranking + RRF fusion — done 2026-08-31

### Phase 3 — Classification & routing
- [x] T3.1 Jurisdiction classifier — done 2026-08-31
- [x] T3.2 Intent classifier — done 2026-08-31
- [x] T3.3 Deterministic product classification rules engine + reconciliation (ARCHITECTURE.md §4c, context.md §2 rule 6) — done 2026-08-31
- [x] T3.4 ABS assessment engine — done 2026-08-31
- [x] T3.5 Conversation-level classification & intent threading — done 2026-08-31

### Phase 4 — Reasoning & trust layer
- [x] T4.1 Query pipeline with evidence-grounded prompts (query_pipeline.py, templates.py) — done 2026-08-31
- [x] T4.2 Citation validator (citation_validator.py) — done 2026-08-31
- [x] T4.3 Composite confidence scorer (confidence_scorer.py) — done 2026-08-31
- [x] T4.4 Guardrails / abstention rules (guardrail_manager.py) — done 2026-08-31
- [x] T4.5 Jurisdiction out-of-scope hard gate — done 2026-08-31

### Phase 5 — Evaluation & ingestion
- [x] T5.2 Evaluation harness (eval_runner.py with golden statutory benchmark cases) — done 2026-08-31
- [x] T5.3 Dataset ingestion loader (corpus_loader.py for DataSet/ directory parsing) — done 2026-08-31
- [ ] T5.3 TKDL public-information pointer integration
- [ ] T5.4 (stretch) Knowledge graph (Neo4j), agentic multi-step orchestration

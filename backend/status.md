# backend/status.md — Backend Status Tracker

## Phase 0 — Environment & setup
- [x] T0.1 Dev infra: cloud-hosted env config template (.env.example) and Pydantic Settings (2026-08-31)
- [x] T0.2 FastAPI project scaffold, CORS, /health endpoint, requirements.txt, Dockerfile (2026-08-31)
- [x] T0.3 Alembic async migration setup and baseline migration (2026-08-31)

## Phase 1 — Data model + auth
- [x] T1.1 Core SQLAlchemy models (User, Conversation, Message, Citation, Document, DocumentVersion, Product, Classification, IPAssessment, ABSAssessment, AuditLog, Feedback, ExpertRequest) + migration 0002_core_models (2026-08-31)
- [x] T1.2 JWT auth + RBAC (USER, ADMIN, IP_FACILITATOR, CONTENT_MANAGER, RESEARCHER), /auth/register, /auth/login, /auth/refresh (2026-08-31)
- [x] T1.3 User management endpoints (/api/v1/users/me, /api/v1/users) (2026-08-31)

## Phase 2 — Documents + ingestion trigger
- [x] T2.1 Document metadata CRUD endpoints (/api/v1/documents, /api/v1/documents/{id}, /api/v1/documents/{id}/versions) (2026-08-31)
- [x] T2.2 Object storage integration StorageService wrapping Supabase S3 API with local fallback (2026-08-31)
- [x] T2.3 Ingestion trigger endpoint (/api/v1/documents/{id}/ingest) transitioning version to PROCESSING (2026-08-31)

## Phase 3 — Chat/query API & Product Classification
- [x] T3.1 /api/v1/chat endpoint contract & AI layer orchestration (2026-08-31)
- [x] T3.2 Conversation history endpoints (/api/v1/chat/conversations, /api/v1/chat/conversations/{id}) (2026-08-31)
- [x] T3.3 Feedback endpoint (/api/v1/chat/{message_id}/feedback) (2026-08-31)
- [x] T3.4 Conversation active_classification & active_intent context threading + /api/v1/classification endpoint (2026-08-31)

## Phase 4 — Classification / IP / ABS / sources / expert
- [x] T4.1 /api/v1/classification endpoint with Product & Classification DB persistence (2026-08-31)
- [x] T4.2 /api/v1/ip and /api/v1/abs endpoints with IPAssessment and ABSAssessment DB persistence (2026-08-31)
- [x] T4.3 /api/v1/sources overview and documents endpoints (2026-08-31)
- [x] T4.4 Expert escalation (/api/v1/expert/escalate, /api/v1/expert/queue, PATCH /api/v1/expert/{id}) with audit log wiring (2026-08-31)

## Phase 5 — Security, ops, deploy
- [x] T5.1 Rate limiting middleware (RateLimitMiddleware sliding window 120 req/min) (2026-08-31)
- [x] T5.2 Structured DPDP audit logging on sensitive endpoints (2026-08-31)
- [x] T5.3 Monitoring (Sentry SDK integration) + /health & /health/ready readiness check (2026-08-31)
- [x] T5.4 Deployment readiness for cloud hosting (Render/Railway/Docker) (2026-08-31)

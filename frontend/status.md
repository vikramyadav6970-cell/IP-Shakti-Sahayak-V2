# frontend/status.md — Frontend Status Tracker

## Phase 0 — Setup
- [x] T0.1 Scaffold Vite + React 18 + TS project, strict mode, package.json, tooling (2026-08-31)
- [x] T0.2 Tailwind + shadcn/ui components installed & themed for legal-tech compliance (2026-08-31)
- [x] T0.3 Env config (.env.example), API client (apiClient.ts), TanStack Query, routing skeleton, Zustand stores (2026-08-31)

## Phase 1 — Core shell & Auth Gate
- [x] T5.1 Auth UI (/login with tabs for sign-in & registration, React Hook Form + Zod, ProtectedRoute route guarding) (2026-08-31)
- [x] T1.1 Persistent app shell with mandatory standing legal disclaimer banner (2026-08-31)
- [x] T1.2 Jurisdiction toggle component (India default / International target dropdown) + localStorage persistence (2026-08-31)
- [x] T1.3 Landing page with query input, prefill routing, and quick-filter chips (2026-08-31)

## Phase 2 — Chat / RAG interface
- [x] T2.1 Chat UI with conversation history, input bar, auto-scroll, clear chat, and sample query cards (2026-08-31)
- [x] T2.2 Citation card component (CitationCard.tsx) with statutory links + confidence badge (ConfidenceBadge.tsx) (2026-08-31)
- [x] T2.3 API service layer wired in chatService.ts with feedback collection (2026-08-31)
- [x] T2.4 Jurisdiction out-of-scope distinct UI guardrail state (JurisdictionOutGuardrail.tsx) with 1-click switch & retry (2026-08-31)

## Phase 3 — Product classification wizard
- [x] T3.1 Multi-step wizard shell (Step 1 formulation -> Step 2 category selection & reconciliation) (2026-08-31)
- [x] T3.2 Step 3 intent declaration + reconciled classification & IP protection map + launch consultation CTA (2026-08-31)

## Phase 4 — ABS / Source Explorer / Escalation / Dashboard
- [x] T4.1 ABS compliance wizard (/abs with 2023 amendment rules & form recommendations) (2026-08-31)
- [x] T4.2 Source Explorer page (/sources with 5 collection filters and verified links) (2026-08-31)
- [x] T4.3 Human expert escalation flow (ExpertEscalationModal.tsx & in-chat action button) (2026-08-31)
- [x] T4.4 Admin & IP Operations dashboard (/admin with escalation queue, resolve modal, and vector collections) (2026-08-31)

## Phase 5 — Auth, polish, deploy
- [x] T5.1 Auth UI (completed early per sequencing requirement) (2026-08-31)
- [x] T5.2 Accessibility & responsive audit (2026-08-31)
- [x] T5.3 Production build & bundle verification (dist/ 0 errors) (2026-08-31)
- [x] T5.4 Deployment readiness for Vercel/Netlify (2026-08-31)

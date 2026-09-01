# IP-SAKTI Sahayak

**SIH 2026 — Problem Statement 26045 (Ministry of Ayush / All India Institute of Ayurveda)**

A multilingual, RAG-based, source-cited AI assistant for Intellectual Property and
regulatory guidance in Ayurveda, across national and international regimes.

> ⚠️ This is not an Ayurveda chatbot. It is an AI-powered IP + regulatory
> decision-support system whose answers are generated from authoritative
> legal/regulatory sources and are traceable to those sources. It provides
> **information, not legal advice**.

---

## 0. Read this first if you are an AI agent

If you are an AI coding assistant picking up this project (in any session, any tool),
**read these six files in the repo root, in order, before writing any code**:

1. `context.md` — what this project is, why it's built this way, and the decisions
   already made (so you don't re-litigate them).
2. `ARCHITECTURE.md` — the technical system architecture: services, the five
   Qdrant collections, the conversation flow, data flow. Source of truth for
   anything technical.
3. `MVP_SCOPE.md` — the locked feature list. If a task isn't on the MVP list,
   it does not get built yet, no matter how small it seems.
4. `AGENT_PROTOCOL.md` — how you move through tasks and phases without
   asking permission at every step, including the retry cap and when you
   must stop and report instead of continuing. Read this before starting any
   task, not just once — the retry-cap discipline matters every time you hit
   a failing test.
5. `process.md` — what has been done, what is in progress, and what to do next.
6. The `coding_conventions.md` inside whichever folder you're working in
   (`frontend/`, `backend/`, or `ai/`).

Then open `prompts/` inside your assigned folder and find the next un-checked task
for the current phase. Each task in that file is a self-contained prompt — treat it
as your instructions. When you finish a task, **update `process.md` and the
`status.md` in your folder** before ending your turn (see the update template in
`process.md`).

---

## 1. What this project actually is

A product entrepreneur (e.g. "turmeric + ashwagandha + giloy formulation for
immunity") has questions like:

- Can I patent this?
- Is it already traditional knowledge?
- Do I need ABS (Access and Benefit Sharing) approval?
- Is it an Ayurvedic medicine or Ayurveda-Aahara (food)?
- Can I register the brand name / protect the packaging?
- Can I export it, and what changes internationally?

Today answering this requires consulting many different statutes, registries and
often a lawyer. IP-SAKTI Sahayak brings this together into one system that:

- **Classifies the product first** (classical medicine / proprietary medicine / new
  drug / phytopharmaceutical / Ayurveda-Aahara / cosmetic) — because IP strategy
  depends entirely on this.
- **Routes the question** across IP types (Patent, GI, Trademark, Copyright, Design,
  Plant Variety, Trade Secret), ABS/TKDL, and drug/food/cosmetic regulation.
- **Keeps India and International answers visibly separate** via an explicit
  jurisdiction toggle — never conflated.
- **Never answers without evidence.** Every material claim is retrieved from a
  version-tracked corpus of statutes/rules/treaties/registry data, cited, and
  validated before being shown to the user.
- **Escalates to a human IP facilitator** when confidence is low.

## 2. Architecture — three parts

```
 USER
   │
   ▼
 FRONTEND (React)  ──calls──▶  BACKEND (FastAPI)  ──calls──▶  AI LAYER (RAG pipeline)
   │                               │                               │
 chat UI, classification        auth, persistence,           retrieval, classification
 wizard, jurisdiction toggle,   document mgmt, audit log,     rules, LLM reasoning,
 citation cards, dashboards     API contracts                 citation validation
```

We build it as a **modular monolith first**, not microservices — three cleanly
separated codebases (`frontend/`, `backend/`, `ai/`) that talk over well-defined HTTP
contracts. This is far easier to build, debug and demo for SIH than a distributed
system, and can be split into services later if needed.

Full stack decisions and rationale live in `context.md`. Each folder's
`coding_conventions.md` has the authoritative, current dependency list — check there
before assuming a library choice from this README is still current.

## 3. Prerequisites (manual, one-time, human setup)

These cannot be done by an AI agent — a human needs to do these before development
starts:

| # | What | Why | Where to get it |
|---|---|---|---|
| 1 | Node.js 20+ and npm/pnpm | Frontend | nodejs.org |
| 2 | Python 3.11+ | Backend + AI layer | python.org |
| 3 | A free **Supabase** project, with the `vector` extension enabled (Database → Extensions) | Postgres + pgvector, and object storage — no local Postgres/Docker install needed | supabase.com |
| 4 | A free **Upstash Redis** database | Cache, rate limiting, Celery broker — no local Redis install needed | upstash.com |
| 5 | An LLM API key (Anthropic **or** OpenAI **or** Google) | AI reasoning layer | console.anthropic.com / platform.openai.com / ai.google.dev |
| 6 | (Optional, Phase 2+) Bhashini API access | Hindi voice/translation | bhashini.gov.in — request API access as a developer |
| 7 | GitHub repo + a place to push (for CI/CD later) | version control | github.com |
| 8 | Free hosting/deploy accounts when ready: Vercel (frontend), Render/Railway (backend) | demo deployment | vercel.com, render.com |

Do **not** wait on #6/#8 to start Phase 1 work — they're only needed from the
phase noted in each folder's `prompts.md`. #3 and #4 take about ten minutes
combined and replace Docker/local Postgres/local Redis entirely — see
`backend/prompts/phases.md` T0.1 for exact setup steps. Docker is optional, not
required, for this project; a native/local-services path exists too if you
specifically want it (also documented in T0.1).

## 4. Repository layout

```
/
├── README.md                  ← you are here
├── context.md                 ← project context, read first
├── ARCHITECTURE.md            ← technical system architecture, read second
├── MVP_SCOPE.md               ← locked feature list, read third
├── AGENT_PROTOCOL.md          ← autonomous test-and-proceed rules, read fourth
├── process.md                 ← live status tracker, read fifth
├── frontend/
│   ├── coding_conventions.md
│   ├── status.md
│   └── prompts/
│       └── phases.md
├── backend/
│   ├── coding_conventions.md
│   ├── status.md
│   └── prompts/
│       └── phases.md
└── ai/
    ├── coding_conventions.md
    ├── status.md
    ├── data/corpus/seed/     ← real verified seed dataset + manifest
    └── prompts/
        └── phases.md
```

(The actual application source code — `frontend/src`, `backend/app`, `ai/` pipeline
code — gets created *inside* these same folders as Phase 1 tasks are executed. These
docs live alongside the code, not in a separate `docs/` tree, so an agent working in
`backend/` always has its conventions one directory away.)

## 5. Local setup (once code exists)

```bash
# 1. Clone
git clone <repo-url> ip-sakti-sahayak && cd ip-sakti-sahayak

# 2. Backend — connects to your Supabase + Upstash projects (§3, prerequisites)
cd backend
cp .env.example .env        # fill in DATABASE_URL, REDIS_URL, LLM_API_KEY etc — see §3 and backend/coding_conventions.md
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 3. AI layer (if run as a separate process/worker; otherwise imported by backend)
cd ../ai
pip install -r requirements.txt
celery -A worker worker --loglevel=info

# 4. Frontend
cd ../frontend
npm install
cp .env.example .env        # set VITE_API_BASE_URL
npm run dev
```

No local database/cache services to start — Postgres+pgvector (Supabase) and
Redis (Upstash) are cloud-hosted per §3. If you're using the local/native
alternative instead (see `backend/prompts/phases.md` T0.1), start your local
Postgres and Redis services before step 2.

Exact commands will solidify once Phase 1 scaffolding tasks are complete — this
section should be kept up to date by whoever completes those tasks (see
`process.md` update instructions).

## 6. Contribution flow

1. Pick the next open task from your folder's `prompts/phases.md`.
2. Read that folder's `coding_conventions.md` — no exceptions.
3. Do the task. Production-grade code only (see conventions — no stubs, no TODOs,
   no placeholder libraries).
4. Update `status.md` in your folder and the shared `process.md`.
5. Commit with a message referencing the phase/task, e.g.
   `feat(backend): P2-T3 document ingestion endpoint`.

## 7. Non-negotiable product requirements (apply across all three parts)

- Jurisdiction (India vs International) is never conflated in a single answer.
- Every factual/legal claim shown to a user must carry a citation traceable to a
  real, retrieved source — never LLM-invented.
- A standing "information, not legal advice" disclaimer is always visible.
- Low-confidence answers must offer escalation to a human IP facilitator.
- No fabricated statutes, sections, case names, dates or patent numbers — ever.

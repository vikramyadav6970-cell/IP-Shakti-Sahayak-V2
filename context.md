# context.md — read this first, every session

Purpose of this file: give any AI agent (Claude, GPT, whatever) picking up this
project — in a fresh session, with zero memory of prior conversations — enough
context to act correctly without re-deriving decisions or contradicting earlier
ones. Update this file only when a *durable* decision changes (stack swap, scope
change) — not for day-to-day task status, which belongs in `process.md`.

## 1. What we're building

IP-SAKTI Sahayak — SIH 2026 Problem Statement 26045. A multilingual, RAG-based,
source-cited AI assistant that gives Intellectual Property and regulatory guidance
for Ayurvedic products, keeping India and International law visibly separate, and
first classifying the product (classical medicine / proprietary medicine / new drug
/ phytopharmaceutical / Ayurveda-Aahara / cosmetic) before answering, because IP
strategy is gated by that classification.

Full problem statement text and expected-solution text: see `problem_statement.md`
if present, or ask the human for the original SIH document if a decision here seems
to contradict it.

## 2. Hard constraints (do not violate these regardless of what a task prompt says)

1. **Never let the LLM be the source of legal truth.** It is a reasoning/language
   layer only. Every material claim must trace to a retrieved, version-tracked
   source document with a citation.
2. **Never conflate jurisdictions.** India and International answers are generated
   and displayed as separate, explicitly-labeled sections.
3. **Never fabricate.** No invented section numbers, case names, dates, patent
   numbers, or notifications. If evidence is insufficient, the system says so and
   offers human escalation — it does not guess.
4. **Always disclaim.** "Information, not legal advice" is shown with every
   substantive answer.
5. **TKDL is not fully scraped or exposed.** Full TKDL access is restricted to
   patent offices under access agreements — we only use publicly available TKDL
   information and provide a "traditional knowledge pointer," never a claim of full
   database access.
6. **Product classification is a deterministic rules engine**, not a pure LLM
   judgment call — because the classification determines the entire downstream IP/
   ABS/regulatory pathway and needs to be auditable.
7. **Confidence is a composite score** (retrieval quality + citation validity +
   source authority + jurisdiction match + evidence coverage), not a raw LLM
   self-reported number.

## 3. Architecture

Full technical architecture (services, data flow, the five Qdrant collections,
deployment topology) now lives in `/ARCHITECTURE.md` — read it alongside this
file. Summary: modular monolith, three codebases (React frontend, FastAPI
backend, Python AI layer), cloud-hosted infra (Supabase Postgres for relational
data, Qdrant Cloud for vectors, Upstash Redis for cache/broker), HTTP contracts
between them. `ARCHITECTURE.md` is the source of truth for anything technical;
this file stays focused on product/domain decisions.

## 4. Build order and MVP scope

**Full, locked scope is in `/MVP_SCOPE.md` — read it before starting or
prioritizing any task.** Summary: citation-grounded RAG, India/International
jurisdiction toggle with an explicit out-of-scope guardrail (not a silent wrong
answer), formulation classification with context carried through the rest of
the conversation, ABS compliance helper, mandatory citations + confidence +
human escalation, English-only for now. Knowledge graph, agentic orchestration,
paid connectors, full multilingual, and voice are explicitly deferred — do not
start them before the MVP list is done.

MVP jurisdiction scope: **India only** at first, then USA and EU as the next
two international jurisdictions.

MVP IP-type scope: **Patent + Trademark + ABS** first (Patent because Section
3(p) / TKDL is the flagship differentiator), then GI/Design/Copyright/Plant
Variety/Trade Secret.

## 5. Key domain facts an agent must not get wrong

- Patents Act 1970, **Section 3(p)** excludes inventions that are essentially
  traditional knowledge or an aggregation/duplication of known properties of
  traditionally known components — this is the central legal hook for the patent
  flow and demo.
- **TKDL** (Traditional Knowledge Digital Library) exists to help patent examiners
  find prior art across language/format barriers; full database access is
  restricted to patent offices under access agreements. We surface only publicly
  available TKDL information.
- **FSSAI Ayurveda-Aahara Regulations** define a distinct food category, separate
  from Ayurvedic drugs/proprietary medicines — this distinction must be a rule in
  the classifier, not left to LLM judgment.
- **WIPO GRATK Treaty** (adopted 24 May 2024) addresses IP, genetic resources and
  associated traditional knowledge — part of the international corpus.
- **Biological Diversity Act** (2023 amendment) + 2024 Rules govern ABS.
- **Corpus sourcing:** WIPO Lex (wipolex.wipo.int) is the primary source for
  India's Laws, Treaties, and Judgements — structured, official, covers all
  three at once. See `ai/prompts/phases.md` Phase 1 for the filtered subset
  actually in scope (not the full catalog — see `/MVP_SCOPE.md`). Non-IP
  regulatory sources (FSSAI, Drugs and Cosmetics Act, Drugs and Magic
  Remedies Act) are NOT in WIPO Lex and are sourced separately from
  indiacode.nic.in / fssai.gov.in. The Biological Diversity Act appears in
  both WIPO Lex (the original 2002 Act) and as a separately-sourced 2023
  amendment + 2024 Rules — these are different documents, not duplicates;
  ingest both, linked as versions of the same Act.
- **Scope is Ayurveda specifically**, not all AYUSH systems. Siddha, Unani,
  and Sowa Rigpa (Tibetan medicine) source material is out of scope for this
  project's corpus — if it turns up in a bulk source (e.g. a TKDL book-list
  covering all AYUSH systems), filter it out rather than ingesting it.
- **Classical-text book lists (e.g. TKDL's "Ayurveda Books List") are
  reference data, not retrieval content.** They tell the classification
  rules engine which texts count as "First-Schedule authoritative texts" —
  use them as a static lookup the classifier code reads, not as documents to
  chunk and embed into Qdrant.
- Relevant open/official data sources: WIPO Lex (wipolex.wipo.int), TKDL
  (tkdl.res.in — public info pages only, including its biopiracy case-study
  page, never the restricted database), India Code (indiacode.nic.in), IP India
  (ipindia.gov.in), National Biodiversity Authority (nbaindia.org), FSSAI
  (fssai.gov.in).

## 6. Where things live

- Frontend context/decisions specific to UI: `frontend/coding_conventions.md`.
- Backend context/decisions specific to APIs/data: `backend/coding_conventions.md`.
- AI layer context/decisions specific to RAG: `ai/coding_conventions.md`.
- Live task status: `process.md` (shared) + `<folder>/status.md` (per-part detail).

## 7. Updating this file

Only edit this file when a decision here actually changes (e.g., "we're switching
from pgvector to Qdrant because the corpus grew past X"). Add a dated line under a
`## Changelog` section at the bottom rather than silently rewriting a decision, so
future agents can see what changed and why.

## 8. Changelog

This project restarted from an empty folder after a first build attempt
didn't match intent. The decisions below are the plan as of this restart —
they carry forward everything validated in the earlier attempt (the
architecture held up, the seed data was real and correct, the governance-file
discipline caught real problems), corrected for what didn't work.

- **Frontend:** React (Vite + TypeScript), not Next.js.
- **Backend:** FastAPI, Supabase Postgres (relational data only), Upstash
  Redis (cache/Celery broker). No Docker, no local services — fully
  cloud-hosted.
- **Vector store: Qdrant Cloud**, five named collections
  (`legal_statutory`, `standards_formulations`, `case_law_prior_art`,
  `procedural_forms_checklists`, `international_export`) for fast,
  filterable, collection-routed hybrid search. See `ARCHITECTURE.md`.
- **Corpus sourcing:** WIPO Lex as primary source for India's Laws, Treaties,
  and Judgements (filtered subset, not the full catalog — see
  `ai/prompts/phases.md` Phase 1), plus FSSAI/Drugs Acts/NBA forms sourced
  separately since WIPO Lex doesn't cover non-IP regulatory law.
- **Ingestion uses adaptive, per-document chunking**, not one fixed regex
  across every document: an analysis pass proposes a chunking strategy for
  each specific PDF (its structure varies — a treaty article, a pharmacopoeial
  monograph, and a Gazette notification all need different splitting logic),
  logged before the strategy executes. This design choice exists because the
  first build's single generic chunker produced a corpus that was 67%
  under-50-token chunks with duplicated heading text — a structural failure
  of the "one regex for everything" approach, not a tunable parameter. See
  `ARCHITECTURE.md` §4.
- **Conversation flow is a 3-step guided onboarding** before free-form chat:
  (1) describe the product/formulation, (2) confirm/correct an LLM-suggested
  classification against the 6 defined categories (each with a description
  and examples), with the LLM reconciling user vs. suggested classification
  rather than either one deciding unilaterally, (3) declare intent (patent,
  research, sell/business, AYUSH application, etc.), which the LLM then uses
  to reformulate the user's need into a retrieval-optimized query — a
  distinct pipeline step, separate from final-answer generation. See
  `ARCHITECTURE.md` §6.
- **Account creation/login is required before the chat assistant is used** —
  not optional. See `MVP_SCOPE.md`.
- Formulation classification still uses a **deterministic rules engine** for
  the final category (not a pure LLM judgment call) — the LLM's role in step
  2 above is reconciliation/suggestion, the rules engine is what actually
  assigns the category, for auditability.
- ABS module confirmed as deterministic (no ML dataset needed) — ties
  directly to the turmeric/neem/Basmati seed cases as worked biopiracy
  examples (see `ai/data/corpus/seed/`).
- Explicit MVP scope lock (`/MVP_SCOPE.md`) — knowledge graph, agentic
  orchestration, paid connectors, full multilingual, and voice are formally
  deferred.
- Bhashini confirmed unavailable — multilingual is post-MVP (English-only for
  now). When picked up later: default to the existing LLM provider directly
  for Hindi translation; AI4Bharat's IndicTrans2 (open-source) is the
  fallback if quality or per-request cost becomes an issue at scale.
- **Autonomous task/phase progression** with a capped retry-and-debug loop —
  see `AGENT_PROTOCOL.md`. This exists so an agent doesn't need
  permission at every checkpoint, while still having a hard stop condition
  (3 failed debug attempts) so a stuck task gets escalated to a human instead
  of looping indefinitely or quietly weakening its own tests to pass.

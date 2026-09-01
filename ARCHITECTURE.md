# ARCHITECTURE.md

Technical system architecture — services, data flow, deployment topology. Read
`/context.md` first for product/domain decisions; this file is the technical
counterpart. If this file and a folder's `coding_conventions.md` disagree, the
`coding_conventions.md` is authoritative (it's touched more often during active
work) — update this file to match rather than the reverse.

## 1. System shape

Modular monolith, three codebases, HTTP contracts between them. Not
microservices — easier to build, debug, and demo on a hackathon timeline; can
split later if genuinely needed.

```
FRONTEND (React)  ──HTTP──▶  BACKEND (FastAPI)  ──calls──▶  AI LAYER (Python)
                                    │                              │
                             Supabase Postgres              Qdrant Cloud
                             (relational data)          (5 vector collections)
                                    │                              │
                                    └──────── Upstash Redis ───────┘
                                           (cache, Celery broker)
```

## 2. Services and why

| Service | Role | Why this one |
|---|---|---|
| **Supabase (Postgres)** | Relational data only — users, documents metadata, conversations, messages, citations, audit log, classification/ABS results | Cloud-hosted, no local install, pgvector NOT used here anymore (see §3) |
| **Qdrant Cloud** | All vector search — five named collections | Native multi-collection + filtered hybrid search, matches this project's 5-way corpus split directly rather than needing to be hand-built on Postgres |
| **Upstash Redis** | Cache, rate limiting, Celery broker | Cloud-hosted, no local install |
| **FastAPI backend** | Auth, persistence, API contracts, orchestrates calls into the AI layer | Async-friendly for I/O-bound RAG workloads |
| **AI layer (Python)** | Ingestion, chunking, embedding, retrieval, classification, reasoning, citation validation, confidence scoring | Kept as owned/auditable code, not hidden behind a framework — see `ai/coding_conventions.md` hard rules |
| **React frontend** | Chat UI, classification/ABS wizards, jurisdiction toggle, citation display | Plain React (not Next.js) per explicit product decision |

No Docker, no local services anywhere in this stack — see each folder's
`coding_conventions.md` T0.1 for exact cloud setup steps.

## 3. The five Qdrant collections

Each is a separate named collection (not a filtered slice of one big
collection) — this is what makes retrieval fast: a query routes to the 1-2
relevant collections via intent classification before searching, instead of
scanning everything.

| Collection | Contains | Chunking unit |
|---|---|---|
| `legal_statutory` | Acts & Rules (from WIPO Lex + FSSAI/Drugs Acts) | One chunk per Section/clause, structure-aware, breadcrumb-prefixed |
| `standards_formulations` | API/AFI pharmacopoeial monographs | One chunk per monograph, sub-chunked if long |
| `case_law_prior_art` | Patent/opposition records + real court judgments (now populated via WIPO Lex Judgements) | One chunk per case/record, kept whole |
| `procedural_forms_checklists` | Filing forms, application checklists (incl. NBA ABS forms) | One chunk per form, rarely split |
| `international_export` | Treaties (from WIPO Lex) + market-access guidance (FDA/EMA) | Structure-aware by Article, or by country+topic block |

Every collection: dense vector 1024-dim (BAAI/bge-m3), Cosine distance, plus a
named sparse vector for hybrid search, with payload indexes on `jurisdiction`,
`document_type`, `language`, `status`.

## 4. Data flow — offline (corpus building)

```
WIPO Lex + FSSAI/Drugs Acts + NBA forms + procedural forms
        │
        ▼
   Per-document chunking-strategy analysis  ── see §4a
        │
        ▼
   Chunk (per the strategy determined above)
        │
        ▼
   Embed (bge-m3 dense + sparse)
        │
        ▼
   Index in Qdrant (routed to the correct one of five collections)
```

### 4a. Adaptive per-document chunking — why, and how

**This exists because of a specific, real failure.** An earlier attempt at
this project used one fixed regex-based chunker across every document in a
collection, assuming documents of the same "type" (e.g. all statutes) shared
a structure. They didn't — different source PDFs used different heading
conventions, table-of-contents formatting, and section-numbering styles, and
the one-size chunker produced a corpus that was 67% under-50-token chunks,
many containing duplicated heading text as their entire "body." That's not a
tunable-parameter problem, it's a wrong-architecture problem.

The fix: **a two-phase ingestion pipeline, not one.**

**Phase A — strategy analysis (runs once per document, before chunking):**
Given a document's extracted text (or a representative sample of it for long
documents), analyze its actual structure and produce a small structured
config describing how to split it — e.g. "split on `Article N` headers, keep
associated footnotes with their article," or "split on `Monograph:` markers,
sub-split by Identity/Purity/Assay/Therapeutic-Use sub-headings," or "split
per numbered form field, never mid-field." Log this proposed strategy before
applying it — this is what would have caught the earlier failure at document
1 of many, not after 17,000+ chunks.

**Phase B — deterministic execution:** apply the logged strategy to actually
produce chunks. This phase should be boring and repeatable — all the
judgment happens in Phase A, Phase B just executes it.

This is more work than one universal regex, and that's the point — it's
correct for a corpus where a treaty article, a pharmacopoeial monograph, a
Gazette notification, and a patent application form all have genuinely
different internal structure.

### 4b. Canonical chunk payload schema

Every collection's chunks carry a payload with this shape (fields vary by
collection — this example is `legal_statutory`/`international_export`;
`standards_formulations`, `procedural_forms_checklists`, and
`case_law_prior_art` need their own field sets at the same level of
specificity, built the same way):

```json
{
  "id": "trips_art_27_p1_p3",
  "vector": [0.0142, -0.0521, 0.0894],
  "payload": {
    "doc_title": "Agreement on Trade-Related Aspects of Intellectual Property Rights",
    "doc_amended_date": "2017-01-23",
    "part_number": "PART II",
    "part_title": "STANDARDS CONCERNING THE AVAILABILITY, SCOPE AND USE OF INTELLECTUAL PROPERTY RIGHTS",
    "section_number": "SECTION 5",
    "section_title": "PATENTS",
    "article_number": "Article 27",
    "article_title": "Patentable Subject Matter",
    "paragraphs": ["1", "2", "3"],
    "ip_domain": "patents",
    "jurisdiction": "international",
    "is_annex_or_appendix": false,
    "cross_references": ["Paris Convention (1967)", "Article 65.4", "Article 70.8", "GATT 1994"],
    "footnotes": [{"footnote_number": 5, "content": "..."}],
    "page_start": 8,
    "page_end": 9,
    "content": "Article 27: Patentable Subject Matter\n1. Subject to the provisions of paragraphs 2 and 3, patents shall be available..."
  }
}
```

The specificity here matters — `part_number`/`section_number`/`article_number`
as separate fields (not one flattened "section" string) is what lets citation
rendering show a precise reference, and what lets `cross_references` power
future multi-hop reasoning without needing the full knowledge-graph stretch
feature.

## 5. Data flow — online (a user question)

A user's first interaction with the assistant is a guided 3-step onboarding,
not free-form chat from message one:

```
Landing page → account creation / login (required, not optional — see
                MVP_SCOPE.md)
        │
        ▼
  Jurisdiction toggle (India / International) selected
        │
        ▼
  STEP 1 — "Describe your product or write its formulation"
        │   user answer → (query + answer + prompt1) → LLM
        │   → suggests a classification from the 6 categories
        ▼
  STEP 2 — "Classify your product" — the 6 categories are shown as options,
        │   each with a description and example products, with the LLM's
        │   suggestion pre-selected/highlighted. User confirms or picks a
        │   different one.
        │   → (user's choice + LLM's suggestion + formulation + prompt2) → LLM
        │   → reconciles the two into a final classification with reasoning
        │   → the DETERMINISTIC RULES ENGINE (not the LLM) assigns the
        │     actual stored classification, using the LLM's reconciled
        │     input as one of its inputs — see §6 below, this is not the
        │     LLM unilaterally deciding
        ▼
  STEP 3 — "What do you want to do with the product?" — options: Patent,
        │   research, sell/business, AYUSH application, export, etc.
        │   → (all prior context + this answer + prompt3) → LLM
        │   → reformulates the actual information need into a retrieval-
        │     optimized query — THIS IS A DISTINCT STEP from final-answer
        │     generation, not the same LLM call
        ▼
  Jurisdiction guardrail check ── if the reformulated query is out of the
        │                          selected jurisdiction's scope, return an
        │                          explicit out-of-scope message here — do
        │                          NOT retrieve or answer. Hard gate, not a
        │                          soft preference (see MVP_SCOPE.md).
        ▼
  Hybrid retrieval, routed to relevant collection(s), using the reformulated
  query + classification + jurisdiction as filters
        │
        ▼
  LLM reasoning, grounded in retrieved evidence only
        │
        ▼
  Citation validation (reject/regenerate on any unvalidated citation)
        │
        ▼
  Composite confidence scoring
        │
        ├── high/medium confidence ──▶ answer shown with citations
        └── low confidence ──▶ escalated to human IP facilitator
```

After this initial 3-step onboarding, subsequent questions in the same
conversation skip straight to the jurisdiction-guardrail-check step, carrying
the established classification and intent forward (see §6) — the user isn't
re-asked to describe their product on every message.

## 6. Classification and intent context threading

Once STEP 2 above produces a final classification, and STEP 3 produces a
declared intent, **both** must persist for the rest of that conversation and
be injected into every subsequent RAG call — to bias retrieval (e.g. weight
toward Section 3(p) content for a classical-medicine classification) and to
be included in the LLM's system context so it doesn't re-ask or contradict
itself.

Implementation: the backend's `Conversation` model carries
`active_classification` and `active_intent` references (nullable, set once
the 3-step onboarding completes). Every `/api/v1/chat` call for that
conversation passes both to the AI layer's query pipeline as parameters —
see `ai/prompts/phases.md` and `backend/prompts/phases.md` for the exact
tasks. The three prompts (`prompt1`, `prompt2`, `prompt3` above) are
versioned runtime prompt templates per `ai/coding_conventions.md` rule 9 —
not inlined strings.

## 7. ABS module (confirmed design, no ML dataset)

Deterministic decision logic (biological resources used → origin → purpose →
prior research) → relevance label + next-steps list. Backed by already-sourced
content: Biological Diversity Act, NBA regulations/forms, Nagoya Protocol. No
training data needed. Ties directly to the `case_law_prior_art` seed cases
(turmeric, neem, Basmati) as worked biopiracy examples when explaining ABS to
a user.

## 8. Testing expectations (applies across all three folders)

Every task in `<folder>/prompts/phases.md` now includes an explicit
verification step — this was added because the first full build didn't match
intent, and untested task completion was part of why. At minimum: automated
tests where the task has real logic, and a documented manual smoke-test
procedure where automated testing isn't practical yet (e.g. "ask these 3
questions and confirm citations point at real WIPO Lex source URLs"). A task
is not `[x]` in `process.md` until its verification step has actually been run
and passed, not just written.

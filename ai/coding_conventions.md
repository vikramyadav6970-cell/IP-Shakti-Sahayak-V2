# ai/coding_conventions.md

Read `/context.md` and `/process.md` before this file. This file governs how code
is written inside `ai/` — the RAG/reasoning layer. **This is the part of the
project where the hard constraints in `context.md` §2 matter most.** Re-read them
before every task in this folder.

## Stack (authoritative — cloud-hosted, no Docker, no local services)

- **Python 3.11+.**
- LLM access via a **provider abstraction** (`LLMProvider` interface with
  `OpenAIProvider` / `AnthropicProvider` / `GeminiProvider` implementations) —
  never call a provider SDK directly from pipeline code. Provider + model name
  come from env vars.
- **Embeddings:** `BAAI/bge-m3` (multilingual, 1024-dim dense vectors, good for
  Hindi+English retrieval) as the default. Keep this behind an
  `EmbeddingProvider` interface too, in case we swap to an API-based embedding
  model later. bge-m3 also produces sparse/lexical vectors natively — use these
  for the hybrid search sparse side rather than standing up a separate BM25
  implementation (see Retrieval below).
- **Vector store: Qdrant Cloud.** Not pgvector, not ChromaDB — decided
  specifically because this project needs five clearly-separated, independently
  filterable collections with fast hybrid (dense+sparse) search, which is
  Qdrant's native design, not something to hand-build on top of a relational
  DB. Free-tier cluster (1GB) is enough for MVP corpus size. Sign-up at
  cloud.qdrant.io; grab the cluster URL + API key into `.env`
  (`QDRANT_URL`, `QDRANT_API_KEY`).
- **Relational data (documents metadata, users, conversations, audit log)**
  stays in the backend's Supabase Postgres — the AI layer does NOT duplicate
  that data in Qdrant. Qdrant payloads carry only what's needed to filter and
  display a retrieved chunk (jurisdiction, section, source_url, etc.), not the
  full document record — that lives in one place (Postgres), referenced by
  `document_id`.
- **Keyword/sparse search:** bge-m3's native sparse output, used as the sparse
  vector in Qdrant's hybrid Query API (prefetch dense + prefetch sparse, fused
  with RRF). Do not hand-roll BM25 or a separate keyword index — Qdrant's
  built-in hybrid query does this in one call.
- **Reranker:** a cross-encoder (e.g. BGE reranker) or Cohere Rerank if an API
  key is available — document which in status.md.
- **Cache:** Upstash Redis — used for Celery broker and any query/answer
  caching. `REDIS_URL` (rediss:// scheme) from `.env`.
- **Orchestration:** LangChain/LlamaIndex may be used for document loaders and
  glue, but the retrieval → evidence-assembly → citation-validation →
  confidence-scoring chain must be code we own and can read end-to-end, not
  hidden inside a framework's black-box chain object. If you use a framework
  "Chain"/"Agent" class for anything in this critical path, justify it
  explicitly in status.md.
- **Background execution:** Celery tasks (triggered by the backend per
  backend/prompts/phases.md T2.3) using Upstash Redis as the broker, or a
  standalone worker process — confirm which with whoever's doing the backend
  Phase 2 tasks.
- **Multilingual (Phase 5):** Bhashini APIs for Hindi ASR/translation/TTS.
- **Evaluation:** RAGAS or an equivalent custom harness.

## The five Qdrant collections (authoritative — do not add/rename without updating this file)

Each is a **separate named Qdrant collection**, not a filtered slice of one big
collection — this is what makes retrieval fast: a query routes to the 1-2
relevant collections (via the intent classifier, Phase 3 T3.2) instead of
searching everything.

| Collection name | Contains | Chunking unit |
|---|---|---|
| `legal_statutory` | Acts & Rules (Patents Act, Biological Diversity Act, GI Act, FSSAI regs, etc.) | One chunk per Section/sub-section/clause — never split a numbered clause mid-way. Prepend a breadcrumb ("Patents Act 1970 › Chapter II › Section 3(p)") into the embedded text itself, not just the payload, so the chunk is self-describing even out of context. |
| `standards_formulations` | API/AFI pharmacopoeial monographs — herb/formulation quality standards | One chunk per monograph if short; if long, sub-chunk by identity/purity/assay/testing-method sections, repeating the monograph + botanical name as a header in every sub-chunk. |
| `case_law_prior_art` | Patent/opposition records, court judgments (starts near-empty — see `ai/data/corpus/seed/case_law_STUB.md`, do not fabricate to fill it) | One chunk per case/record, kept whole. Only split by Facts/Holding/Reasoning once real long judgment text exists, each sub-chunk still carrying the case title+outcome as a repeated header. |
| `procedural_forms_checklists` | Filing forms, application checklists, step sequences | One chunk per form/checklist, rarely split. If 15+ steps, split by phase (Pre-filing / Filing / Post-filing) — never mid-step; sequence integrity matters more than chunk-size uniformity here. |
| `international_export` | Treaties (TRIPS, CBD, Nagoya, WIPO GRATK) + export/market-access requirements by country | Treaties: structure-aware by Article, same pattern as `legal_statutory`. Market-access guidance: chunk by country+topic block (e.g. "USA — labeling requirements"). |

Every collection uses: dense vector size 1024 (bge-m3), distance = Cosine, plus
a named sparse vector for the bge-m3 sparse output. Every collection gets
payload indexes on at minimum `jurisdiction`, `document_type`, `language`,
`status` — unindexed payload filters silently fall back to a full scan and
defeat the entire point of using Qdrant here.

Common payload fields across all five collections (in addition to
collection-specific fields in the seed data / Phase 1 chunker):
`document_id`, `title`, `jurisdiction`, `language`, `source_url`, `source_type`,
`verification_status`, `chunk_index`, `parent_document`.

## Hard rules — these encode the project's actual differentiator, follow them exactly

1. **The LLM never generates a legal claim without retrieved evidence backing it.**
   Every prompt to the LLM must include the retrieved evidence chunks, and the
   system prompt must instruct it to answer only from that evidence and to say so
   explicitly when evidence is insufficient (see context.md §2 rule 3).
2. **Citations are IDs, not free text the LLM writes.** The LLM references evidence
   by the chunk/document IDs it was given; a separate citation validator step
   checks every citation ID in the LLM's output actually exists in the evidence
   set it was given (see Phase 4, T4.2). If a citation can't be validated, reject
   and regenerate (or abstain) — never pass an unvalidated citation through to the
   user.
3. **Product classification is a deterministic rules engine**, not an LLM
   judgment call (context.md §2 rule 6). Encode rules as explicit, testable
   `if/elif` logic or a small rules-table — not a prompt asking the LLM to decide
   the category. The LLM may explain the classification in natural language
   afterward, but must not be the thing deciding it.
4. **Confidence is computed, not asked for.** Never use a raw "rate your
   confidence 0-100" LLM self-report as the confidence score. Compute a composite
   from retrieval score, citation validity, source authority, jurisdiction match,
   and evidence coverage (formula documented in Phase 4, T4.3).
5. **Jurisdiction metadata is mandatory on every chunk** at ingestion time
   (INDIA/USA/EU/INTERNATIONAL/etc.) and every retrieval call must filter by the
   jurisdiction the user asked about — cross-jurisdiction leakage into a single
   answer is a hard bug, not a style issue (context.md §2 rule 2). In Qdrant
   terms: this is a payload filter on the query, not a post-hoc check on results.
6. **Never claim full TKDL access.** Only public TKDL information may be indexed;
   represent TKDL-related answers as a "traditional knowledge pointer," and say so
   explicitly in any prompt/response template that touches TKDL (context.md §5).
7. **Chunking respects document structure, per the table above** — never blindly
   split on a fixed token count without retaining structure as payload metadata;
   citations need to reference an exact section/monograph/form, not "chunk #47."
8. **No fabricated dates, section numbers, case names, or patent numbers** may
   appear anywhere in a prompt template as an "example" that could leak into
   output — even few-shot examples in prompts must use clearly fictional
   placeholders (e.g. "Example Act, Section X") so the LLM never confuses a
   few-shot example with real law.
9. **Prompts are versioned code, not scratch strings.** Keep every system/user
   prompt template in `ai/prompts/` (the *runtime* prompts directory — distinct
   from this `ai/prompts/phases.md` *task* file, don't confuse the two) as a
   separate file with a version comment, not inlined as a Python string literal
   scattered across the codebase.
10. **No custom reimplementation of hybrid fusion, cross-encoder inference, or
    embedding math** — use Qdrant's native Query API for fusion and the
    established libraries named in the Stack section above.
11. **Collection routing before retrieval, not after.** The intent classifier
    (Phase 3, T3.2) should narrow which of the five collections get queried
    before running search, not run search against all five and discard
    irrelevant results — this is the primary lever for retrieval speed, more
    than any index tuning.

## Folder structure

```
ai/
├── coding_conventions.md
├── status.md
├── prompts/
│   └── phases.md              # THIS folder's task prompts (what you're reading)
├── requirements.txt
├── src/
│   ├── ingestion/              # parsing, chunking (per-collection strategies)
│   ├── embeddings/
│   ├── retrieval/              # Qdrant hybrid search, collection routing, reranking
│   ├── classification/         # deterministic rules engine, jurisdiction/intent classifiers
│   ├── abs/
│   ├── reasoning/               # LLM provider abstraction, answer generation
│   ├── citations/               # citation validator
│   ├── confidence/
│   ├── guardrails/
│   ├── multilingual/
│   ├── evaluation/
│   └── prompts/                 # RUNTIME prompt templates (versioned), not task prompts
├── data/
│   └── corpus/                  # curated source documents (or pointers/manifests to them)
└── tests/
    └── eval/                    # the evaluation question set + expected answers
```

## Definition of done for any AI-layer task

- Has at least one automated test (unit test for rules/parsing logic; an eval-set
  regression check for anything retrieval/generation related, once Phase 5's
  harness exists — before that, a small manual smoke test documented in
  status.md is acceptable).
- Every new function/module has a docstring stating its inputs/outputs and, for
  anything touching evidence/citations, explicitly states what guarantee it
  provides (e.g. "guarantees every citation ID returned exists in the input
  evidence set").
- `status.md` and `process.md` updated, including the exact function signature/
  interface if backend depends on calling into this code.

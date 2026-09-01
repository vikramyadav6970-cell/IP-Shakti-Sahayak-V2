# ai/prompts/phases.md

Ready-to-paste prompts for an AI coding agent, one per task. This is the most
domain-sensitive part of the project — every task prompt below tells the agent to
re-read `context.md` §2 and `ai/coding_conventions.md` because getting these wrong
silently produces a system that looks like it works but fabricates law. Don't skip
that instruction when pasting these.

---

## Phase 0 — Environment & setup

### T0.1 — Project scaffold

**Manual prerequisite:** Python 3.11+ installed.

**Prompt:**
```
Read /context.md, /process.md, and /ai/coding_conventions.md in full first.

Task: Scaffold the `ai/` Python project per the folder structure documented in
ai/coding_conventions.md. Include requirements.txt pinning exact versions of every
dependency named in that file's Stack section (and nothing beyond it without
flagging why). Set up pytest configuration and a `tests/` folder skeleton matching
the src/ structure.

When done: update /ai/status.md and flip T0.1 to [x] in /process.md.
```

### T0.2 — LLM provider abstraction

**Manual prerequisite:** an API key for at least one LLM provider (Anthropic,
OpenAI, or Google) — get one from console.anthropic.com, platform.openai.com, or
ai.google.dev and set it in a local `.env` (never commit it; add it to
`.env.example` as a placeholder with a comment on where to get it).

**Prompt:**
```
Read /context.md §3 (architecture decision — provider abstraction, not tied to one
vendor) and /ai/coding_conventions.md first.

Task: Implement `src/reasoning/llm_provider.py`: an `LLMProvider` abstract
interface with a single core method (something like
`generate(system_prompt: str, user_prompt: str, **kwargs) -> str`), and at least
one concrete implementation reading its API key and model name from environment
variables (don't hardcode a model name — read `LLM_PROVIDER` and `LLM_MODEL` env
vars and instantiate the right implementation). Write a small smoke test that
actually calls the real API once (skip it automatically in CI if no key is
present, don't fail the build) to confirm the wiring works end to end.

When done: update /ai/status.md (note which provider was smoke-tested) and flip
T0.2 to [x] in /process.md.
```

### T0.3 — Embedding model smoke test

**Prompt:**
```
Read /ai/coding_conventions.md first.

Task: Implement `src/embeddings/embedding_provider.py` wrapping `BAAI/bge-m3` (via
sentence-transformers or the recommended BGE loading method), behind an
`EmbeddingProvider` interface (`embed(texts: list[str]) -> list[list[float]]`).
Write a smoke test embedding a small English sentence and a small Hindi sentence,
asserting the output vectors have the expected dimensionality and aren't all-zero.
Note the model's embedding dimension in status.md — the backend's pgvector column
needs to match it exactly (flag this as a Cross-part note in /process.md, backend
needs this number for their migration).

When done: update /ai/status.md and flip T0.3 to [x] in /process.md.
```

---

## Phase 1 — Corpus & ingestion

### T1.1 — Reconcile the existing dataset against WIPO Lex, fill gaps

**Manual prerequisite:** none — WIPO Lex (wipolex.wipo.int) is free, no signup.

**Prompt:**
```
Read /context.md §5 (domain facts) and §8 (Changelog), /ARCHITECTURE.md §3
(the five collections), and /MVP_SCOPE.md first.

A dataset has already been downloaded (in /data-staging/ or wherever the human
places it — confirm the path before starting) with this structure:

  India/
    Bio-Piracy/ (TKDL biopiracy PDF)
    Biological diversity Act/ (2023 Act + 2024 Rules)
    Books-Formulations/ (Sowa Rigpa, Ayurveda/Siddha/Unani book lists)
    Drugs & cosmetic act/
    FSSAI Ayurvedic-Aahar Regulations/
    India-IP/ (WIPO Lex Main IP Laws + Implementing Rules, by IP-type folder)
    Patents Act and 2024 rules/
    The Drugs And Magic Remedies (Objectionable Advertisements)/
  International/
    Convention on Biological Diversity/, Madrid System/, Nagoya Protocol/,
    PCT/, Trips/, Wipo Gratk Treaty/

Task: reconcile this against the target scope and fill the known gaps, rather
than re-sourcing from scratch:

1. DEDUP: `indian patent act 1970.pdf` (standalone folder) and
   `India-IP/Main IP Laws/Patents (Inventions)/The Patents Act, 1970,
   India.pdf` are very likely the same document from different sources — sha256
   + title check before ingesting both; keep whichever has cleaner extracted
   text if they differ, note the choice in the manifest.
2. NOT A DUPLICATE — verify and keep both: `Biological diversity Act/
   Biological Diversity Act 2023.pdf` + `Rules 2024.pdf` are the amendment and
   implementing rules; `India-IP/.../Traditional Knowledge (TK)/The
   Biological Diversity Act, 2002, India.pdf` is the original Act. Link all
   three as versions of the same Act in the manifest, ingest all three.
3. FILL GAP — Judgements: there is currently NO case_law_prior_art source
   material in this dataset at all. Source WIPO Lex's India Judgements
   listing, filtered to Patents/Traditional-Knowledge/GI/Biodiversity-tagged
   cases first, then a small number of broadly foundational IP precedent
   cases (e.g. a landmark Section 3(d) case) even if not Ayurveda-specific.
   Verify each against the actual judgment text before including it — don't
   pad this collection with loosely-related content. This is the priority
   item in this task; do it before the smaller gaps below.
4. FILL GAP — Treaties: Hague Agreement (industrial designs) and Budapest
   Treaty (micro-organism deposits) are both in scope per context.md §4 and
   both missing from the International/ folder. Source both from WIPO Lex.
5. FILL GAP — Implementing Rules: `India-IP/Implementing Rules/` has empty
   folders for Industrial Designs, Plant Variety Protection, and Trademarks
   (Patents is at least partly covered by the separate `Patents Act and 2024
   rules/` folder — confirm it actually has the current Patent Rules, not
   just the Act). Source the missing Trademark/Design/Plant-Variety
   implementing rules from WIPO Lex.
6. ROUTE, DON'T EMBED — Books-Formulations: the Sowa Rigpa and Siddha/Unani
   book lists are out of scope (see context.md §5 — Ayurveda-specific
   project). The Ayurveda book list specifically is reference data for the
   classification rules engine (T3.3 — which texts count as "First-Schedule
   authoritative texts"), not retrieval content — extract it into a static
   lookup table/file the classifier code reads, do NOT chunk-and-embed it
   into Qdrant. Confirm this interpretation before treating any of
   Books-Formulations as embeddable corpus content.
7. Bio-Piracy PDF: check whether it documents cases beyond the
   turmeric/neem/Basmati set already in ai/data/corpus/seed/ipr_prior_art.jsonl
   — if it adds genuinely new, verifiable biopiracy cases, source those into
   case_law_prior_art following the same real-content-only standard as the
   existing seed data; if it's describing the same three cases, use it only
   as supplementary framing text, don't create duplicate records.

For every document (existing or newly sourced): record in
ai/data/corpus/manifest.jsonl: title, jurisdiction, document_type, source_url,
fetch_date, sha256, verification_status, target_collection.

VERIFICATION:
1. Report final counts per collection-destination, and explicitly confirm
   case_law_prior_art went from 0 to a meaningfully non-zero count.
2. Confirm the dedup decision (item 1) and the three-Biological-Diversity-
   Act-versions decision (item 2) are both reflected correctly in the
   manifest — spot check by reading the manifest entries, not just trusting
   the count.
3. Confirm the Books-Formulations content is NOT present in the manifest as
   embeddable corpus content — only as a separate reference-data file path.

When done: update /ai/status.md's corpus manifest section and flip T1.1 to
[x] in /process.md.
```

### T1.2 — Per-document chunking-strategy analysis

**Prompt:**
```
Read /ARCHITECTURE.md §4a (why this is two phases, not one) and
/ai/coding_conventions.md first.

Task: Implement `src/ingestion/strategy_analyzer.py`. Given a parsed
document's text (see parsing note below) and its manifest metadata
(document_type, target_collection), analyze its actual structure and produce
a structured chunking-strategy config — do NOT hardcode one regex and assume
it fits every document. The config should specify: the split-marker pattern
for this specific document (e.g. "Article N" for a treaty, "Monograph:" for a
pharmacopoeial source, numbered form fields for a filing form), any
sub-splitting rule for oversized sections, and what header/breadcrumb text to
prepend to each resulting chunk.

Parsing: use PyMuPDF for PDF text extraction, BeautifulSoup for HTML; fall
back to Tesseract OCR only if a PDF has no extractable text layer (detect
this, don't always OCR).

Log the proposed strategy per document BEFORE it's used for actual chunking
(T1.3) — write it to a reviewable file (e.g.
ai/data/corpus/chunking_strategies.jsonl), one entry per document. This log
is what lets a human or agent catch a bad strategy on document 1 instead of
after 17,000 chunks — treat producing this log as the actual deliverable of
this task, not a side effect.

VERIFICATION:
1. Run against at least one document from each of the five target
   collections (a WIPO Lex Act, a pharmacopoeial monograph source, a filing
   form, a treaty, and — once T1.1's gap-fill lands — a judgment) and
   manually review the 5 resulting strategy configs for plausibility before
   proceeding to T1.3.
2. Specifically check: does the proposed strategy for a Drugs Rules-style
   document (short numbered items like "5. Refractometer") correctly avoid
   producing near-empty single-heading chunks? This is the exact failure
   pattern from an earlier attempt at this project — confirm the strategy
   analysis catches it before chunking runs, not after.

When done: update /ai/status.md and flip T1.2 to [x] in /process.md.
```

### T1.3 — Chunk execution + payload assembly

**Prompt:**
```
Read /ARCHITECTURE.md §4b (canonical payload schema) and
/ai/coding_conventions.md rule 7 first.

Task: Implement `src/ingestion/chunker.py`: given a document's parsed text and
the chunking-strategy config from T1.2, execute the split deterministically
and assemble each chunk's payload matching the schema in ARCHITECTURE.md §4b
— adapt the field set per collection (legal_statutory/international_export
use the full example shown there; standards_formulations needs
monograph_name/botanical_name/quality_parameters fields instead;
procedural_forms_checklists needs form_name/steps/required_documents;
case_law_prior_art needs the fields already established in
ai/data/corpus/seed/ipr_prior_art.jsonl — reuse that schema rather than
inventing a new one for consistency with the existing seed data).

Every chunk gets: document_id, jurisdiction, chunk_index, parent_document,
source_url, verification_status, plus the collection-specific fields above.

VERIFICATION:
1. Run end-to-end on the same 5 sample documents from T1.2's verification.
   For each, report: chunk count, token-length distribution (min/median/max),
   and manually inspect 3 chunks per document for correctness (real content,
   not duplicated headings, correct section/field values populated).
2. Explicit regression check against the earlier failure: confirm the
   under-50-token chunk percentage across the sample is low (single digits,
   not the 67% seen previously) and that no sampled chunk contains its own
   heading text duplicated as its body.
3. Only after both checks pass on the 5-document sample, run across the full
   reconciled dataset from T1.1, and re-run the same distribution check on
   the full corpus before proceeding to Phase 2.

When done: update /ai/status.md and flip T1.3 to [x] in /process.md.
```

---

## Phase 2 — Retrieval


### T2.1 — Embedding generation + pgvector indexing

**Prompt:**
```
Read /ai/coding_conventions.md and check /backend/status.md for the exact
Postgres connection details and whether the pgvector column/table already exists
(it should, from backend Phase 1 T1.1's Document/DocumentVersion models — but the
chunk-level table with the vector column is this task's responsibility to define
unless backend already scaffolded it; confirm and avoid duplicating).

Task: Implement `src/embeddings/indexer.py`: takes chunks from T1.3, embeds them
via the T0.3 EmbeddingProvider, and writes them to a `chunks` table with a
pgvector column (dimension must match T0.3's noted embedding size), plus all the
chunk metadata as regular columns for filtering (jurisdiction, document_type,
section, etc. — not buried only in a JSON blob, since these need indexed,
filterable columns for the hybrid search in T2.3). Write a migration for this
table if backend hasn't already created it (coordinate — see Cross-part notes in
process.md) using the same Alembic setup as backend, or a clearly-documented
separate migration path if the AI layer manages this table independently — decide
and document which in status.md.

When done: update /ai/status.md and flip T2.1 to [x] in /process.md.
```

### T2.2 — Keyword (BM25/FTS) index

**Prompt:**
```
Task: Implement `src/retrieval/keyword_search.py` using Postgres full-text search
(a `tsvector` column + GIN index on the chunks table from T2.1) or `rank_bm25` —
pick one and document why in status.md (Postgres FTS is likely simpler given
everything already lives in Postgres; only reach for a separate BM25 library if
FTS proves insufficient for legal-text quirks like "Section 3(p)" tokenization —
test this specifically, since keyword search on section references like "3(p)"
needs to actually work, not just prose search).

When done: update /ai/status.md and flip T2.2 to [x] in /process.md.
```

### T2.3 — Hybrid retrieval + reranking

**Prompt:**
```
Read /context.md §2 and /ai/coding_conventions.md first.

Task: Implement `src/retrieval/hybrid_retriever.py`: given a query, jurisdiction
filter, and optional document_type/intent filter, run both vector search (T2.1)
and keyword search (T2.2), merge results (e.g. reciprocal rank fusion), then apply
a cross-encoder reranker (or Cohere Rerank if an API key is configured) to produce
the top 5-8 evidence chunks. The jurisdiction filter must be a hard filter applied
at the query stage, not a post-hoc soft preference — this is the mechanism that
enforces context.md §2 rule 2 (never conflate jurisdictions) at the retrieval
layer. Write tests with a small fixture set of chunks across 2 jurisdictions,
asserting a query filtered to jurisdiction=INDIA never returns a USA-tagged chunk.

When done: update /ai/status.md with the final function signature (backend's
Phase 3 T3.1 will call into this indirectly via the query pipeline in T4.1 below)
and flip T2.3 to [x] in /process.md.
```

---

## Phase 3 — Classification & routing

### T3.1 — Jurisdiction classifier

**Prompt:**
```
Read /context.md §2 rule 2 and /ai/coding_conventions.md first.

Task: Implement `src/classification/jurisdiction_classifier.py`: given a user
question and the jurisdiction explicitly selected in the UI (this is passed
through, not purely inferred — the frontend's jurisdiction toggle from
frontend/prompts/phases.md T1.2 is the primary signal), resolve the concrete
jurisdiction filter value(s) to use in retrieval (e.g. "INDIA", or "USA" +
"INTERNATIONAL" if the question also references a treaty/WIPO). This can be
mostly rule-based (map UI selection → filter value) with a light LLM/keyword
assist only for detecting when a question explicitly names a different
jurisdiction than the one selected (e.g. user has India selected but asks "what
does US law say") — in that case, surface a clear signal for the reasoning layer
to explicitly separate both, don't silently switch.

When done: update /ai/status.md and flip T3.1 to [x] in /process.md.
```

### T3.2 — Intent classifier

**Prompt:**
```
Task: Implement `src/classification/intent_classifier.py`: classify a question
into one of: PATENT, TRADEMARK, GI, COPYRIGHT, DESIGN, PLANT_VARIETY,
TRADE_SECRET, ABS, TKDL, PRODUCT_CLASSIFICATION, DRUG_REGULATION,
FOOD_REGULATION, COSMETIC, EXPORT, INTERNATIONAL_IP, GENERAL. Use a lightweight
approach appropriate for the MVP (keyword/rule-based first pass, LLM classification
as fallback for ambiguous cases — don't default straight to an LLM call for every
message if a rule confidently matches, for latency/cost reasons). This output
feeds the retrieval filter in T2.3 (narrows which document_types/sections are
searched). Write tests with representative example questions for each intent.

When done: update /ai/status.md and flip T3.2 to [x] in /process.md.
```

### T3.3 — Deterministic product classification rules engine + LLM reconciliation (steps 1-2 of the onboarding flow)

**Prompt:**
```
Read /ARCHITECTURE.md §5 (the 3-step onboarding flow) and §6, /context.md §2
rule 6 and §5 (FSSAI Ayurveda-Aahara distinction), then /ai/coding_conventions.md
rule 3.

Task: implement the AI-layer side of onboarding steps 1-2:

STEP 1 — Implement `src/prompts/classification_suggest.md` (versioned prompt
template, per coding_conventions rule 9) and the function that calls it:
given the user's free-text product/formulation description, the LLM suggests
one of the 6 categories (classical/generic medicine, patent-or-proprietary
medicine, new/non-classical drug, phytopharmaceutical, Ayurveda-Aahar/
nutraceutical, cosmetic) with brief reasoning. This is a suggestion only, not
the final classification.

STEP 2 — Implement `src/classification/product_classifier.py` as an explicit,
auditable rules engine (not an LLM prompt) — this is what actually assigns
the FINAL classification, taking as input: the user's confirmed/corrected
category choice (from the 6-option UI, each option shown with its
description and examples), the LLM's step-1 suggestion, and the original
formulation description. Where the user's choice and the LLM's suggestion
disagree, implement `src/prompts/classification_reconcile.md` (a second
versioned prompt) that reasons about the disagreement and produces a
recommendation — but the rules engine, not this prompt, makes the final
determination, using the reconciled recommendation as one input among its
explicit rules. Return: classification label, regulatory pathway
description, and the list of rules that fired (for the `rules_fired` audit
field on backend's Classification model). Encode the FSSAI Ayurveda-Aahara
distinction (food vs. drug) as an explicit rule per context.md §5, not an LLM
inference.

Write thorough unit tests: one per rule branch, edge cases that should return
UNCLEAR rather than guessing, and specifically a disagreement case (user
picks X, LLM suggested Y) to confirm the reconciliation path is exercised,
not just the agreement path.

This is the function backend's classification endpoint calls into — document
its exact signature and return shape in status.md as soon as it's stable, and
flag it in process.md's Cross-part notes.

When done: update /ai/status.md and flip T3.3 to [x] in /process.md.
```

### T3.3b — Intent capture and query reformulation (step 3 of the onboarding flow)

**Prompt:**
```
Read /ARCHITECTURE.md §5 (step 3 specifically — this is a DISTINCT pipeline
stage from final-answer generation, not the same LLM call) first.

Task: Implement `src/prompts/query_reformulate.md` (versioned prompt) and the
function that calls it: given the full onboarding context so far (formulation
description, final classification from T3.3, and the user's declared intent
from a fixed option set — Patent, Research, Sell/Business, AYUSH Application,
Export, Other), produce a retrieval-optimized query — a structured
representation of what needs to be searched for (not just the raw user text),
including which collection(s) are likely relevant given the intent (e.g.
"Patent" intent weights toward legal_statutory + case_law_prior_art;
"AYUSH Application" weights toward procedural_forms_checklists +
standards_formulations).

This reformulated query, not the user's raw step-1/step-3 text, is what feeds
T2.3's hybrid retrieval.

VERIFICATION: test with at least 4 different intent selections against the
same underlying formulation/classification, and confirm the reformulated
query and collection-routing hints genuinely differ by intent — if "Patent"
and "Research" intents produce near-identical reformulated queries, the
reformulation isn't actually using the intent signal, fix that before
marking done.

When done: update /ai/status.md and flip T3.3b to [x] in /process.md.
```

### T3.4 — ABS assessment engine

**Prompt:**
```
Read /context.md §5 (Biological Diversity Act facts) first.

Task: Implement `src/abs/abs_engine.py`: given biological resources used, origin,
purpose (commercial/research), and whether research/access already occurred,
return a relevance label (HIGH/MEDIUM/LOW/NOT_APPLICABLE) and an ordered
next-steps list (identify applicable authority → determine approval/intimation
requirement → identify benefit-sharing obligations → preserve source/provenance
information), matching what frontend renders. Like T3.3, this should be
primarily rule-based given the compliance stakes — document any place you use LLM
assistance and why.

When done: update /ai/status.md with the function signature (backend depends
on it) and flip T3.4 to [x] in /process.md.
```

### T3.5 — Conversation-level classification and intent context threading

**Prompt:**
```
Read /ARCHITECTURE.md §6 (classification and intent context threading) and
/context.md §8 Changelog first.

Task: Modify the query pipeline (T4.1 below — coordinate if it's already built)
to accept optional `active_classification` and `active_intent` parameters
(the results from T3.3/T3.3b, if the conversation already completed the
3-step onboarding). When present, use both to:
1. Bias retrieval: pass them as additional filter/boost hints to T2.3's
   hybrid retrieval — e.g. a "classical/generic medicine" classification
   should weight legal_statutory retrieval toward Section 3(p)-adjacent
   content; a "Patent" intent should weight toward case_law_prior_art.
2. Include both in the LLM's system context (T4.1) so the model doesn't
   re-ask what's already established, and doesn't produce an answer that
   contradicts them.

This does not replace T3.3/T3.3b's onboarding flow — it's the mechanism that
carries their *results* forward through the rest of a conversation. The
backend is responsible for persisting and passing these parameters (see
backend/prompts/phases.md) — this task is the AI-layer side that consumes
them.

VERIFICATION:
1. Unit test: call the query pipeline twice in sequence with the same
   `active_classification`/`active_intent` set — confirm the second call's
   retrieval results are influenced by them (different top-k results with vs.
   without, for a query that's ambiguous without this context).
2. Manual smoke test: simulate a full conversation — complete the 3-step
   onboarding (classical/generic medicine, intent=Patent), then ask "can I
   protect this?" without restating anything — confirm the answer correctly
   references Section 3(p) and patent-specific content without needing to
   re-ask the onboarding questions.

When done: update /ai/status.md and flip T3.5 to [x] in /process.md.
```

---

## Phase 4 — Reasoning & trust layer

### T4.1 — Query pipeline (evidence-grounded answer generation)

**Prompt:**
```
Read /context.md §2 rules 1 and 3, and /ai/coding_conventions.md rules 1, 8, 9
before writing a single line of prompt text.

Task: Implement `src/reasoning/query_pipeline.py`, the top-level entrypoint
(`query(question, jurisdiction, language, conversation_history) -> QueryResult`)
backend's Phase 3 T3.1 calls into. It should:
1. Run T3.1 (jurisdiction) and T3.2 (intent) classifiers.
2. Run T2.3 hybrid retrieval with the resulting filters.
3. If retrieval returns no evidence above a minimum relevance threshold, skip the
   LLM call entirely and return an explicit abstention result ("insufficient
   authoritative evidence") — don't call the LLM to "try anyway."
4. Otherwise, build a prompt (from a versioned template in `src/prompts/`, per
   coding_conventions rule 9) that gives the LLM the evidence chunks with their
   IDs and instructs it to answer only from that evidence, citing chunk IDs
   inline, and to explicitly flag any part of the question it cannot answer from
   the evidence.
5. Pass the LLM's raw output to the T4.2 citation validator (build a stub for now
   if T4.2 isn't done yet, but do not skip calling it once it exists — never ship
   this pipeline without validation wired in).
6. Compute confidence via T4.3.
7. Return a `QueryResult` matching backend's documented `/api/v1/chat` contract
   (check backend/status.md).

When done: update /ai/status.md with the finalized function signature and flip
T4.1 to [x] in /process.md. Add a Cross-part note — this is what unblocks backend
T3.1 fully.
```

### T4.2 — Citation validator

**Prompt:**
```
Read /ai/coding_conventions.md rule 2 first.

Task: Implement `src/citations/validator.py`: given the LLM's raw answer (with
inline citation markers referencing chunk IDs) and the actual evidence chunk set
it was given, verify every citation ID referenced exists in that evidence set and
that the cited chunk's text plausibly supports the sentence citing it (a
similarity/overlap check is enough for MVP — this doesn't need to be a second LLM
call, though it can fall back to one for ambiguous cases if you document that
tradeoff). If any citation fails validation, do not silently drop it — either
strip that specific unsupported sentence and note the reduction, or trigger a
regeneration/abstention depending on how much of the answer is affected (encode a
clear threshold and document it). Write tests: a case with all-valid citations
passes through unchanged; a case with a fabricated citation ID is caught and
handled per your documented policy.

When done: update /ai/status.md and flip T4.2 to [x] in /process.md.
```

### T4.3 — Composite confidence scorer

**Prompt:**
```
Read /ai/coding_conventions.md rule 4 first.

Task: Implement `src/confidence/scorer.py` computing a confidence score from a
weighted combination of: retrieval_score (top result relevance), citation_score
(fraction of citations that passed T4.2 validation), source_authority_score
(e.g. statute/treaty > guideline > secondary source — define an explicit
authority ranking table), jurisdiction_match (exact vs. inferred), and
answer_evidence_coverage (fraction of the answer's claims that carry a citation).
Document the exact weights and formula in a comment at the top of the file and in
status.md — this needs to be explainable, since the frontend shows a HIGH/MEDIUM/
LOW label derived from it and backend's requires_human_review flag depends on it.
Set and document the LOW threshold that triggers requires_human_review=true.

When done: update /ai/status.md and flip T4.3 to [x] in /process.md.
```

### T4.4 — Guardrails / abstention rules

**Prompt:**
```
Read /context.md §2 and §5 (esp. the TKDL restriction) and
/ai/coding_conventions.md rules 6 and 8 first.

Task: Implement `src/guardrails/rules.py`, a checklist applied to every answer
before it's returned from T4.1:
- Refuse (return an explicit "insufficient evidence" response) if no authoritative
  evidence was retrieved — already partly handled in T4.1, consolidate the logic
  here so it's a single, testable module.
- Never let a TKDL-related answer imply full database access — enforce via a
  check on the response text/template, not just prompt instruction (prompt
  instructions can be insufficient alone; add a template-level guarantee, e.g. the
  TKDL response always uses a fixed "traditional knowledge pointer" phrasing block
  you control in code, not free LLM text for that specific disclaimer).
- Never let an answer mix jurisdictions without explicit labeling — check that if
  evidence chunks from more than one jurisdiction were used, the answer template
  visibly separates them (this can be enforced by how T4.1 assembles multi-
  jurisdiction answers, structurally, rather than trusting the LLM to remember).
- Always append the "information, not legal advice" disclaimer at the pipeline
  level (not relying on the frontend alone) so it's present even if an API
  consumer bypasses the UI.

Write tests for each guardrail with a deliberately adversarial input (e.g. a
crafted evidence set from two jurisdictions) to confirm the rule actually catches
it, not just the happy path.

When done: update /ai/status.md and flip T4.4 to [x] in /process.md.
```

### T4.5 — Jurisdiction out-of-scope guardrail (MVP_SCOPE.md item 5)

This is one of the most important behavioral requirements in the whole system —
the first build likely answered international questions while India was
selected (or vice versa) instead of refusing. Get this one right.

**Prompt:**
```
Read /MVP_SCOPE.md item 4 and /ARCHITECTURE.md §5 (online data flow — this gate
sits BEFORE retrieval, not after) first.

Task: Implement a hard jurisdiction-scope gate at the start of the query
pipeline (before T2.3 retrieval runs, not as a post-hoc filter on results):
given the user-selected jurisdiction (India or International) and the
classified intent (T3.2) of the question, determine whether the question is
answerable within the selected jurisdiction's scope. If the question is
clearly about a different jurisdiction than selected (e.g. India selected but
the question asks about USA/EU patent law, or International selected but the
question is purely about an India-specific procedural detail with no
international counterpart), do NOT proceed to retrieval or generate an
answer — return an explicit out-of-scope response naming the mismatch and
suggesting the user switch the jurisdiction toggle.

This must be a genuine hard gate, not a soft LLM instruction the model can be
talked past — implement the scope check as its own function with clear
pass/fail logic (rule-based on the intent classifier's jurisdiction signal,
with LLM assistance only for genuinely ambiguous cases, same pattern as T3.1's
jurisdiction classifier), called before any retrieval or LLM reasoning happens
for out-of-scope cases.

VERIFICATION (this is the test suite that actually matters for this task):
1. Write at least 6 test cases: 3 where India is selected and the question is
   genuinely India-scoped (should proceed normally), 3 where India is
   selected but the question is clearly international-only (e.g. "what are
   the PCT filing requirements in the US") — these 3 MUST return the
   out-of-scope response, not an answer.
2. Repeat symmetrically for International selected + India-specific
   questions.
3. Include at least one adversarial case where the question tries to embed
   an out-of-scope request inside an in-scope-sounding wrapper (e.g. "for my
   India filing, what does the US require") — confirm the gate still catches
   the out-of-scope portion rather than answering it because the sentence
   also mentions India.
4. Manually run these same test questions through the actual deployed/running
   system (not just the unit test) before marking this done — this is
   specifically the kind of behavior that can pass a unit test on the
   function in isolation but still fail end-to-end if the gate isn't actually
   wired into the real request path.

When done: update /ai/status.md and flip T4.5 to [x] in /process.md.
```

---

## Phase 5 — Multilingual, evaluation, stretch

### T5.1 — Hindi support (Bhashini confirmed unavailable — do not start before MVP_SCOPE.md's MVP list is done)

**Status: explicitly deferred per MVP_SCOPE.md item 13.** English-only is the
MVP. Do not pick this up early. Left here so the plan is complete, per the
instruction to keep the full roadmap documented even while focus stays on MVP.

Bhashini API access was investigated and confirmed unavailable for this
project — do not attempt to register for it again without new information.
Two alternatives, in preference order:

**Default: use the existing LLM provider directly for translation.** No new
service or API key — the same provider already wired in T0.2 can translate
Hindi↔English as part of the prompt, with the query pipeline (T4.1) framing
it as a distinct translation step (not blended into the reasoning step) so
translation quality can be checked independently of answer quality. Simpler
integration, one fewer service to maintain, consistent with this project's
general preference for fewer moving parts.

**Fallback if LLM-based translation proves too costly at volume or quality is
insufficient:** AI4Bharat's IndicTrans2 (open-source, self-hostable or via
HuggingFace Inference API), which is purpose-built for Indian languages and
free to run.

**Prompt (when this is actually picked up, not before):**
```
Read /MVP_SCOPE.md to confirm the MVP list is genuinely complete before
starting this — this task is explicitly deferred.

Read /context.md §8 Changelog (Bhashini decision) and /ai/coding_conventions.md
first.

Task: Implement `src/multilingual/translator.py` using the existing LLM
provider (T0.2) for Hindi↔English translation — a distinct, explicitly-labeled
translation call, not blended into the reasoning prompt. Wire Hindi question
handling into T4.1's pipeline: detect/accept a `language="hi"` input,
translate to English for retrieval, run the pipeline as normal, then translate
the final answer back to Hindi — but do NOT translate citation source
titles/section references themselves; those must remain tied to the original
authoritative source text/citation (only translate the natural-language
explanation, not the legal reference itself). Keep the interface
provider-agnostic enough that swapping to IndicTrans2 later is a config
change, not a rewrite, in case translation volume or quality requires it.

VERIFICATION: translate a set of 10 known English legal Q&A pairs to Hindi and
back, and have a Hindi speaker (not just an automated check) confirm the
round-trip preserves meaning, especially for legal terms — automated
similarity scoring alone is not sufficient for this specific check given the
stakes of a mistranslated legal answer.

When done: update /ai/status.md and flip T5.1 to [x] in /process.md.
```

### T5.2 — Evaluation harness

**Prompt:**
```
Read /context.md §4 and /ai/coding_conventions.md first.

Task: Build `ai/tests/eval/questions.jsonl`: 100 questions categorized
approximately as 25 Patent / 20 Regulatory / 15 ABS / 10 Trademark / 10 Product
classification / 10 International / 10 TKDL, each with: expected_answer_summary,
expected_source (document + section), expected_jurisdiction, expected
classification (where applicable). Then implement
`src/evaluation/run_eval.py` measuring: retrieval accuracy (correct source in top-
k), citation accuracy (citations that pass T4.2 validation), answer accuracy
(rough match against expected_answer_summary — can use an LLM-as-judge approach
for this specific metric, document if so), abstention accuracy (does it correctly
abstain on out-of-scope/insufficient-evidence questions — include some
deliberately unanswerable questions in the set for this), and multilingual
quality (a subset of the 100 asked in Hindi via T5.1, once available). Output a
summary report (the numbers the frontend admin dashboard in frontend T4.4 will
eventually display — expose them via a simple JSON file or endpoint backend can
read).

When done: update /ai/status.md with the eval results summary and flip T5.2 to
[x] in /process.md.
```

### T5.3 — TKDL public-information pointer

**Prompt:**
```
Read /context.md §2 rule 5 and §5 again — this task exists specifically to
implement that constraint correctly.

Task: Implement `src/reasoning/tkdl_pointer.py`: a fixed, code-controlled response
template (not free LLM generation) used whenever a query's intent is TKDL-related,
stating that full TKDL database access is restricted to patent offices under
access agreements, surfacing only the publicly available TKDL information already
in the corpus (from T1.1), and directing the user to tkdl.res.in for anything
beyond that. Wire this into T4.1's pipeline so TKDL-intent queries always pass
through this template rather than relying on prompt instructions alone.

When done: update /ai/status.md and flip T5.3 to [x] in /process.md.
```

### T5.4 — Stretch: knowledge graph & agentic orchestration

**Prompt (do not start until everything above is `[x]`):**
```
Read /context.md §4 — this is explicitly the last-priority stretch phase; confirm
with /process.md that Phases 0-4 and T5.1-T5.3 are actually done before starting
this.

Task (two independent sub-tasks — do either or both, they don't depend on each
other):

A) Knowledge graph: stand up Neo4j (add to docker-compose, coordinate with backend
if it should live in the shared compose file or a separate one — document the
decision), and model a graph capturing relationships like Product-contains->
BiologicalResource, Product-based_on->AyurvedicText, Law-has_section->Section,
Section-governs->ProductCategory. Use it to answer genuinely multi-hop questions
(e.g. "does my GI-tagged formulation also need Nagoya clearance for export to the
EU?") that hybrid retrieval alone struggles with. This supplements, not replaces,
the citation-grounded RAG pipeline — every graph-derived claim still needs to
trace to a source document.

B) Agentic orchestration: for complex multi-jurisdiction, multi-step questions
(e.g. "I want to sell in India, USA and Germany — what should I do?"), implement a
planner that decomposes the question into sub-queries (product classification,
India IP research, India regulatory research, USA research, EU research, ABS
analysis), runs each through the existing T4.1 pipeline, and merges results into
one structured response. Do not use an agent framework for simple single-turn
questions — this path should only trigger for genuinely multi-step requests
(gate it with a simple heuristic or the intent classifier from T3.2).

When done: update /ai/status.md and flip T5.4 to [x] in /process.md.
```

# ai/data/corpus/seed/README.md

## What this is

A small, hand-verified starter dataset matching the vector-DB schemas in
`AYUSH_SIH_Vector_DB_Collections_and_Schemas` — enough real records to get the
ingestion → embedding → retrieval → citation pipeline running end to end before
the full 20-50 document corpus (T1.1) is assembled.

**This is not the full corpus. It is a seed of ~15 records to prove the pipeline
works on real content.** Do not present this as the finished corpus in a demo
without saying so — it's a foundation, not the deliverable.

## Verification tiers — read this before using any record

Every record has a `verification_status` field. There are three tiers, and they
must be treated differently:

| Status | Meaning | Safe to answer users with? |
|---|---|---|
| `VERIFIED_FACTS_PARAPHRASED_TEXT` | The underlying facts (case outcomes, patent numbers, dates, statute existence) were confirmed against multiple independent sources. The `text` field is a **paraphrase**, not a verbatim quote — I could not confirm word-for-word statute/document text with enough confidence to present it as exact. | Yes, for the facts. **No, for exact statutory wording** — confirm against India Code / the primary source before quoting it verbatim to a user. |
| `VERIFIED_CORE_FACTS_SOME_FIELDS_UNCONFIRMED` | Core facts (what happened, outcome) are solid; specific fields (exact filing date, exact grant date) are left `null` because I could not verify them precisely rather than guess. | Yes for what's populated. The `null` fields need a human to fill in from the primary source (linked in `source_url`). |
| `SCHEMA_EXAMPLE_NOT_REAL` | Fabricated, for pipeline/schema testing only. Title and IDs are prefixed `EXAMPLE_`. | **Never.** Must not be embedded into the same collection as real data without this flag surviving into retrieval-time filtering — safest is to not ingest these into the actual vector DB at all; keep them for unit tests only. |

This mirrors the project's own hard rule in `ai/coding_conventions.md`: never present
fabricated or unverified legal content as authoritative. These tiers exist so the
ingestion pipeline (and any human reviewing this data) can tell the difference
at a glance.

## Files

- `legal_knowledge.jsonl` — 6 records: Patents Act 1970 §3(p) and §3(d), the
  Biological Diversity Act's core ABS obligation, FSSAI Ayurveda-Aahar's
  food/drug boundary, TRIPS Article 27.1, the Nagoya Protocol's PIC/MAT
  framework. All `VERIFIED_FACTS_PARAPHRASED_TEXT`.
- `ipr_prior_art.jsonl` — 3 records: the turmeric, neem, and Basmati
  traditional-knowledge patent disputes. These are your strongest demo
  material — real, well-documented, exactly the kind of case IP-SAKTI exists to
  help someone understand. `VERIFIED_CORE_FACTS_SOME_FIELDS_UNCONFIRMED` (dates
  noted above).
- `ayush_tk.jsonl` — 2 records: general, safe, well-corroborated traditional-use
  facts for turmeric and neem, deliberately *not* claiming a specific classical-
  text chapter/verse citation I couldn't verify. Treat these as placeholders —
  the real `ayush_tk` collection needs sourcing from the CCRAS e-Samhita/APTA
  Digital Library per `ai/prompts/phases.md` T1.1.
- `case_law_STUB.md` — deliberately empty of records. I could not find a real
  Indian court judgment (as opposed to a patent-office administrative/opposition
  proceeding) squarely on point for Section 3(p) that I could verify with
  confidence. The turmeric/neem/basmati matters were patent-office reexamination
  or opposition proceedings, not court judgments, so they're filed under
  `ipr_prior_art`, not `case_law`. Don't fabricate a case here to fill the gap —
  leave it empty until a human sources a real one (or confirms this collection
  starts genuinely empty for the MVP demo).
- `schema_examples_DO_NOT_EMBED.jsonl` — fictional `regulatory_standards` and
  `market_access` records, clearly marked, for testing the ingestion pipeline's
  handling of those two collections before real content exists. **Do not run
  these through the real embedding/indexing pipeline into the production
  vector DB** — use them only in unit tests that need a well-formed but disposable
  input.
- `load_seed.py` — script that embeds and inserts `legal_knowledge.jsonl`,
  `ipr_prior_art.jsonl`, and `ayush_tk.jsonl` into Postgres/pgvector. Does not
  touch `schema_examples_DO_NOT_EMBED.jsonl` by design.

## What to do next (human + agent)

1. Run `load_seed.py` against a local dev DB to prove the ingestion → embedding →
   retrieval path works (this is effectively a fast-tracked version of Phase 1
   T1.2/T1.3 + Phase 2 T2.1 using pre-chunked data instead of raw PDFs).
2. Use `ai/tests/eval/questions_seed.jsonl` as the first 8 rows of the real
   100-question eval set in Phase 5 T5.2 — it's already grounded in this seed
   data, so it's usable immediately, not just a format example.
3. Treat T1.1 in `ai/prompts/phases.md` as still open — this seed does not
   replace curating the full corpus.

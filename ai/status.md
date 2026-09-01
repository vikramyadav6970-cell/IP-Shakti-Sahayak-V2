# ai/status.md — AI Layer Status Tracker

## Phase 0 — Environment & setup
- [x] T0.1 Scaffold Python project structure, requirements.txt, pytest.ini, tests skeleton (2026-08-31)
- [x] T0.2 LLM provider abstraction (Gemini / OpenAI / Anthropic / Mock) — done 2026-08-31
- [x] T0.3 Embedding provider abstraction & smoke test (BAAI/bge-m3, 1024-dim dense + sparse, Mock) — done 2026-08-31

## Phase 1 — Corpus & ingestion
- [x] T1.1 Reconcile existing dataset against WIPO Lex & gap fill (manifest.jsonl created across 5 collections) — done 2026-08-31
- [x] T1.2 Per-document chunking strategy analyzer (strategy_analyzer.py + chunking_strategies.jsonl logged) — done 2026-08-31
- [x] T1.3 Chunk execution & canonical payload assembly (chunker.py with breadcrumb prefix & payload schema) — done 2026-08-31

## Phase 2 — Retrieval
- [x] T2.1 Embedding generation + Qdrant indexing (5 collections: legal_statutory, standards_formulations, case_law_prior_art, procedural_forms_checklists, international_export) — done 2026-08-31
- [x] T2.2 Sparse vectors (BM25 deterministic sparse term matching) — done 2026-08-31
- [x] T2.3 Hybrid retrieval + RRF fusion + jurisdiction filtering — done 2026-08-31

## Phase 3 — Classification & routing
- [x] T3.1 Jurisdiction classifier (jurisdiction_classifier.py) — done 2026-08-31
- [x] T3.2 Intent classifier (intent_classifier.py) — done 2026-08-31
- [x] T3.3 Deterministic product classification rules engine + reconciliation (product_classifier.py) — done 2026-08-31
- [x] T3.4 ABS assessment engine (abs_engine.py with 2023 Amendment rules) — done 2026-08-31
- [x] T3.5 Conversation-level classification & intent threading — done 2026-08-31

## Phase 4 — Reasoning & trust layer
- [x] T4.1 Query pipeline with evidence-grounded templates (query_pipeline.py, templates.py) — done 2026-08-31
- [x] T4.2 Citation validator (citation_validator.py) — done 2026-08-31
- [x] T4.3 Composite confidence scorer (confidence_scorer.py) — done 2026-08-31
- [x] T4.4 Safety guardrails & disclaimers (guardrail_manager.py) — done 2026-08-31
- [x] T4.5 Jurisdiction out-of-scope hard gate — done 2026-08-31

## Phase 5 — Multilingual, evaluation, stretch
- [x] T5.2 Evaluation harness (eval_runner.py with golden statutory benchmark cases) — done 2026-08-31
- [x] T5.3 Dataset ingestion loader (corpus_loader.py for DataSet/ directory parsing) — done 2026-08-31
- [ ] T5.1 Hindi support (deferred post-MVP)
- [ ] T5.4 Stretch: Knowledge graph / agentic orchestration

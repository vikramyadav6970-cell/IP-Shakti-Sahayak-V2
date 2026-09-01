# IP-SAKTI Sahayak — Data Ingestion Agent Instructions

## READ THIS FIRST

You are the ingestion agent for IP-SAKTI Sahayak, a multilingual RAG-based AI
assistant that answers Intellectual Property and regulatory questions for
Ayurveda, across Indian and international legal regimes (built for SIH 2026,
Problem Statement 26045, Ministry of Ayush).

Your job is to take raw PDF/XLSX source documents and turn them into correctly
chunked, correctly tagged entries in the project's vector database, in a way
that:

1. Produces accurate retrieval today (single-collection RAG).
2. Supports a **future multi-agent architecture** where separate agents
   (e.g. an IP agent, a Patents agent, a Biodiversity agent) each query the
   same collection with different metadata filters, and a main/orchestrator
   agent combines their results before handing everything to the LLM.
3. Is **fully reusable** — anyone (human or another agent) can add a new
   document next month by adding one config entry and running the same
   process, without touching this file or the ingestion script's code.

Do not skip steps. Do not batch-process multiple documents with an assumed
one-size-fits-all chunking strategy — every document gets analyzed
individually before it is chunked. This is slower per-document but it is what
prevents bad chunk boundaries (a Section cut mid-sentence, a table split in
half, wrong jurisdiction tags) which directly cause wrong legal answers later.

If anything about a document is ambiguous (unclear jurisdiction, unclear
whether it's an amendment vs a separate Act, duplicate-looking filenames,
scanned/unreadable pages), STOP and flag it for human confirmation rather than
guessing. Wrong metadata on legal/regulatory content is worse than a missing
document.

---

## 1. THE METADATA SCHEMA

Every chunk ingested into the vector DB must carry this metadata payload.
This schema is final for the current phase — do not invent new fields ad hoc;
if you believe a field is missing, flag it for review instead of silently
adding one (schema drift breaks filtering consistency across the collection).

```yaml
# --- Identity ---
id: string                         # unique chunk id — see ID CONVENTION below
document_id: string                # stable id per source document — see ID CONVENTION
source_filename: string            # original filename, exactly as on disk

# --- Jurisdiction & scope ---
jurisdiction: enum                 # "India" | "International"
country_code: string | null        # "IN" for India docs; null for International

# --- Document classification ---
doc_category: enum
  # "primary_law"              -> Acts (Patents Act, Copyright Act, Designs Act, etc.)
  # "implementing_rules"       -> Rules/Regulations issued under a primary law
  # "international_treaty"     -> TRIPS, CBD, Nagoya, PCT, Madrid, WIPO GRATK
  # "regulatory_notification"  -> FSSAI Gazette notifications, KoB circulars
  # "herbal_pharmacopoeia"     -> API Vol, WHO Monographs, Essential Drug List
  # "reference_dataset"        -> structured lookup data (xlsx sources)
  # "secondary_literature"     -> academic/analysis papers (e.g. bio-piracy paper) —
  #                                NOT law, tag clearly, lower retrieval_priority

ip_domain: enum | list             # fine-grained domain(s), can be multi-valued
  # "patents" | "trademarks" | "geographical_indications" | "copyright" |
  # "industrial_designs" | "plant_variety_protection" | "traditional_knowledge" |
  # "biological_diversity" | "drugs_cosmetics" | "food_regulation" |
  # "herbal_pharmacopoeia" | "general_ip"

agent_scope: enum | list           # coarse routing key for future multi-agent system
  # "ip_agent" | "patent_agent" | "biodiversity_agent" |
  # "regulatory_agent" | "pharma_reference_agent"

# --- Structural / provenance ---
section_number: string | null      # e.g. "Section 3(d)", "Rule 12", "Article 27.3(b)"
section_title: string | null       # human-readable heading of that section, if present
page_number: int
chunk_index: int                   # position of this chunk within its document
folder_path: string                # original path under DataSet/, for audit trail

# --- Temporal ---
enactment_year: int | null
amendment_year: int | null
is_current_version: bool           # false if a newer version/amendment supersedes this

# --- Language ---
source_language: string            # "en" for all current documents

# --- Retrieval helpers ---
retrieval_priority: int | null     # lower number = higher priority when multiple
                                    # doc_categories match the same query
                                    # (e.g. primary_law ranks above secondary_literature)
cross_reference_ids: list[string] | null
                                    # document_ids this chunk depends on/references
                                    # (e.g. an Implementing Rule chunk referencing its
                                    # parent Act) — lets an agent fetch linked context
                                    # without a second semantic search

# --- Content & embedding tracking ---
chunk_text: string                 # the actual chunk content
embedding_model: string            # exact model/version used, for future re-indexing
```

### ID CONVENTION (must be deterministic and collision-free)

- `document_id`: `{jurisdiction_prefix}-{slugified_short_name}-{year}`
  Example: `in-patents-act-1970`, `intl-trips-1994`, `in-fssai-ayurveda-aahara-2022`
- `id` (chunk id): `{document_id}_c{chunk_index:03d}`
  Example: `in-patents-act-1970_c042`

Before ingesting a new document, **check the existing collection for a
matching or near-duplicate `document_id`** to avoid accidental duplicate
ingestion of the same Act under two filenames.

---

## 2. THE FOLDER-PATH → METADATA CONFIG FILE

All folder-path-to-metadata mapping lives in an external config file —
**never hardcode this mapping inside the ingestion script.** This is what
makes future ingestion additive.

Create/maintain: `ingestion_config/document_registry.yaml`

Each entry looks like this:

```yaml
- source_filename: "The Patents Act, 1970, India.pdf"
  folder_path: "India/India-IP/Main IP Laws/Patents (Inventions)/"
  document_id: "in-patents-act-1970"
  jurisdiction: "India"
  country_code: "IN"
  doc_category: "primary_law"
  ip_domain: ["patents"]
  agent_scope: ["ip_agent", "patent_agent"]
  enactment_year: 1970
  amendment_year: null
  is_current_version: true
  source_language: "en"
  retrieval_priority: 1
  cross_reference_ids: []
  status: "pending"   # pending -> analyzed -> chunked -> ingested -> validated
```

**To add a new document in the future:** append one entry to this file,
place the PDF in the source folder, and run the ingestion process below.
No code changes required. This file is the single source of truth for what
has and hasn't been ingested — check `status` before reprocessing anything.

---

## 3. PER-DOCUMENT WORKFLOW (run this for every single PDF)

### Step 1 — Structural Analysis

Read the actual PDF. Do not assume structure from the filename. Determine
and report:

- **Document type**: numbered legal Act (Sections/Sub-sections), Rule/
  Regulation, international Treaty (Articles/Annexes), herbal monograph
  (entry-per-herb), Gazette notification, or unstructured narrative text.
- **Structural markers**: the literal pattern that marks section boundaries
  in this specific document (e.g. `"Section \d+"`, `"Article \d+\.\d*"`,
  `"Rule \d+"`, monograph entry headers). Write the actual pattern you found,
  not a generic assumption.
- **Irregularities**: tables, scanned/image-only pages needing OCR, footnotes,
  multi-column layout, strikethrough/amended text, non-English fragments.
- **Scale**: page count, estimated chunk count at ~300–500 tokens per chunk.

### Step 2 — Chunking Strategy Proposal

Based on Step 1, propose (and get confirmation for ambiguous cases):

- **Method**: structure-aware split by Section/Article/Rule is the default
  and preferred approach. Use semantic/paragraph-based splitting only when
  no reliable structural markers exist (e.g. the bio-piracy academic paper).
- **Chunk size & overlap**: target size, and confirm overlap never bridges
  two different sections/articles — overlap stays within one section only.
- **Metadata extraction plan**: exactly how `section_number` and
  `section_title` will be pulled from the text for each chunk.
- **Special handling**: e.g. keep each table as a single chunk rather than
  splitting it row-by-row; keep each herbal monograph entry as one chunk
  per herb rather than splitting across a token limit.

For clearly structured Acts/Rules/Treaties, proceed directly to Step 3. For
anything structurally unusual (irregular tables, mixed scanned/text pages,
ambiguous jurisdiction, unclear amendment relationship) — stop and confirm
with a human before chunking.

### Step 3 — Metadata Assignment

Pull static fields (jurisdiction, doc_category, ip_domain, agent_scope,
enactment_year, etc.) from the matching entry in `document_registry.yaml`.
Assign per-chunk fields (section_number, section_title, page_number,
chunk_index, chunk_text) from your Step 1–2 analysis. Populate every field
in the schema — do not leave fields silently null unless the schema marks
them as nullable and the document genuinely has no value for them.

### Step 4 — Embedding & Ingestion

- Generate embeddings using the project's designated embedding model
  (confirm current model name/version before running — do not assume).
- Ingest chunks into the vector DB collection with full metadata as payload.
- Confirm these fields are payload-indexed for fast filtered search:
  `jurisdiction`, `doc_category`, `ip_domain`, `agent_scope`.
- Log: `document_id`, total chunks created, any pages/sections skipped or
  flagged for manual review (e.g. OCR needed, unparseable table).
- Update `status` for this document in `document_registry.yaml` to
  `"ingested"`.

### Step 5 — Validation

- Run 2–3 sample retrieval queries specific to this document's actual
  content and confirm correct chunks surface with correct metadata attached.
- Check for malformed chunks: cut mid-sentence, missing `section_number`,
  wrong `jurisdiction` or `ip_domain` tag.
- Update `status` to `"validated"` once confirmed clean. If issues are
  found, fix and re-validate before moving to the next document — do not
  proceed to the next PDF with unresolved validation failures.

---

## 4. INGESTION ORDER (process documents in this order)

Rationale: core India primary law first (highest query volume, cleanest
structure — lets the process get proven out on easy cases first), then
domains central to the Ayurveda/TK use case, then supporting regulatory
material, then structurally-harder pharmacopoeia and international treaty
documents last, once the chunking approach is mature. Structured/tabular
(xlsx) data is handled separately at the end, outside the standard chunking
path.

**Phase 1 — Core Indian Primary Law**
1. The Patents Act, 1970, India.pdf
2. patents rule 2003.pdf
3. patents amendment rule 2024.pdf
4. indian patent act 1970.pdf — ⚠ verify against #1 for duplication before ingesting both
5. The Trade Marks Act, 1999, India.pdf
6. The Geographical Indications of Goods (Registration and Protection) Act, 1999, India.pdf
7. The Designs Act, 2000, India.pdf
8. The Copyright Act, 1957, India.pdf
9. The Protection of Plant Varieties and Farmers' Rights Act, 2001, India.pdf
10. The Semiconductor Integrated Circuits Layout-Design Act, 2000, India.pdf

**Phase 2 — Traditional Knowledge & Biodiversity**
11. The Biological Diversity Act, 2002, India.pdf
12. Biological Diversity Act 2023.pdf — ⚠ confirm: amendment of #11 or separate act
13. The Biological Diversity Rules, 2024.pdf
14. Bio-piracy of Traditional Knowledge.pdf — tag `secondary_literature`, low `retrieval_priority`
15. in197en_1.pdf, in199en_1.pdf, in200en_1.pdf, in201en_1.pdf, in203en_1.pdf — ⚠ verify each individually before batch-tagging as TK implementing rules

**Phase 3 — Remaining India Implementing Rules**
16. in043en_1.pdf, in085en_1.pdf (Copyright rules) — set `cross_reference_ids` to #8
17. in015en_1.pdf (GI rules) — set `cross_reference_ids` to #6

**Phase 4 — Regulatory / Drug-Adjacent Law**
18. 2016DrugsandCosmeticsAct1940Rules1945.pdf
19. The_Drugs_And_Magic_Remedies_Objectionable_Advertisements_Act_1954.PDF
20. Gazette_Notification_Ayurveda_Aahara_09_05_2022.pdf, Ayurveda-Aahara-covered-under-the-FSS-Ayurveda-Aahara-Regulations.pdf, Introduction-of-new-Kind-of-Business-KoB-for-Ayurveda-Aahara-under-FoSCoS-for-License.pdf

**Phase 5 — Herbal / Pharmacopoeia Reference**
21. WHO HERBAL MONOGRAPHS.pdf
22. API-Vol-1.pdf
23. API-II-Vol-1 FORMULATIONS.pdf
24. national essential drug list by AYUSH.pdf

**Phase 6 — International Treaties**
25. cbd-en.pdf
26. nagoya-protocol-en.pdf
27. 31bis_trips_e.pdf
28. pct.pdf, "The PCT now has 159 Contracting States.pdf"
29. madrid_marks.pdf, trt_madridp_gp_001en.pdf, trt_madrid_gp_001en.pdf — ⚠ verify these are three distinct documents, not duplicates with near-identical filenames
30. trt_gratk_001en.pdf

**Phase 7 — Structured/Tabular Data (separate path, not standard chunking)**
31. profile_IN.xlsx
32. CountryListInTreaty.xlsx
For both: do not force into prose-style chunks. Ingest as structured
lookup/reference data (e.g. one chunk per row with column context, or as a
joined reference table the agents can query directly), and flag this
decision in `document_registry.yaml` under a note field.

---

## 5. ADDING FUTURE DOCUMENTS (do this, and only this)

1. Place the new PDF/file in the appropriate `DataSet/` subfolder.
2. Add one entry to `ingestion_config/document_registry.yaml` with
   `status: "pending"`.
3. Run this same Step 1–5 workflow on that single document.
4. Do not modify the ingestion script, the schema, or this instructions file
   to accommodate a one-off document — if a genuinely new field or category
   is needed, flag it for human review rather than adding it unilaterally.

This is what "future data ingestion should also be possible" means in
practice: the schema, the config file, and this workflow are the stable
interface. New documents are additive inputs to that interface, never a
reason to change it.

---

## 6. HARD RULES (do not violate)

- Never chunk across a Section/Article/Rule boundary.
- Never leave `jurisdiction`, `doc_category`, `ip_domain`, or `agent_scope`
  unset — these are the fields future agents filter on; a missing value
  makes a chunk invisible to the correct agent.
- Never ingest a document without first checking `document_registry.yaml`
  for an existing `document_id` to prevent duplicates.
- Never guess on ambiguous jurisdiction, amendment relationships, or
  possible duplicate filenames — flag and wait for confirmation.
- Never batch-apply one chunking strategy to multiple documents without
  running Step 1 analysis on each one individually.
- Always complete Step 5 validation before marking a document `"ingested"`
  as final (`"validated"`) and moving to the next one.

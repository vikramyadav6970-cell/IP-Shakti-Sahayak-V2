# IP-SAKTI Sahayak — Master Data Ingestion Architecture & Agent Instructions

## READ THIS FIRST

You are the ingestion agent for **IP-SAKTI Sahayak**, a multilingual statutory RAG system for Ayurveda, Traditional Knowledge (TK), Intellectual Property (IP), patents, ABS, Indian/international law, regulations, treaties, case law, standards, and research material (built for SIH 2026, Problem Statement 26045, Ministry of Ayush).

Your job is to ingest the comprehensive dataset located in `ai/NewDataSet/` into Qdrant vector database in a way that:

1. **Produces Grounded Retrieval Today**: Real-time vector search across statutory, regulatory, and prior-art collections.
2. **Supports Future Multi-Agent Orchestration**: Independent specialist agents (IP Agent, Patent Agent, ABS Agent, Case-Law Agent, Ayurveda Agent, International Agent) retrieve evidence using targeted metadata filters, synthesized by an orchestrator agent.
3. **Maintains 100% Backward Compatibility**: All existing API endpoints, chat services, and test suites will work seamlessly regardless of whether pointing to the old or new Qdrant database/API key.
4. **Is Fully Reproducible and Extensible**: External configuration files (`ingestion_config/document_registry.yaml`) drive the ingestion pipeline without hardcoding.

---

# 1. NEWDATASET DIRECTORY & PHASING OVERVIEW

The `ai/NewDataSet/` directory contains 272 files organized across 6 distinct legal and knowledge phases:

### Phase 1: India IP Statutory Law & Rules (`ai/NewDataSet/India/India-IP/`)
- **Patents (Inventions)**: Primary Acts (1970, 1950, 1939, 1930, 1920, 1911, Ordinance 1968) and Rules (2003, 2006, 2014, 2019, 2020, 2024).
- **Trademarks**: Trade Marks Act 1999, 1941, Trade Marks Rules 2002, 2013, 2017, IPAB Rules.
- **Copyright**: Copyright Act 1957, 1914, Amendment Acts 1983..2012, Copyright Rules 1958..2013.
- **Industrial Designs**: Designs Act 2000, 1911, Amendment Acts, Design Rules 2001, 2008, 2014.
- **Geographical Indications**: GI Act 1999, GI Rules 2002, 2013.
- **Plant Variety Protection**: PPV&FR Act 2001, Regulations 2006..2013, Rules 2009..2012.

### Phase 2: India ABS / Biological Diversity (`ai/NewDataSet/India/`)
- **Biological Diversity / ABS**: Biological Diversity Act 2002, Amendment Act 2023, BD Rules 2004, 2019, NBA guidelines on ABS, SBB notifications.
- **Bio-Privacy**: Secondary literature and analysis on traditional knowledge protection.

### Phase 3: Ayurveda, TK, Standards & Health Regulations (`ai/NewDataSet/India/`)
- **The Ayurvedic Pharmacopoeia of India (API)**: All Volumes (23 Monograph and Appendix PDFs).
- **Shlokas**: 7 Shloka volumes covering classical formulation references.
- **Drugs & Cosmetics**: Drugs and Cosmetics Act 1940, Rules 1945 (Form 25-D, Rule 158B, Form 32).
- **Drugs & Magic Remedies**: Drugs and Magic Remedies (Objectionable Advertisements) Act 1954.
- **FSSAI Food Safety**: FSSAI Ayurveda Aahara Regulations 2022 and related statutory orders.

### Phase 4: Indian Case Law & Judgments (`ai/NewDataSet/India/Judgements/`)
- 52 High Court and Supreme Court landmark IP and AYUSH judgments (e.g. *Novartis AG v. Union of India*, *Cipla Ltd.*, *Biswanath Prasad Radhey Shyam*, *Bajaj Auto*, *Bayer*, *Glenmark*).

### Phase 5: International Treaties & IP Systems (`ai/NewDataSet/International/` & `ai/NewDataSet/India/Treaties/`)
- **Multilateral Treaties**: TRIPS (31bis), CBD (Convention on Biological Diversity), Nagoya Protocol on ABS, Budapest Treaty (Microorganisms Deposit), PCT (Patent Cooperation Treaty), Madrid System, Hague System, WIPO GRATK Treaty (Genetic Resources & Associated Traditional Knowledge).
- **India Bilateral/Multilateral Treaties**: 62 international agreements and protocols.

### Phase 6: Research & Prior Art (`ai/NewDataSet/Research/`)
- Research data and academic prior-art documents.

---

# 2. COMMON METADATA SCHEMA

Every chunk ingested into Qdrant carries this standardized schema. Fields are backwards compatible with the current retrieval pipeline while supporting future multi-agent routing.

```yaml
# --- Primary Identity & Vector Keys ---
id: string                         # deterministic chunk id (e.g. in-patents-act-1970_s003p)
document_id: string                # stable slugified id (e.g. in-patents-act-1970)
source_filename: string            # original filename on disk
folder_path: string                # relative path under NewDataSet/

# --- Jurisdiction & Scope ---
jurisdiction: string               # "India" | "International"
country_code: string | null        # "IN" for India; ISO code or null for International

# --- Classification & Multi-Agent Routing ---
doc_category: string
  # "primary_law"              -> Acts, Amendment Acts, Ordinances
  # "implementing_rules"       -> Rules, Regulations, Orders
  # "international_treaty"     -> TRIPS, CBD, Nagoya, PCT, Budapest, Madrid, Hague
  # "regulatory_notification"  -> FSSAI Gazette, NBA notifications, Circulars
  # "herbal_pharmacopoeia"     -> API Monographs, Shlokas, Pharmacopoeial standards
  # "case_law"                 -> Court judgments, tribunal rulings
  # "reference_dataset"        -> Structured lookup data (XLSX, CSV)
  # "secondary_literature"     -> Research papers, prior-art articles

ip_domain: list[string]
  # ["patents", "trademarks", "geographical_indications", "copyright",
  #  "industrial_designs", "plant_variety_protection", "traditional_knowledge",
  #  "biological_diversity", "drugs_cosmetics", "food_regulation",
  #  "herbal_pharmacopoeia", "case_law", "general_ip"]

agent_scope: list[string]          # routing keys for future multi-agent orchestration
  # ["ip_agent", "patent_agent", "biodiversity_agent", "regulatory_agent",
  #  "case_law_agent", "pharma_reference_agent", "international_agent", "research_agent"]

# --- Structural Hierarchy & Content ---
section_number: string | null      # e.g. "Section 3(p)", "Rule 158B", "Article 27.3(b)", "Monograph: Ashwagandha"
section_title: string | null       # Heading / title of that section/monograph
page_number: int                   # PDF page number (1-indexed)
chunk_index: int                   # Sequence position within document
chunk_text: string                 # The actual chunk content (with contextual header prepended)

# --- Temporal & Version Tracking ---
enactment_year: int | null
amendment_year: int | null
is_current_version: bool           # true if current operative law
parent_document_id: string | null
amends_document_id: string | null
supersedes_document_id: string | null

# --- Verification & Model Metadata ---
source_language: string            # "en"
retrieval_priority: int            # 1 (Primary Law/Treaty), 2 (Rules/Regulations), 3 (Secondary)
verification_status: string        # "VERIFIED_OFFICIAL_GAZETTE"
embedding_model: string            # "BAAI/bge-m3"
ingestion_timestamp: string        # ISO 8601 timestamp
content_hash: string               # SHA-256 hash of raw chunk text
```

---

# 3. DOCUMENT-SPECIFIC CHUNKING & PARSING PROFILES

Each document type requires a tailored chunking strategy:

| Document Type | Primary Unit | Chunking Strategy | Contextual Prepending |
|---|---|---|---|
| **Primary Act** | Legal Section (`Section \d+`) | Atomic sub-clause / section parsing | `Document: {title} | Section: {sec}` |
| **Implementing Rules** | Rule (`Rule \d+`) | Rule-based boundary split | `Document: {title} | Rule: {rule}` |
| **Regulations / Orders** | Regulation (`Reg \d+`) | Structural clause split | `Document: {title} | Reg: {reg}` |
| **International Treaty** | Article (`Article \d+`) | Article & paragraph split | `Treaty: {title} | Article: {art}` |
| **API Monograph** | Monograph / Herb | Monograph-per-chunk with standards tables | `Monograph: {herb_name} | API Vol {vol}` |
| **Classical Shlokas** | Shloka / Verse | Shloka-level with English translation | `Text: {classical_source} | Shloka {num}` |
| **Case Law / Judgments** | Judgment Paragraph / Holding | Ratio decidendi & factual holding split | `Court: {court} | Case: {case_name}` |
| **Reference Datasets** | Row / Record | Row-level JSON-LD stringification | `Dataset: {source_name} | Row: {key}` |

---

# 4. INGESTION PIPELINE EXECUTION STEPS

For every document in `ai/ingestion_config/document_registry.yaml`, execute the 5-step lifecycle:

```
Document in NewDataSet/
   │
   ├── [Step 1: Structural Analysis] ────────► Detect layout, page count, OCR need, markers
   │
   ├── [Step 2: Adaptive Chunking] ──────────► Split into atomic legal units (< 500 tokens)
   │
   ├── [Step 3: Metadata Assembly] ──────────► Populate full schema with deterministic IDs
   │
   ├── [Step 4: GPU Embedding & Upsert] ─────► Embed via BAAI/bge-m3 on CUDA -> Qdrant
   │
   └── [Step 5: Retrieval Validation] ───────► Semantic search query to verify indexed recall
```

---

# 5. REGISTRY-DRIVEN INGESTION (`document_registry.yaml`)

- The registry file `ai/ingestion_config/document_registry.yaml` is the single source of truth.
- Track status: `pending` → `analyzed` → `chunked` → `ingested` → `validated`.
- Re-running the pipeline skips `validated` documents unless `--force` is specified.
- To add a new document in the future: place the file in `ai/NewDataSet/` subfolder, add an entry to `document_registry.yaml`, and run `run_ingestion.py`.

---

# 6. FUTURE AGENTIC ROUTING MAPPING

When the future multi-source orchestrator is enabled, specialist agents query the unified knowledge base with metadata filters:

- **Patent Agent**: `jurisdiction: "India"`, `ip_domain: "patents"`, `doc_category: ["primary_law", "implementing_rules"]`
- **ABS Agent**: `ip_domain: "biological_diversity"`, `agent_scope: "biodiversity_agent"`
- **Ayurveda / Regulatory Agent**: `ip_domain: ["herbal_pharmacopoeia", "drugs_cosmetics", "food_regulation"]`
- **Case-Law Agent**: `doc_category: "case_law"`, `agent_scope: "case_law_agent"`
- **International Agent**: `jurisdiction: "International"`, `doc_category: "international_treaty"`
- **Main Synthesis Agent**: Gathers retrieved evidence chunks from all specialist agents, deduplicates by `content_hash`, sorts by `retrieval_priority`, and generates grounded, fully cited legal analysis.

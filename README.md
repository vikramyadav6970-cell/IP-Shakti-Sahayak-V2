---
title: IP SAKTI Sahayak Backend
emoji: 🌿
colorFrom: green
colorTo: emerald
sdk: docker
app_port: 7860
pinned: false
---

# IP-SAKTI Sahayak: AI-Powered Intellectual Property & Regulatory Intelligence for Ayush

**Smart India Hackathon (SIH) — Problem Statement 26045 (Ministry of Ayush / All India Institute of Ayurveda)**

A multilingual, domain-orchestrated, source-cited AI decision-support platform providing authoritative Intellectual Property (IPR), Biodiversity Access & Benefit Sharing (ABS), and regulatory compliance guidance for Ayurvedic, Siddha, and Unani innovations across national and international legal regimes.

> ⚖️ **Statutory Notice:** IP-SAKTI Sahayak provides verified legal and regulatory **information, not legal advice**. All statutory outputs are traceable to indexed government gazettes, acts, pharmacopoeias, and judicial precedents. Official filings require review by a registered patent attorney or legal counsel.

---

## Table of Contents
1. [Problem Statement & How IP-SAKTI Solves It](#1-problem-statement--how-ip-sakti-solves-it)
2. [End-to-End System Workflow Architecture](#2-end-to-end-system-workflow-architecture)
3. [Retrieval-Augmented Generation (RAG) Architecture](#3-retrieval-augmented-generation-rag-architecture)
4. [Technology Stack & Architecture Matrix](#4-technology-stack--architecture-matrix)
5. [Complete Repository Directory & File Structure](#5-complete-repository-directory--file-structure)
6. [Key Innovation Modules](#6-key-innovation-modules)
7. [Getting Started & Local Development](#7-getting-started--local-development)
8. [Automated Testing & Verification](#8-automated-testing--verification)

---

## 1. Problem Statement & How IP-SAKTI Solves It

### The Problem
Ayush innovators, herbal formulations startups, and researchers face a labyrinth of fragmented, complex, and overlapping regulatory and intellectual property frameworks:
1. **Patents vs. Traditional Knowledge (TKDL)**:
   - **Section 3(p)** of the *Indian Patents Act, 1970* bars the patenting of traditional knowledge or mere aggregations/duplications of known properties.
   - To secure a patent, innovators must demonstrate proven non-obvious synergistic therapeutic efficacy under **Section 3(e)**, rather than a simple mixture.
2. **Access & Benefit Sharing (ABS) & Biodiversity Compliance**:
   - Under the *Biological Diversity Act, 2002* and the *2014 ABS Regulations*, accessing Indian biological resources from forests, farmers, or vendors requires mandatory prior approval (Form 1) from the **National Biodiversity Authority (NBA)** or State Biodiversity Boards (SBB), along with benefit-sharing percentages (0.1%–0.5% or 3%–5%).
3. **Statutory Classification & Licensing Ambiguity**:
   - The same botanical formulation can fall into distinct statutory classes with entirely different compliance pathways:
     - **Classical Ayurvedic Medicine** (Section 3(a), *Drugs & Cosmetics Act, 1940* via Form 25-D).
     - **Proprietary Ayurvedic Medicine** (Rule 158-B with pilot clinical safety trials).
     - **Ayurveda Aahara** (*FSSAI Regulations, 2022* with strict non-therapeutic packaging and labeling disclaimers).
     - **Phytopharmaceutical Drugs** (Schedule Y / Rule 122E with fractionated extracts and regulatory toxicology dossiers).
     - **Cosmetics** (Part XIII, *Drugs and Cosmetics Rules, 1945*).
4. **International Export Barriers**:
   - Navigating foreign jurisdictions requires adherence to the **Nagoya Protocol**, WIPO Patent Cooperation Treaty (**PCT**) international phase filings, USPTO botanical guidance, and EMA herbal monographs.

---

### How IP-SAKTI Sahayak Solves It
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          IP-SAKTI SAHAYAK PLATFORM                          │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│ 1. Diagnostic Engine │ 2. Multi-Agent RAG   │ 3. Voice & Multi-Lingual      │
│ Pre-classifies herbal│ Decomposes queries   │ Full hands-free conversation  │
│ formulations into 6  │ across Patent, ABS,  │ in 11+ Indic languages via    │
│ statutory categories │ Food, Trademark, and │ Sarvam AI (saaras:v3 speech-  │
│ before legal routing.│ Export domain agents.│ to-text & bulbul:v3 neural    │
│                      │                      │ text-to-speech engine).       │
├──────────────────────┼──────────────────────┼───────────────────────────────┤
│ 4. Grounding Engine  │ 5. Confidence Scorer │ 6. Human Escalation Desk      │
│ Validates statutory  │ Weakest-link multi-  │ Low-confidence gray areas are │
│ quotes against exact │ domain score based on│ seamlessly triaged to human IP│
│ indexed gazette text.│ evidence coverage.   │ facilitators with full audit. │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
```

---

## 2. End-to-End System Workflow Architecture

The entire user journey from multi-modal query entry to statutory synthesis, confidence scoring, translation, voice synthesis, and facilitator escalation is illustrated below:

![IP-SAKTI Sahayak End-to-End Workflow Diagram](docs/assets/workflow_pipeline_flowchart.jpg)

### Step-by-Step Workflow Description:
1. **User Interaction**: The user enters queries via either the **Light-Mode Glassmorphic Chat UI** or the **Hands-Free Voice Conversation Mode**.
2. **Speech Recognition**: Voice audio is encoded to 16kHz PCM WAV in the browser and transcribed using **Sarvam AI `saaras:v3`** Speech-to-Text.
3. **Product Classification Diagnostic**: The formulation engine extracts ingredients, classical references, and dosage forms, categorizing the product into one of 6 statutory categories (Classical, Proprietary, Ayurveda Aahara, Phytopharmaceutical, Cosmetic, or New Drug).
4. **Multi-Agent Query Decomposition**: Compound queries (e.g., *"Can I patent Ashwagandha extract and do I need NBA approval?"*) are decomposed by `QueryDecomposer` into specialized domain sub-tasks (`patent_agent`, `biodiversity_agent`, `formulation_agent`, `trademark_agent`, `international_agent`).
5. **Parallel Vector Retrieval**: Specialized agents query Qdrant Cloud in parallel with strict payload filters (`jurisdiction`, `agent_scope`, `ip_domain`).
6. **Reasoning & Statutory Synthesis**: The LLM engine (**Google Gemini 2.5**) synthesizes an evidence-grounded answer adhering strictly to retrieved evidence.
7. **Citation & Substring Verification**: `CitationValidator` performs exact string matching against the source text to ensure 0% hallucinated citations.
8. **Weakest-Link Multi-Domain Confidence Scoring**: Computes harmonic mean and min-coverage scores across all involved domains.
9. **Speech Sanitization & Neural TTS**: Cleans markdown formatting, headers, and raw JSON tags via `strip_markdown_for_speech()`, synthesizing natural audio via **Sarvam AI `bulbul:v3`**.
10. **Interactive Display & Escalation**: Renders interactive citation chips, confidence badges, feedback thumbs, and an optional **Ask Human Expert** escalation trigger.

---

## 3. Retrieval-Augmented Generation (RAG) Architecture

The statutory intelligence retrieval pipeline combines dense vector semantics with sparse lexical matching and payload filtering over Qdrant Cloud:

![IP-SAKTI Sahayak RAG Pipeline Architecture](docs/assets/rag_pipeline_flowchart.jpg)

### RAG Pipeline Specifications:
- **Corpus Ingestion**: Legal statutes, official gazettes, pharmacopoeia monographs (API/UPI), FSSAI regulations, and Supreme Court/High Court case laws are normalized into structured Markdown with strict YAML metadata.
- **Hierarchical Chunking**: Legal documents are parsed by Chapter, Section, Rule, Sub-rule, and Proviso preserving statutory boundaries.
- **Hybrid Embeddings**:
  - **Dense**: `BAAI/bge-m3` generates 1024-dimensional semantic embeddings supporting Sanskrit, Indic languages, and English.
  - **Sparse**: BM25 lexical vector representation captures exact Section numbers (e.g., *Section 3(p)*, *Rule 158(B)*, *Form 25-D*).
- **Qdrant Cloud Filtering**: Hardware-accelerated payload indices on `jurisdiction` (`INDIA` vs `INTERNATIONAL`) and `agent_scope` guarantee zero cross-jurisdiction data pollution.
- **Strict Grounding Enforcement**: LLM prompt mandates refusal or absence disclaimers if retrieved evidence does not support a claim.

---

## 4. Technology Stack & Architecture Matrix

| Layer | Chosen Technology | Alternatives Evaluated | Why Chosen Technology is Best |
|---|---|---|---|
| **AI / LLM Engine** | **Google Gemini 2.5 (Flash / Pro)** | OpenAI GPT-4o, Anthropic Claude 3.5, Llama 3.3 | 1M+ token context window, state-of-the-art legal reasoning, native multilingual comprehension, and low latency per token. |
| **Vector Database** | **Qdrant Cloud (Managed)** | Pinecone, ChromaDB, Weaviate, Milvus | Native hybrid dense+sparse vectors, instant payload filtering on multi-tenant metadata, HNSW graph indexing, zero collection cold-start delay. |
| **Dense Embeddings** | **BAAI/bge-m3 (`SentenceTransformers`)** | OpenAI `text-embedding-3-large`, Cohere Embed | Multi-lingual support with high accuracy on Indic legal scripts; local in-memory CPU/GPU inference with no API rate limits. |
| **Voice AI (STT & TTS)** | **Sarvam AI (`saaras:v3` & `bulbul:v3`)** | OpenAI Whisper, ElevenLabs, Google Cloud Speech | Purpose-built for Indian English accents and 11+ Indic languages; superior recognition of Sanskrit/Ayurvedic botanical terms; low latency. |
| **Backend Framework** | **FastAPI (Python 3.11+)** | Django REST Framework, Express.js, Spring Boot | Asynchronous event loop (`asyncio`), native Pydantic v2 data serialization, automatic OpenAPI documentation, seamless Python ML integration. |
| **Database & ORM** | **PostgreSQL + Asyncpg + SQLAlchemy 2.0** | MongoDB, MySQL, DynamoDB | Strict ACID compliance for user audits and facilitator tickets, async connection pooling, native UUID and JSONB support. |
| **Frontend UI** | **React 18 + Vite + TypeScript** | Next.js, Angular, Vue.js | Lightning-fast development and build times, full type safety, client-side state predictability, lightweight bundle size. |
| **Styling & Design** | **Tailwind CSS + Glassmorphism Design Tokens** | Material UI, Ant Design, Bootstrap | Pixel-perfect customization with CSS custom properties, backdrop-blur frosted glass, emerald green theme tokens, WCAG AA contrast. |
| **State Management** | **Zustand (with LocalStorage Sync)** | Redux Toolkit, MobX, React Context | Zero-boilerplate atomic state with native persistence for session history, sidebar collapse state, and voice continuous dialogue. |

---

## 5. Complete Repository Directory & File Structure

```
ip-sakti-V2/
├── README.md                              # Main platform documentation and architecture guide
├── ARCHITECTURE.md                        # In-depth technical architecture and data schemas
├── MVP_SCOPE.md                           # Locked feature checklist and compliance deliverables
├── AGENT_PROTOCOL.md                      # Engineering and agentic execution discipline guidelines
├── context.md                             # Domain decisions, legal definitions, and grounding rules
├── howToStart.md                          # Quickstart guide for running the platform
├── process.md                             # Task tracking, completed milestones, and audit history
│
├── docs/                                  # Architectural visual assets
│   └── assets/
│       ├── rag_pipeline_flowchart.jpg     # RAG Pipeline Flowchart diagram
│       └── workflow_pipeline_flowchart.jpg# End-to-End System Workflow diagram
│
├── ai/                                    # AI Engine & Legal RAG Pipeline
│   ├── data/
│   │   └── corpus/                        # Authoritative legal text repository (Acts, Gazettes, Rules)
│   │       ├── manifest.jsonl             # Registry manifest with SHA-256 hashes and metadata
│   │       ├── The_Patents_Act,_1970.pdf  # Indian Patents Act 1970 with amendments
│   │       ├── Biological_Diversity_Act_2002.pdf # Biological Diversity Act 2002 & 2023 amendment
│   │       ├── 2016DrugsandCosmeticsAct1940Rules1945.pdf # D&C Act 1940 and Rules 1945
│   │       ├── FSSAI_Ayurveda_Aahara_Regulations_2022.pdf # Ayurveda Aahara standards
│   │       └── The_Trade_Marks_Rules,_2002.pdf # Trade Marks Act 1999 & Rules 2002
│   ├── src/
│   │   ├── abs/
│   │   │   └── abs_engine.py              # Access & Benefit Sharing rule evaluator (NBA Form 1 & SBB)
│   │   ├── citations/
│   │   │   ├── citation_extractor.py      # Regex & AST extractor for legal statutory citations
│   │   │   └── citation_validator.py      # Substring verification against retrieved corpus text
│   │   ├── classification/
│   │   │   ├── intent_classifier.py       # Multi-intent & acoustic keyword intent detector
│   │   │   ├── jurisdiction_classifier.py # India vs International jurisdiction classifier
│   │   │   └── product_classifier.py      # 6-Category Ayurvedic formulation diagnostic engine
│   │   ├── confidence/
│   │   │   └── confidence_scorer.py       # Weakest-link multi-domain confidence scoring engine
│   │   ├── ingestion/
│   │   │   ├── chunker.py                 # Statutory-aware legal document chunker
│   │   │   ├── corpus_validator.py        # Manifest integrity and hash validator
│   │   │   ├── metadata_extractor.py      # Document type and Section identifier extractor
│   │   │   ├── pdf_parser.py              # PDF to structured text extractor
│   │   │   ├── qdrant_indexer.py          # Vector ingestion worker for Qdrant Cloud
│   │   │   └── strategy_analyzer.py       # Document strategy and domain tag analyzer
│   │   ├── llm/
│   │   │   ├── base.py                    # Abstract base class for LLM providers
│   │   │   └── gemini_provider.py         # Google Gemini 2.5 Flash/Pro provider integration
│   │   ├── orchestration/
│   │   │   └── decomposer.py              # Multi-agent domain query decomposition engine
│   │   ├── prompts/
│   │   │   └── templates.py               # Grounded consultation prompts and domain isolation rules
│   │   └── retrieval/
│   │       ├── embedder.py                # BGE-M3 Dense vector embedding wrapper
│   │       ├── hybrid_search.py           # Dense + Sparse reciprocal rank fusion search
│   │       ├── qdrant_manager.py          # Qdrant client connection pool and index manager
│   │       └── retriever.py               # Scoped multi-collection and multi-agent retriever
│   └── tests/                             # AI layer test suite
│       ├── abs/test_abs_engine.py         # ABS calculation tests
│       ├── citations/test_citation_validator.py # Substring verification tests
│       └── classification/                # Classifier unit tests
│
├── backend/                               # FastAPI Asynchronous REST & Voice Backend
│   ├── app/
│   │   ├── main.py                        # FastAPI application entrypoint with lifespan pre-warming
│   │   ├── config.py                      # Pydantic Settings and environment configuration
│   │   ├── database.py                    # Async SQLAlchemy session factory with PostgreSQL pooling
│   │   ├── api/v1/                        # REST API router endpoints
│   │   │   ├── auth.py                    # Innovator & Expert JWT authentication
│   │   │   ├── chat.py                    # Chat consultation and Voice endpoint (/chat/voice)
│   │   │   ├── classify.py                # Formulation diagnostic endpoints
│   │   │   ├── documents.py               # Knowledge corpus document query endpoints
│   │   │   ├── expert.py                  # Human facilitator escalation endpoints
│   │   │   └── abs.py                     # Standalone ABS benefit calculation endpoints
│   │   ├── models/
│   │   │   ├── base.py                    # SQLAlchemy Base, TimestampMixin, UUIDMixin
│   │   │   └── entities.py                # User, Conversation, Message, Citation, ExpertRequest models
│   │   ├── schemas/                       # Pydantic request and response schemas
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── classification.py
│   │   │   ├── documents.py
│   │   │   └── expert.py
│   │   └── services/
│   │       ├── chat_service.py            # End-to-end chat orchestration and terminal logging
│   │       ├── classification_service.py  # Product diagnostic classification service
│   │       ├── document_service.py        # Document search and metadata service
│   │       ├── expert_service.py          # Facilitator triage and escalation service
│   │       └── voice_service.py           # Sarvam AI STT & TTS with speech markdown sanitization
│   └── tests/                             # Backend integration and regression test suite
│       ├── test_grounding_eval_suite.py   # Full 24-point legal grounding evaluation suite
│       ├── test_voice_chat.py             # Voice conversation, STT, and TTS regression tests
│       └── test_chat_and_classification.py# Chat flow and diagnostic classification tests
│
├── frontend/                              # React 18 Innovator Web Application
│   ├── src/
│   │   ├── App.tsx                        # Application routing and authentication guards
│   │   ├── main.tsx                       # React DOM entrypoint
│   │   ├── app/
│   │   │   ├── ChatPage.tsx               # Light-mode glassmorphism chat workspace & sidebar
│   │   │   ├── LandingPage.tsx            # Platform landing page with feature showcase
│   │   │   ├── ABSPage.tsx                # Standalone Access & Benefit Sharing calculator
│   │   │   ├── FacilitatorQueriesPage.tsx # Innovator escalation tracking dashboard
│   │   │   ├── LoginPage.tsx              # Innovator login and registration page
│   │   │   └── Layout.tsx                 # Global header, navigation, and disclaimer footer
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── VoiceConversationButton.tsx # 4-state hands-free voice mode button
│   │   │   │   ├── VoiceInputButton.tsx   # Speech-to-text dictation button
│   │   │   │   ├── ConfidenceBadge.tsx    # Evidence grounding confidence chip
│   │   │   │   ├── CitationCard.tsx       # Verified statutory citation card
│   │   │   │   ├── ProductClassificationPanel.tsx # 6-category formulation diagnostic card
│   │   │   │   ├── ProductHistorySidebar.tsx # Slide-out product dossier drawer
│   │   │   │   ├── LanguageSelector.tsx   # Multilingual Indic language selector dropdown
│   │   │   │   ├── JurisdictionOutGuardrail.tsx # Out-of-scope jurisdiction banner
│   │   │   │   └── ExpertEscalationModal.tsx # Human facilitator escalation modal
│   │   │   └── ui/                        # Reusable UI primitives (Button, Card, Badge, Tabs)
│   │   ├── services/
│   │   │   ├── apiClient.ts               # Axios client with JWT interceptor
│   │   │   ├── chatService.ts             # API client for text and voice consultation
│   │   │   └── authService.ts             # Authentication API service
│   │   ├── store/
│   │   │   ├── useChatStore.ts            # Zustand store for chat, history, and voice settings
│   │   │   ├── useJurisdictionStore.ts    # Active jurisdiction state (India / International)
│   │   │   └── useAuthStore.ts            # User authentication state
│   │   └── styles/
│   │       └── index.css                  # Light-mode glass design tokens and fallback utilities
│   ├── tailwind.config.js                 # Tailwind CSS theme extension
│   └── package.json                       # Frontend dependencies and build scripts
│
├── admin/                                 # Ministry / Admin Control Portal
│   └── src/                               # Corpus management, indexing status, and analytics portal
│
└── ip-facilitator/                        # IP Facilitator Escalation Review Desk
    └── src/                               # Expert queue triage, case review, and advisory resolution
```

---

## 6. Key Innovation Modules

### 1. Multi-Agent Domain Orchestration
When an innovator asks a compound query (*"Can I patent my Giloy tea, what license is needed, and do I need NBA clearance?"*), the `QueryDecomposer` splits the question into three parallel sub-tasks:
- **`patent_agent`**: Retrieves *The Patents Act, 1970* (§3(p), §3(e)).
- **`formulation_agent`**: Retrieves *FSSAI Ayurveda Aahara Regulations, 2022* & *D&C Rules, 1945*.
- **`biodiversity_agent`**: Retrieves *Biological Diversity Act, 2002* (§3, Regulation 3).

The LLM synthesizes a single, multi-section response where each section is exclusively grounded in its domain's retrieved statutory evidence.

### 2. Full Hands-Free Voice Conversation Mode
- **16kHz PCM WAV Recording**: Direct browser Web Audio API sampling.
- **Sarvam AI `saaras:v3` STT**: Accurate speech-to-text supporting English and 11+ Indic languages (Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, etc.).
- **Speech Markdown Sanitizer**: Strips headers (`###`), bold markers (`**`), bullet points, and raw `[[PRODUCT_CONTEXT:...]]` JSON tags before synthesis.
- **Sarvam AI `bulbul:v3` Neural TTS**: Returns crystal-clear spoken audio.
- **Tap-to-Barge-In**: Tapping the voice button during audio playback immediately halts speech and initiates a new listening turn.

### 3. Light-Mode Glassmorphism UI
- **Emerald Theme Tokens**: Curated palette (`#10B981`, `#059669`, `#047857`) for legal trust and Ayurvedic botanical heritage.
- **Frosted Glass Panels**: `backdrop-filter: blur(16px)` with subtle elevated shadows (`0 12px 32px rgba(16,60,40,0.10)`).
- **Collapsible History Rail**: Smooth width transition (190px $\leftrightarrow$ 56px) with persistent session state across page reloads.

---

## 7. Getting Started & Local Development

### Prerequisites
- **Python 3.11+**
- **Node.js 20+ & npm**
- **Qdrant Cloud Cluster** (or local Qdrant instance)
- **PostgreSQL 15+**
- **API Keys**: Google Gemini API Key (`GEMINI_API_KEY`) and Sarvam AI API Key (`SARVAM_API_KEY`)

---

### Step 1: Environment Configuration

Create `backend/.env` and `ai/.env`:
```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ipsakti

# AI & LLM Providers
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Vector DB
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your_qdrant_api_key

# Voice & Speech (Sarvam AI)
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_API_BASE_URL=https://api.sarvam.ai

# Security
JWT_SECRET_KEY=your_super_secret_jwt_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

### Step 2: Backend & AI Engine Setup
```bash
# From repository root
cd backend
python -m venv venv
venv\Scripts\activate  # Windows (or source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt

# Run FastAPI backend with hot reload
uvicorn app.main:app --reload --port 8000
```

---

### Step 3: Frontend Web Setup
```bash
# In a new terminal
cd frontend
npm install
npm run dev
```
The application will be accessible at `http://localhost:5173`.

---

## 8. Automated Testing & Verification

The repository includes a comprehensive 30-point evaluation and regression test suite verifying jurisdiction isolation, grounding enforcement, multi-domain decomposition, and voice STT/TTS:

```bash
# Run all backend grounding and voice regression tests
$env:PYTHONPATH="ai;backend"
pytest backend/tests/test_grounding_eval_suite.py backend/tests/test_voice_chat.py -v
```

### Test Coverage Highlights:
- ✅ **Jurisdiction Isolation**: Validates zero leakages between Indian domestic and international legal corpora.
- ✅ **Adversarial Hallucination Rejection**: Tests that tangential or fabricated patents are explicitly rejected with statutory absence disclaimers.
- ✅ **Multi-Domain Orchestration**: Verifies multi-agent decomposition, parallel retrieval, and weakest-link confidence calculations.
- ✅ **Voice Pipeline & Fallback**: Tests English & Indic speech flows, TTS graceful failure fallbacks, and markdown speech sanitization.

---

## License & Attribution
Developed for the **Ministry of Ayush** and **All India Institute of Ayurveda (AIIA)** under Smart India Hackathon 2026.
All legal statutory texts are property of the respective Gazette Authorities (IP India, NBA, FSSAI, CDSCO, WIPO).

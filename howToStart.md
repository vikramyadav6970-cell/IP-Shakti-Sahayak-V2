# IP-SAKTI Sahayak — Architecture & Startup Guide

---

## 1. Backend Service (FastAPI)
Runs the RAG query pipeline, deterministic classification engine, ABS assessment, and authentication.
*Admin and Facilitator accounts are already persisted in the database (or run `python -m app.db_seed` if reset needed).*

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- **API URL**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`

---

## 2. Public User Portal (`frontend`)
Primary consultation portal for Ayurvedic innovators, manufacturers, and researchers.
*Features*: Grounded AI chat, 3-step product classification wizard, ABS biodiversity assessment, source explorer, and multi-category escalation modal.

```bash
cd frontend
npm run dev
```
- **User Portal URL**: `http://localhost:5173`

---

## 3. IP Facilitator Portal (`ip-facilitator`)
Dedicated workspace for institutional **IP Facilitators** acting as the **Human-in-the-Loop Safety & Reliability Fallback**.
*Features*:
- **No registration**: Login-only with assigned facilitator credentials.
- **Escalation Desk Queue**: Inspect and resolve queries escalated from AI chat (questions, clarifications, research dossiers, consultation requests).
- **Safety & Reliability Overview**: Framework explaining human intervention triggers.

```bash
cd ip-facilitator
npm run dev
```
- **Facilitator Desk URL**: `http://localhost:5174`
- **Seeded Facilitator Credentials**:
  - **Email**: `facilitator@ayush.gov.in`
  - **Password**: `Facilitator@123`

---

## 4. System Administrator Portal (`admin`)
Dedicated portal for **System Administrators & Compliance Officers**.
*Features*:
- **No registration**: Login-only with administrator credentials.
- **Corpus Sync & Vector Collections**: Live monitoring of the 5 canonical Qdrant collections (`wipo_lex_treaties`, `india_statutes_gazettes`, `drugs_cosmetics_corpus`, `fssai_ayurveda_aahara`, `nba_abs_guidelines`), indexed chunks, and manual sync triggers.
- **DPDP Immutable Audit Trail**: Cryptographically verified SHA-256 session logs, user hash verification, and event tracking.
- **Infrastructure & Diagnostics**: Health status across FastAPI, Supabase PostgreSQL, and Qdrant clusters.

```bash
cd admin
npm run dev
```
- **Admin Portal URL**: `http://localhost:5175`
- **Seeded Administrator Credentials**:
  - **Email**: `admin@ayush.gov.in`
  - **Password**: `Admin@123`

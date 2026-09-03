# IP-SAKTI Sahayak — Production Deployment Guide

Comprehensive deployment guide for **IP-SAKTI Sahayak** (Frontend React SPA, FastAPI Backend, and AI Multi-Agent RAG Service).

---

## Architecture Overview

```
[ Frontend (Vercel / Netlify) ]
             |
             v (HTTPS / REST & Voice WAV)
[ Backend + AI Service (Render / Railway / Docker) ]
             |
             +---> PostgreSQL (Supabase / Neon)
             +---> Vector Database (Qdrant Cloud)
             +---> LLM Reasoning (Google Gemini 1.5 Flash)
             +---> Multilingual Voice & STT/TTS (Sarvam AI)
             +---> Cache & Queue (Upstash Redis)
```

---

## Option 1: Managed Cloud Deployment (Recommended)

### A. Deploy Backend & AI Service (Render.com / Railway.app)

> [!TIP]
> **Resource Recommendation**: Deploy with at least **2GB RAM** (Render Standard plan or Railway Pro) to accommodate PyTorch and the `BAAI/bge-m3` (2.2GB) dense embedding model in memory.

#### Steps for Render:
1. Push your repository to GitHub.
2. Log in to [Render.com](https://render.com) and click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository: `vikramyadav6970-cell/IP-Shakti-Sahayak-V2`.
4. Choose **Docker** as the Environment (Render will automatically detect the root `Dockerfile`).
5. Set the **Instance Type** to at least **2 GB RAM (Standard)**.
6. Configure the **Environment Variables** in the Render Dashboard (see [Environment Variables Table](#environment-variables-reference) below).
7. Set **Health Check Path** to `/health/ready`.
8. Click **Create Web Service**.
9. Once deployed, copy your backend service URL (e.g., `https://ip-sakti-backend.onrender.com`).

---

### B. Deploy Frontend (Vercel / Netlify)

#### Steps for Vercel:
1. Log in to [Vercel.com](https://vercel.com) and click **Add New...** $\rightarrow$ **Project**.
2. Select your GitHub repository: `vikramyadav6970-cell/IP-Shakti-Sahayak-V2`.
3. In the project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: `https://your-backend-service.onrender.com` *(your deployed backend URL from Step A)*
5. Click **Deploy**.
6. The `frontend/vercel.json` file will automatically handle Single-Page Application (SPA) routing for `/chat`, `/expert`, and all client routes.

#### Steps for Netlify (Alternative):
1. Log in to [Netlify.com](https://netlify.com) $\rightarrow$ **Add new site** $\rightarrow$ **Import an existing project**.
2. Base directory: `frontend`
3. Build command: `npm run build`
4. Publish directory: `frontend/dist`
5. Add environment variable: `VITE_API_BASE_URL` = `https://your-backend-service.onrender.com`.

---

## Option 2: Self-Hosted Docker / VPS (AWS EC2 / DigitalOcean)

Deploy the entire stack with Docker Compose on any Ubuntu/Linux server:

1. **Install Docker & Docker Compose**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose
   ```

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/vikramyadav6970-cell/IP-Shakti-Sahayak-V2.git
   cd IP-Shakti-Sahayak-V2
   ```

3. **Configure Environment Variables**:
   Create a `.env` file at the root:
   ```bash
   QDRANT_URL=https://your-qdrant-cluster.cloud.qdrant.io:6333
   QDRANT_API_KEY=your_qdrant_api_key
   GEMINI_API_KEY=your_gemini_api_key
   SARVAM_API_KEY=your_sarvam_api_key
   JWT_SECRET=super_secure_random_jwt_secret_min_32_chars
   ```

4. **Start the Stack**:
   ```bash
   docker-compose up -d --build
   ```

5. **Verify Running Containers**:
   ```bash
   docker ps
   curl http://localhost:8000/health/ready
   ```

---

## Environment Variables Reference

| Variable Name | Required | Description / Example |
|---|:---:|---|
| `DATABASE_URL` | **Yes** | Postgres async connection string: `postgresql+asyncpg://user:pass@host:5432/dbname?ssl=require` |
| `GEMINI_API_KEY` | **Yes** | Google AI Studio API key for Gemini 1.5 Flash reasoning |
| `SARVAM_API_KEY` | **Yes** | Sarvam AI API key for Indian language STT (`saaras:v3`) and TTS (`bulbul:v3`) |
| `QDRANT_URL` | **Yes** | Qdrant Cloud cluster URL (`https://xyz.cloud.qdrant.io:6333`) |
| `QDRANT_API_KEY` | **Yes** | Qdrant Cloud cluster API key |
| `EMBEDDING_PROVIDER` | **Yes** | Must be set to `bge-m3` for dense 1024-dim neural retrieval |
| `JWT_SECRET` | **Yes** | 32+ character random string for signing JWT tokens |
| `CORS_ORIGINS` | **Yes** | Comma-separated allowed origins (e.g. `https://my-app.vercel.app,http://localhost:5173`) |
| `REDIS_URL` | Optional | Upstash Redis URL (`rediss://...`) for Celery & rate limiting |
| `ENVIRONMENT` | Optional | `production` (default in Dockerfile) |
| `PORT` | Optional | `8000` (default) |
| `VITE_API_BASE_URL` | **Frontend** | URL pointing to the deployed backend (e.g. `https://ip-sakti-backend.onrender.com`) |

---

## Post-Deployment Verification Checklist

- [ ] **Backend Health Probe**:
  `curl -i https://your-backend.onrender.com/health` returns `{"status": "healthy"}`
- [ ] **Database Readiness**:
  `curl -i https://your-backend.onrender.com/health/ready` returns `{"status": "ready", "database": "connected"}`
- [ ] **AI Multi-Agent RAG**:
  Querying via Frontend or `/api/v1/chat` triggers `BAAI/bge-m3` embedding search against Qdrant and grounds response with statutory citations.
- [ ] **Voice Pipeline**:
  `POST /api/v1/chat/voice` transcribes speech via Sarvam STT, performs RAG reasoning, and synthesizes audio via Sarvam TTS.
- [ ] **SPA Navigation**:
  Reloading `/chat`, `/expert`, or `/dashboard` in the browser returns the page without a 404 error.

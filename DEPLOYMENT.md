# IP-SAKTI Sahayak — Production Deployment Guide

Comprehensive deployment guide for **IP-SAKTI Sahayak** (Frontend React SPA, FastAPI Backend, and AI Multi-Agent RAG Service).

---

## Free-Tier Solutions for the 512MB RAM Constraint

The neural embedding model (`BAAI/bge-m3`) requires ~2.2GB RAM. Since cloud free tiers (like Render $0/mo) provide **512MB RAM**, you have two 100% free production solutions:

```
[ ARCHITECTURE OPTION 1: Serverless Split (Recommended for Render 512MB) ]

[ Vercel / Netlify ] ---> [ Render Backend (512MB RAM Free) ] ---> [ Qdrant Cloud ]
                                    |
                                    v (HTTP POST /embed)
                         [ Free HuggingFace Space ] (16GB RAM Free)
                         (Runs BAAI/bge-m3 in RAM)
```

```
[ ARCHITECTURE OPTION 2: All-in-One Free 16GB RAM ]

[ Vercel / Netlify ] ---> [ Hugging Face Docker Space ] (16GB RAM + 2 vCPU Free)
                         (Runs FastAPI Backend + AI + BAAI/bge-m3 together)
```

---

## Option 1: Render Free Tier (512MB) + Free Hugging Face Embedding Microservice

### Step 1: Deploy the Embedding Model on Hugging Face Spaces (100% FREE, 16GB RAM)
1. Go to [Hugging Face Spaces](https://huggingface.co/new-space).
2. Set Space Name: `bge-m3-embedder`
3. License: `apache-2.0`
4. SDK: Select **Docker** $\rightarrow$ **Blank**.
5. Hardware: **CPU Basic (2 vCPU, 16 GB RAM) — Free**.
6. Visibility: **Public**.
7. Click **Create Space**.
8. In the Space files tab, upload the 3 files from [`ai/deploy_bge_m3_space/`](file:///d:/Hackathons/SIH%20Project/ip-sakti-V2/ai/deploy_bge_m3_space/):
   - `Dockerfile`
   - `requirements.txt`
   - `app.py`
9. Once built (takes ~2 minutes), your embedding endpoint will be live at:
   `https://<your-hf-username>-bge-m3-embedder.hf.space/embed`

---

### Step 2: Deploy Backend on Render ($0 / Free 512MB Tier)
1. Log in to [Render.com](https://render.com) $\rightarrow$ **New +** $\rightarrow$ **Web Service**.
2. Connect your GitHub repository: `vikramyadav6970-cell/IP-Shakti-Sahayak-V2`.
3. Choose **Docker** as the Environment.
4. Select the **Free Plan (512 MB RAM / 0.1 CPU)**.
5. In **Environment Variables**, add:
   - `EMBEDDING_PROVIDER`: `remote`
   - `EMBEDDING_API_URL`: `https://<your-hf-username>-bge-m3-embedder.hf.space/embed`
   - `DATABASE_URL`: `postgresql+asyncpg://...` *(from Supabase / Neon)*
   - `GEMINI_API_KEY`: `your_gemini_api_key`
   - `SARVAM_API_KEY`: `your_sarvam_api_key`
   - `QDRANT_URL`: `https://your-cluster.cloud.qdrant.io:6333`
   - `QDRANT_API_KEY`: `your_qdrant_api_key`
   - `JWT_SECRET`: `your_random_32_char_secret`
   - `CORS_ORIGINS`: `https://your-frontend.vercel.app,http://localhost:5173`
6. Set **Health Check Path** to `/health/ready`.
7. Click **Create Web Service**.
8. The backend will consume only **~65 MB RAM** on Render!

---

## Option 2: Deploy Entire Backend on Hugging Face Spaces (All-in-One 16GB RAM Free)

You can host the entire FastAPI backend with the local 2.2GB model directly on Hugging Face Spaces:

1. Create a new Space on [huggingface.co/new-space](https://huggingface.co/new-space).
2. Select **Docker**. Hardware: **CPU Basic (16GB RAM) - Free**.
3. Push/Sync this repository to the Hugging Face Space.
4. Add your secrets (`DATABASE_URL`, `GEMINI_API_KEY`, `SARVAM_API_KEY`, `QDRANT_URL`, etc.) under Space **Settings $\rightarrow$ Variables and Secrets**.
5. Your backend will be accessible at `https://<username>-<space-name>.hf.space`.

---

## Deploying the Frontend (Vercel / Netlify)

1. Log in to [Vercel.com](https://vercel.com) $\rightarrow$ **Add New...** $\rightarrow$ **Project**.
2. Import `vikramyadav6970-cell/IP-Shakti-Sahayak-V2`.
3. Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-backend-url` *(from Render or HuggingFace)*
5. Click **Deploy**.

---

## Environment Variables Reference

| Variable Name | Required | Description / Example |
|---|:---:|---|
| `DATABASE_URL` | **Yes** | Postgres async connection string: `postgresql+asyncpg://user:pass@host:5432/dbname?ssl=require` |
| `GEMINI_API_KEY` | **Yes** | Google AI Studio API key for Gemini 1.5 Flash reasoning |
| `SARVAM_API_KEY` | **Yes** | Sarvam AI API key for Indian language STT (`saaras:v3`) and TTS (`bulbul:v3`) |
| `QDRANT_URL` | **Yes** | Qdrant Cloud cluster URL (`https://xyz.cloud.qdrant.io:6333`) |
| `QDRANT_API_KEY` | **Yes** | Qdrant Cloud cluster API key |
| `EMBEDDING_PROVIDER` | **Yes** | `remote` (for 512MB RAM Render) or `bge-m3` (if 2GB+ RAM available) |
| `EMBEDDING_API_URL` | If remote | `https://<username>-bge-m3-embedder.hf.space/embed` |
| `JWT_SECRET` | **Yes** | 32+ character random string for signing JWT tokens |
| `ENCRYPTION_MASTER_KEY` | **Yes** | 32+ character dedicated symmetric key for encrypting user connector secrets at rest (isolated from JWT_SECRET) |
| `CORS_ORIGINS` | **Yes** | Comma-separated allowed origins (e.g. `https://my-app.vercel.app,http://localhost:5173`) |
| `VITE_API_BASE_URL` | **Frontend** | URL pointing to the deployed backend |

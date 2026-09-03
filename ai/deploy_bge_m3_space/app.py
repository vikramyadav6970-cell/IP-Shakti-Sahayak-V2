"""
Standalone High-Performance BAAI/bge-m3 Embedding Microservice
Deployable to a 100% FREE Hugging Face Space (16 GB RAM + 2 vCPU).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
import torch

app = FastAPI(title="BGE-M3 Dense Embedding Microservice", version="1.0.0")

# Load BAAI/bge-m3 into memory
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer("BAAI/bge-m3", device=device)

class EmbedRequest(BaseModel):
    texts: List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int

@app.get("/")
def root():
    return {"status": "ok", "model": "BAAI/bge-m3", "dimension": 1024, "device": device}

@app.post("/embed", response_model=EmbedResponse)
def embed_texts(req: EmbedRequest):
    if not req.texts:
        return EmbedResponse(embeddings=[], dimension=1024)
    try:
        with torch.inference_mode():
            vectors = model.encode(req.texts, normalize_embeddings=True, show_progress_bar=False)
        return EmbedResponse(embeddings=[v.tolist() for v in vectors], dimension=1024)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

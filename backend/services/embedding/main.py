"""
Service d'Embedding
Génère des embeddings vectoriels pour le texte
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator
import os
import torch

# Configuration
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

# Initialize FastAPI
app = FastAPI(
    title="OpenRAG Embedding Service",
    description="Service de génération d'embeddings",
    version="1.0.0"
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Load model
logger.info(f"Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME, device=DEVICE)
logger.info(f"Model loaded successfully on {DEVICE}")

# ============================================
# Models
# ============================================

class EmbedRequest(BaseModel):
    """Requête pour générer un embedding"""
    text: str

class EmbedBatchRequest(BaseModel):
    """Requête pour générer plusieurs embeddings"""
    texts: List[str]

class EmbedResponse(BaseModel):
    """Réponse contenant l'embedding"""
    embedding: List[float]
    dimension: int

class EmbedBatchResponse(BaseModel):
    """Réponse contenant plusieurs embeddings"""
    embeddings: List[List[float]]
    dimension: int
    count: int

# ============================================
# Routes
# ============================================

@app.get("/")
async def root():
    """Point d'entrée racine"""
    return {
        "service": "OpenRAG Embedding Service",
        "model": MODEL_NAME,
        "device": DEVICE,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Vérification de santé"""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": DEVICE,
        "dimension": model.get_sentence_embedding_dimension()
    }

@app.post("/embed", response_model=EmbedResponse)
async def generate_embedding(request: EmbedRequest):
    """
    Génère un embedding pour un texte
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Generate embedding
        embedding = model.encode(
            request.text,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return EmbedResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding)
        )
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed/batch", response_model=EmbedBatchResponse)
async def generate_embeddings_batch(request: EmbedBatchRequest):
    """
    Génère des embeddings pour plusieurs textes (batch)
    Optimisé pour le traitement de masse
    """
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="Texts list cannot be empty")
        
        # Filter empty texts
        valid_texts = [text for text in request.texts if text and text.strip()]
        
        if not valid_texts:
            raise HTTPException(status_code=400, detail="All texts are empty")
        
        # Generate embeddings in batch
        embeddings = model.encode(
            valid_texts,
            batch_size=BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return EmbedBatchResponse(
            embeddings=embeddings.tolist(),
            dimension=model.get_sentence_embedding_dimension(),
            count=len(embeddings)
        )
        
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model/info")
async def model_info():
    """Retourne les informations sur le modèle"""
    return {
        "model_name": MODEL_NAME,
        "dimension": model.get_sentence_embedding_dimension(),
        "max_seq_length": model.max_seq_length,
        "device": str(model.device),
        "pooling": "mean"  # Most sentence-transformers use mean pooling
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

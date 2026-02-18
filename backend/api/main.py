"""
OpenRAG API Gateway
Point d'entrée principal pour toutes les requêtes utilisateur
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import os
from loguru import logger
import uuid
from datetime import datetime

# Configuration
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8001")
API_VERSION = "1.0.0"

# Initialize FastAPI
app = FastAPI(
    title="OpenRAG API",
    description="API Gateway pour la solution RAG",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À configurer selon vos besoins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Models
# ============================================

class QueryRequest(BaseModel):
    """Requête de recherche/question"""
    query: str = Field(..., description="Question ou requête de l'utilisateur")
    collection_id: Optional[str] = Field(None, description="ID de la collection à interroger")
    max_results: int = Field(5, description="Nombre maximum de résultats", ge=1, le=20)
    use_llm: bool = Field(True, description="Utiliser le LLM pour générer une réponse")
    metadata_filter: Optional[dict] = Field(None, description="Filtres de métadonnées")

class QueryResponse(BaseModel):
    """Réponse à une requête"""
    query_id: str
    answer: Optional[str] = None
    sources: List[dict] = []
    execution_time_ms: int
    timestamp: str

class DocumentUploadResponse(BaseModel):
    """Réponse après upload de document"""
    document_id: str
    filename: str
    status: str
    message: str

class HealthResponse(BaseModel):
    """Statut de santé de l'API"""
    status: str
    version: str
    timestamp: str
    services: dict

# ============================================
# Routes
# ============================================

@app.get("/", tags=["General"])
async def root():
    """Point d'entrée racine"""
    return {
        "service": "OpenRAG API Gateway",
        "version": API_VERSION,
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Vérification de santé de l'API et des services"""
    services = {}
    
    # Check orchestrator
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
            services["orchestrator"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        services["orchestrator"] = "unreachable"
        logger.error(f"Orchestrator health check failed: {e}")
    
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        timestamp=datetime.utcnow().isoformat(),
        services=services
    )

@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def process_query(request: QueryRequest):
    """
    Traiter une requête utilisateur
    
    Cette endpoint :
    1. Recherche les documents pertinents
    2. Génère une réponse avec le LLM (si activé)
    3. Retourne la réponse et les sources
    """
    query_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        # Timeout augmenté pour permettre la génération LLM (peut prendre 30-120s)
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/process-query",
                json={
                    "query_id": query_id,
                    "query": request.query,
                    "collection_id": request.collection_id,
                    "max_results": request.max_results,
                    "use_llm": request.use_llm,
                    "metadata_filter": request.metadata_filter
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Orchestrator error: {response.text}"
                )
            
            result = response.json()
            
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return QueryResponse(
            query_id=query_id,
            answer=result.get("answer"),
            sources=result.get("sources", []),
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Query timeout")
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    collection_id: Optional[str] = None
):
    """
    Upload un document pour indexation
    
    Formats supportés : PDF, DOCX, TXT, MD, etc.
    """
    document_id = str(uuid.uuid4())
    
    try:
        # Lire le contenu du fichier
        content = await file.read()
        
        # Envoyer à l'orchestrateur
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, content, file.content_type)}
            data = {
                "document_id": document_id,
                "collection_id": collection_id or "default"
            }
            
            response = await client.post(
                f"{ORCHESTRATOR_URL}/documents/ingest",
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upload failed: {response.text}"
                )
            
            result = response.json()
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="processing",
            message="Document uploaded successfully and is being processed"
        )
        
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", tags=["Documents"])
async def list_documents(
    collection_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Liste tous les documents"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "collection_id": collection_id,
                "status": status,
                "limit": limit,
                "offset": offset
            }
            response = await client.get(
                f"{ORCHESTRATOR_URL}/documents",
                params={k: v for k, v in params.items() if v is not None}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch documents"
                )
            
            return response.json()
            
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}", tags=["Documents"])
async def get_document(document_id: str):
    """Récupère les détails d'un document"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/documents/{document_id}")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch document"
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str):
    """Supprime un document"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(f"{ORCHESTRATOR_URL}/documents/{document_id}")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to delete document"
                )
            
            return {"status": "deleted", "document_id": document_id}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections", tags=["Collections"])
async def list_collections():
    """Liste toutes les collections"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/collections")
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch collections"
                )
            
            return response.json()
            
    except Exception as e:
        logger.error(f"List collections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

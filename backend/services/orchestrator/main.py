"""
OpenRAG Orchestrator
Coordonne l'ensemble du workflow RAG
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime
from loguru import logger
import asyncio

from services.document_processor import DocumentProcessor
from services.vector_store import VectorStoreService
from services.llm_service import LLMService
from services.storage import MinIOStorage
from database.db import DatabaseService

# Configuration
app = FastAPI(
    title="OpenRAG Orchestrator",
    description="Service d'orchestration pour le système RAG",
    version="1.0.0"
)

# Initialize services
db_service = DatabaseService()
storage = MinIOStorage()
vector_store = VectorStoreService()
document_processor = DocumentProcessor()
llm_service = LLMService()

# ============================================
# Models
# ============================================

class ProcessQueryRequest(BaseModel):
    query_id: str
    query: str
    collection_id: Optional[str] = None
    max_results: int = 5
    use_llm: bool = True
    metadata_filter: Optional[Dict[str, Any]] = None

class ProcessQueryResponse(BaseModel):
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

# ============================================
# Routes
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {}
    }
    
    # Check database
    try:
        await db_service.check_connection()
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check vector store
    try:
        vector_store.health_check()
        health_status["dependencies"]["vector_store"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["vector_store"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check MinIO
    try:
        storage.health_check()
        health_status["dependencies"]["minio"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["minio"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.post("/process-query", response_model=ProcessQueryResponse)
async def process_query(request: ProcessQueryRequest):
    """
    Traite une requête utilisateur selon le workflow RAG :
    1. Génère l'embedding de la requête
    2. Recherche dans le vector store
    3. Récupère les documents sources
    4. Génère une réponse avec le LLM
    """
    try:
        logger.info(f"Processing query: {request.query_id}")
        
        # 1. Recherche vectorielle
        logger.info("Step 1: Vector search")
        search_results = await vector_store.search(
            query=request.query,
            collection_name=request.collection_id or "documents_embeddings",
            limit=request.max_results or 5,  # Par défaut 5 résultats
            score_threshold=0.25  # Seuil abaissé pour meilleure couverture
        )
        
        if not search_results:
            logger.warning("No relevant documents found")
            return ProcessQueryResponse(
                answer="Je n'ai pas trouvé de documents pertinents pour répondre à votre question." if request.use_llm else None,
                sources=[],
                metadata={"search_results_count": 0}
            )
        
        # 2. Récupérer les contextes des chunks
        logger.info("Step 2: Retrieving document contexts")
        contexts = []
        sources = []
        
        for result in search_results:
            chunk_data = await db_service.get_chunk_by_vector_id(result["id"])
            if chunk_data:
                contexts.append({
                    "content": chunk_data["content"],
                    "score": result["score"],
                    "metadata": chunk_data.get("metadata", {})
                })
                
                # Get document info for sources
                doc_data = await db_service.get_document(chunk_data["document_id"])
                if doc_data:
                    sources.append({
                        "document_id": str(doc_data["id"]),
                        "filename": doc_data["filename"],
                        "chunk_index": chunk_data["chunk_index"],
                        "relevance_score": result["score"]
                    })
        
        # 3. Générer la réponse avec le LLM
        answer = None
        if request.use_llm and contexts:
            logger.info("Step 3: Generating LLM response")
            answer = await llm_service.generate_answer(
                query=request.query,
                contexts=[ctx["content"] for ctx in contexts]
            )
        
        # 4. Enregistrer la requête dans la base
        await db_service.save_query(
            query_id=request.query_id,
            query_text=request.query,
            response_text=answer,
            sources=sources
        )
        
        logger.info(f"Query processed successfully: {request.query_id}")
        
        return ProcessQueryResponse(
            answer=answer,
            sources=sources,
            metadata={
                "search_results_count": len(search_results),
                "contexts_used": len(contexts)
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    document_id: str = Form(...),
    collection_id: str = Form("default")
):
    """
    Ingère un nouveau document :
    1. Sauvegarde dans MinIO
    2. Enregistre les métadonnées en DB
    3. Lance le traitement asynchrone (chunking + embedding)
    """
    try:
        logger.info(f"Ingesting document: {file.filename}")
        
        # 1. Sauvegarder dans MinIO
        content = await file.read()
        object_key = f"{document_id}/{file.filename}"
        
        await storage.upload_file(
            bucket_name=os.getenv("MINIO_BUCKET_NAME", "documents"),
            object_key=object_key,
            file_data=content,
            content_type=file.content_type
        )
        
        # 2. Enregistrer les métadonnées en base
        await db_service.create_document(
            document_id=document_id,
            filename=file.filename,
            file_type=file.content_type,
            file_size=len(content),
            minio_object_key=object_key,
            collection_id=collection_id
        )
        
        # 3. Créer un job de traitement
        job_id = await db_service.create_processing_job(
            job_type="document_processing",
            document_id=document_id
        )
        
        # 4. Lancer le traitement asynchrone
        asyncio.create_task(
            process_document_async(document_id, object_key, file.filename, collection_id)
        )
        
        logger.info(f"Document ingestion started: {document_id}")
        
        return {
            "document_id": document_id,
            "job_id": job_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_async(document_id: str, object_key: str, filename: str, collection_id: str):
    """
    Traitement asynchrone d'un document :
    1. Télécharger depuis MinIO
    2. Extraire le texte et chunker
    3. Générer les embeddings
    4. Indexer dans Qdrant
    5. Mettre à jour le statut
    """
    try:
        logger.info(f"Starting async processing for document: {document_id}")
        
        # Update status to processing
        await db_service.update_document_status(document_id, "processing")
        
        # 1. Télécharger le fichier
        file_data = await storage.download_file(
            bucket_name=os.getenv("MINIO_BUCKET_NAME", "documents"),
            object_key=object_key
        )
        
        # 2. Extraire le texte et créer des chunks
        chunks = await document_processor.process_document(
            file_data=file_data,
            filename=filename
        )
        
        logger.info(f"Document chunked into {len(chunks)} pieces")
        
        # 3. Générer les embeddings et indexer
        for idx, chunk in enumerate(chunks):
            # Générer l'embedding
            embedding = await document_processor.generate_embedding(chunk["content"])
            
            # Créer un ID unique pour le vecteur (UUID requis par Qdrant)
            vector_id = str(uuid.uuid4())
            
            # Indexer dans Qdrant
            await vector_store.add_vector(
                collection_name=collection_id or "documents_embeddings",
                vector_id=vector_id,
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_index": idx,
                    "content": chunk["content"],
                    "metadata": chunk.get("metadata", {})
                }
            )
            
            # Sauvegarder le chunk en DB
            await db_service.create_chunk(
                document_id=document_id,
                chunk_index=idx,
                content=chunk["content"],
                vector_id=vector_id,
                metadata=chunk.get("metadata", {})
            )
        
        # 4. Mettre à jour le statut
        await db_service.update_document_status(document_id, "processed")
        
        logger.info(f"Document processing completed: {document_id}")
        
    except Exception as e:
        logger.error(f"Error in async document processing: {e}")
        await db_service.update_document_status(document_id, "failed")

@app.get("/documents")
async def list_documents(
    collection_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Liste les documents"""
    try:
        documents = await db_service.list_documents(
            collection_id=collection_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Récupère les détails d'un document"""
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Supprime un document"""
    try:
        # Get document info
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from MinIO
        await storage.delete_file(
            bucket_name=os.getenv("MINIO_BUCKET_NAME", "documents"),
            object_key=document["minio_object_key"]
        )
        
        # Delete vectors from Qdrant
        chunks = await db_service.get_document_chunks(document_id)
        for chunk in chunks:
            await vector_store.delete_vector(
                collection_name="documents_embeddings",
                vector_id=chunk["vector_id"]
            )
        
        # Delete from database (cascades to chunks)
        await db_service.delete_document(document_id)
        
        logger.info(f"Document deleted: {document_id}")
        return {"status": "deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections")
async def list_collections():
    """Liste toutes les collections"""
    try:
        collections = await db_service.list_collections()
        return {"collections": collections}
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

"""
Service Vector Store - Interface avec Qdrant
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from loguru import logger
import os
import httpx


class VectorStoreService:
    """Handles vector store operations on Qdrant"""
    
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.client = QdrantClient(host=self.host, port=self.port)
        self.vector_size = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))  # all-MiniLM-L6-v2
        self.embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8002")
        
        # Initialize default collection
        self._ensure_collection("documents_embeddings")
    
    def _ensure_collection(self, collection_name: str):
        """Create the Qdrant collection if it does not already exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                logger.info(f"Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection created: {collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    async def search(
        self,
        query: str,
        collection_name: str,
        limit: int = 5,
        score_threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche vectorielle dans Qdrant
        """
        try:
            # Generate query embedding
            query_vector = await self._generate_query_embedding(query)
            
            # Build filter if provided
            query_filter = None
            if metadata_filter:
                conditions = []
                for key, value in metadata_filter.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)
            
            # Search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            results = []
            for hit in search_results:
                results.append({
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload
                })
            
            logger.info(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching in vector store: {e}")
            raise
    
    async def add_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ):
        """Ajoute un vecteur dans la collection"""
        try:
            self._ensure_collection(collection_name)
            
            point = PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.debug(f"Vector added: {vector_id}")
            
        except Exception as e:
            logger.error(f"Error adding vector: {e}")
            raise
    
    async def delete_vector(self, collection_name: str, vector_id: str):
        """Supprime un vecteur"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=[vector_id]
            )
            logger.debug(f"Vector deleted: {vector_id}")
        except Exception as e:
            logger.error(f"Error deleting vector: {e}")
            raise
    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate a query embedding via the embedding service"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.embedding_service_url}/embed",
                    json={"text": query}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Embedding service error: {response.text}")
                
                result = response.json()
                return result["embedding"]
                
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    def health_check(self):
        """Check Qdrant connectivity"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            raise

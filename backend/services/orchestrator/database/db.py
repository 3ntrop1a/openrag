"""
Service de base de données PostgreSQL
"""

from typing import List, Dict, Any, Optional
import asyncpg
import os
from loguru import logger
import json
from datetime import datetime


class DatabaseService:
    """Gère les opérations sur PostgreSQL"""
    
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "postgres")
        self.port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.user = os.getenv("POSTGRES_USER", "openrag")
        self.password = os.getenv("POSTGRES_PASSWORD", "openrag123")
        self.database = os.getenv("POSTGRES_DB", "openrag_db")
        self.pool = None
    
    async def _get_pool(self):
        """Obtient ou crée le pool de connexions"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=2,
                max_size=10
            )
        return self.pool
    
    async def check_connection(self):
        """Vérifie la connexion à la base"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    
    # ============================================
    # Documents
    # ============================================
    
    async def create_document(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        minio_object_key: str,
        collection_id: str = "default"
    ):
        """Crée un nouveau document"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO documents (id, filename, original_filename, file_type, file_size, minio_object_key, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                document_id, filename, filename, file_type, file_size, minio_object_key, "uploaded"
            )
            
            # Add to collection
            collection = await conn.fetchrow(
                "SELECT id FROM collections WHERE name = $1", collection_id
            )
            
            if collection:
                await conn.execute(
                    """
                    INSERT INTO document_collections (document_id, collection_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    document_id, collection["id"]
                )
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un document par ID"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM documents WHERE id = $1", document_id
            )
            return dict(row) if row else None
    
    async def list_documents(
        self,
        collection_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Liste les documents avec filtres"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            query = "SELECT d.* FROM documents d"
            params = []
            conditions = []
            param_count = 0
            
            if collection_id:
                query += " JOIN document_collections dc ON d.id = dc.document_id"
                query += " JOIN collections c ON dc.collection_id = c.id"
                param_count += 1
                conditions.append(f"c.name = ${param_count}")
                params.append(collection_id)
            
            if status:
                param_count += 1
                conditions.append(f"d.status = ${param_count}")
                params.append(status)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY d.upload_date DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def update_document_status(self, document_id: str, status: str):
        """Met à jour le statut d'un document"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE documents 
                SET status = $1::text, 
                    processed_date = CASE WHEN $1::text = 'processed' THEN CURRENT_TIMESTAMP ELSE processed_date END
                WHERE id = $2::uuid
                """,
                status, document_id
            )
    
    async def delete_document(self, document_id: str):
        """Supprime un document (cascade aux chunks)"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
    
    # ============================================
    # Chunks
    # ============================================
    
    async def create_chunk(
        self,
        document_id: str,
        chunk_index: int,
        content: str,
        vector_id: str,
        metadata: Dict[str, Any]
    ):
        """Crée un chunk de document"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO document_chunks (document_id, chunk_index, content, vector_id, metadata)
                VALUES ($1, $2, $3, $4, $5)
                """,
                document_id, chunk_index, content, vector_id, json.dumps(metadata)
            )
    
    async def get_chunk_by_vector_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un chunk par son vector_id"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM document_chunks WHERE vector_id = $1", vector_id
            )
            if row:
                result = dict(row)
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"]
                return result
            return None
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Récupère tous les chunks d'un document"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM document_chunks WHERE document_id = $1 ORDER BY chunk_index",
                document_id
            )
            return [dict(row) for row in rows]
    
    # ============================================
    # Queries
    # ============================================
    
    async def save_query(
        self,
        query_id: str,
        query_text: str,
        response_text: Optional[str],
        sources: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ):
        """Sauvegarde une requête dans l'historique"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO queries (id, user_id, query_text, response_text, sources, execution_time_ms)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                query_id, user_id, query_text, response_text, json.dumps(sources), execution_time_ms
            )
    
    # ============================================
    # Processing Jobs
    # ============================================
    
    async def create_processing_job(self, job_type: str, document_id: str) -> str:
        """Crée un job de traitement"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO processing_jobs (job_type, document_id, status)
                VALUES ($1, $2, 'pending')
                RETURNING id
                """,
                job_type, document_id
            )
            return str(row["id"])
    
    # ============================================
    # Collections
    # ============================================
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """Liste toutes les collections"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM collections ORDER BY name")
            return [dict(row) for row in rows]

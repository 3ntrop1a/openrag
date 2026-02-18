#!/usr/bin/env python3
"""
Script pour retraiter tous les documents uploadés
"""

import asyncio
import os
import sys
import httpx
from pathlib import Path

# Ajouter le chemin parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "services" / "orchestrator"))

from database.db import DatabaseService
from services.storage import MinIOStorage
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStoreService

async def reprocess_all_documents():
    """Retraite tous les documents avec status='uploaded'"""
    
    print("🔄 Starting document reprocessing...")
    
    # Initialize services
    db_service = DatabaseService()
    storage = MinIOStorage()
    document_processor = DocumentProcessor()
    vector_store = VectorStoreService()
    
    # Get all documents with status='uploaded'
    documents = await db_service.list_documents(status='uploaded', limit=1000)
    
    print(f"📊 Found {len(documents)} documents to process")
    
    for idx, doc in enumerate(documents, 1):
        try:
            print(f"\n[{idx}/{len(documents)}] Processing: {doc['filename']}")
            
            # Update status
            await db_service.update_document_status(doc['id'], 'processing')
            
            # Download from MinIO
            file_data = await storage.download_file(
                bucket_name=os.getenv("MINIO_BUCKET_NAME", "documents"),
                object_key=doc['minio_object_key']
            )
            
            # Process document (extract text + chunk)
            chunks = await document_processor.process_document(
                file_data=file_data,
                filename=doc['filename']
            )
            
            print(f"  → Created {len(chunks)} chunks")
            
            # Generate embeddings and index
            for chunk_idx, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await document_processor.generate_embedding(chunk["content"])
                
                # Create vector ID
                import uuid
                vector_id = str(uuid.uuid4())
                
                # Index in Qdrant
                await vector_store.add_vector(
                    collection_name="documents_embeddings",
                    vector_id=vector_id,
                    vector=embedding,
                    payload={
                        "document_id": str(doc['id']),
                        "chunk_index": chunk_idx,
                        "content": chunk["content"],
                        "metadata": chunk.get("metadata", {})
                    }
                )
                
                # Save chunk in DB
                await db_service.create_chunk(
                    document_id=str(doc['id']),
                    chunk_index=chunk_idx,
                    content=chunk["content"],
                    vector_id=vector_id,
                    metadata=chunk.get("metadata", {})
                )
            
            # Update status to processed
            await db_service.update_document_status(doc['id'], 'processed')
            print(f"  ✅ Success!")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            await db_service.update_document_status(doc['id'], 'failed')
    
    print("\n✨ Reprocessing complete!")

if __name__ == "__main__":
    asyncio.run(reprocess_all_documents())

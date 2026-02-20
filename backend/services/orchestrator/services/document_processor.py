"""
Document Processing Service
Text extraction, chunking, and preparation for embedding
"""

from typing import List, Dict, Any
import io
from loguru import logger
import httpx
import os

# Document parsers
from pypdf import PdfReader
import docx
from unstructured.partition.auto import partition


class DocumentProcessor:
    """Processes documents for text extraction and chunking"""
    
    def __init__(self):
        self.embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8002")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "512"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    async def process_document(self, file_data: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Process a document:
        1. Extract text
        2. Split into chunks
        3. Return chunks with metadata
        """
        logger.info(f"Processing document: {filename}")
        
        # Extract text based on file type
        text = await self._extract_text(file_data, filename)
        
        if not text:
            raise ValueError(f"No text could be extracted from {filename}")
        
        # Chunk the text
        chunks = self._chunk_text(text, filename)
        
        logger.info(f"Extracted {len(chunks)} chunks from {filename}")
        
        return chunks
    
    async def _extract_text(self, file_data: bytes, filename: str) -> str:
        """Extrait le texte selon le type de fichier"""
        file_extension = filename.lower().split('.')[-1]
        
        try:
            if file_extension == 'pdf':
                return self._extract_from_pdf(file_data)
            elif file_extension in ['docx', 'doc']:
                return self._extract_from_docx(file_data)
            elif file_extension in ['txt', 'md', 'markdown']:
                return file_data.decode('utf-8')
            else:
                # Use unstructured for other formats
                return self._extract_with_unstructured(file_data, filename)
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            raise
    
    def _extract_from_pdf(self, file_data: bytes) -> str:
        """Extrait le texte d'un PDF"""
        pdf_file = io.BytesIO(file_data)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
        
        return text.strip()
    
    def _extract_from_docx(self, file_data: bytes) -> str:
        """Extrait le texte d'un fichier DOCX"""
        docx_file = io.BytesIO(file_data)
        doc = docx.Document(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    
    def _extract_with_unstructured(self, file_data: bytes, filename: str) -> str:
        """Utilise unstructured pour extraire le texte"""
        # Save temporarily
        temp_path = f"/tmp/{filename}"
        with open(temp_path, 'wb') as f:
            f.write(file_data)
        
        elements = partition(filename=temp_path)
        text = "\n\n".join([str(el) for el in elements])
        
        # Cleanup
        os.remove(temp_path)
        
        return text
    
    def _chunk_text(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.
        Uses a simple character-based approach.
        """
        chunks = []
        
        # Simple chunking by characters (can be improved with semantic chunking)
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            # Get chunk
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > self.chunk_size // 2:  # Only break if not too early
                    chunk_text = chunk_text[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append({
                "content": chunk_text.strip(),
                "metadata": {
                    "source_file": filename,
                    "chunk_index": chunk_idx,
                    "start_char": start,
                    "end_char": end
                }
            })
            
            # Move to next chunk with overlap
            start = end - self.chunk_overlap
            chunk_idx += 1
        
        return chunks
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate the embedding for a text string via the embedding service.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.embedding_service_url}/embed",
                    json={"text": text}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Embedding service error: {response.text}")
                
                result = response.json()
                return result["embedding"]
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

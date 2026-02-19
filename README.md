# OpenRAG

A self-hosted Retrieval-Augmented Generation (RAG) platform built on microservices. Upload documents, query them in natural language, and get structured LLM-generated answers backed by semantic vector search.

## Stack

| Layer | Technology |
|-------|-----------|
| API Gateway | FastAPI (port 8000) |
| Orchestrator | Python / httpx |
| Embedding | `paraphrase-multilingual-mpnet-base-v2` (768D) |
| Vector DB | Qdrant (port 6333) |
| LLM | Ollama · llama3.1:8b (port 11434) |
| Object Storage | MinIO (port 9000 / console 9001) |
| Metadata DB | PostgreSQL 16 (port 5432) |
| Cache / Queue | Redis 7 (port 6379) |
| Admin UI | Streamlit (port 8502) |
| User Chat UI | Next.js + ShadcnUI (port 3001) |

## Requirements

- Docker 26+ and Docker Compose 2.26+
- 16 GB RAM
- 50 GB disk (model weights + vectors)

## Quick Start

```bash
git clone https://github.com/3ntrop1a/openrag.git
cd openrag

# Start all services
sudo docker-compose up -d

# Wait for Ollama to pull the model (~4.9 GB, first run only)
sudo docker-compose logs -f ollama

# Start the chat frontend
cd frontend-nextjs
npm install
npm run dev   # http://localhost:3001
```

## Interfaces

| Interface | URL |
|-----------|-----|
| Chat UI (Next.js) | http://localhost:3001 |
| Admin Panel | http://localhost:8502 |
| API (Swagger) | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| MinIO Console | http://localhost:9001 |
| Mintlify Docs | http://localhost:3000 |

## API

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is a black hole?",
    "collection_id": "default",
    "max_results": 5,
    "use_llm": true
  }'
```

Upload a document:

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@document.pdf" \
  -F "collection_id=default"
```

## Configuration

| Parameter | Value |
|-----------|-------|
| Embedding model | `paraphrase-multilingual-mpnet-base-v2` |
| Chunk size | 2000 chars |
| Chunk overlap | 200 chars |
| LLM | `llama3.1:8b` |
| Temperature | 0.3 |
| Max tokens | 4096 |
| Ollama timeout | 300s |

## Documentation

Full Mintlify docs in the `docs/` folder:

```bash
npm install -g mintlify
cd docs && mintlify dev   # http://localhost:3000
```

Covers architecture, API reference, embedding configuration, and experiment results.

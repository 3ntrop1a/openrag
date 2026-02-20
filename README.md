# OpenRAG

A self-hosted Retrieval-Augmented Generation (RAG) platform built on microservices. Upload documents, query them in natural language, and get structured LLM-powered answers backed by semantic vector search.

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
| Frontend | Next.js + shadcn/ui (port 3000) |

## Requirements

- Docker 26+ and Docker Compose 2.26+
- 16 GB RAM minimum
- 50 GB disk (model weights + vectors)

## Quick Start

```bash
git clone https://github.com/3ntrop1a/openrag.git
cd openrag

# Start all services
docker-compose up -d

# Wait for Ollama to pull the model (~4.9 GB on first run)
docker-compose logs -f ollama

# Start the frontend
cd frontend-nextjs && npm install && npm run dev
# http://localhost:3000
```

## Interfaces

| Interface | URL |
|-----------|-----|
| Chat UI | http://localhost:3000 |
| Admin Panel | http://localhost:3000/admin |
| API (Swagger) | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| MinIO Console | http://localhost:9001 |

## API

Query your documents:

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

Full API reference is available via Swagger at `http://localhost:8000/docs` once the stack is running.

## Configuration

| Parameter | Default |
|-----------|---------|
| Embedding model | `paraphrase-multilingual-mpnet-base-v2` |
| Chunk size | 2000 chars |
| Chunk overlap | 200 chars |
| LLM | `llama3.1:8b` |
| Temperature | 0.3 |
| Max tokens | 4096 |
| Ollama timeout | 300s |

## Contributing

PRs and issues are welcome. Please open an issue before submitting large changes.

## License

MIT

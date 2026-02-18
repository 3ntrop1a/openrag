# Structure du projet OpenRAG

```
openrag/
├── README.md                           # Documentation principale
├── QUICKSTART.md                       # Guide de démarrage rapide
├── Makefile                            # Commandes make utiles
├── docker-compose.yml                  # Configuration Docker Compose
├── .env.example                        # Exemple de configuration
├── .gitignore                          # Fichiers à ignorer par Git
│
├── backend/                            # Code backend Python
│   ├── requirements.txt                # Dépendances Python
│   │
│   ├── api/                            # API Gateway (FastAPI)
│   │   ├── Dockerfile
│   │   ├── main.py                     # Point d'entrée API
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── orchestrator/               # Service orchestrateur
│   │   │   ├── Dockerfile
│   │   │   ├── main.py                 # Orchestrateur principal
│   │   │   ├── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── document_processor.py  # Traitement documents
│   │   │   │   ├── vector_store.py        # Interface Qdrant
│   │   │   │   ├── llm_service.py         # Interface LLM
│   │   │   │   └── storage.py             # Interface MinIO
│   │   │   └── database/
│   │   │       ├── __init__.py
│   │   │       └── db.py                  # Interface PostgreSQL
│   │   │
│   │   └── embedding/                  # Service d'embeddings
│   │       ├── Dockerfile
│   │       ├── main.py                 # Service embeddings
│   │       └── __init__.py
│   │
│   └── database/
│       └── init.sql                    # Schéma PostgreSQL
│
├── docs/                               # Documentation Mintlify
│   ├── mint.json                       # Configuration Mintlify
│   ├── introduction.mdx                # Page d'introduction
│   ├── quickstart.mdx                  # Guide démarrage rapide
│   ├── architecture.mdx                # Architecture détaillée
│   │
│   ├── installation/
│   │   └── requirements.mdx            # Prérequis système
│   │
│   └── api-reference/
│       ├── introduction.mdx            # Introduction API
│       └── query/
│           └── process-query.mdx       # Endpoint de requête
│
├── scripts/                            # Scripts utilitaires
│   ├── setup.sh                        # Script d'installation
│   └── test.sh                         # Script de tests
│
└── monitoring/                         # Configuration monitoring
    └── prometheus.yml                  # Config Prometheus
```

## Description des composants

### Backend

#### API Gateway (`backend/api/`)
- Point d'entrée REST principal
- Validation des requêtes
- Routing vers l'orchestrateur
- Documentation Swagger automatique

#### Orchestrateur (`backend/services/orchestrator/`)
- Cœur du système RAG
- Coordonne tous les workflows
- Services inclus :
  - `document_processor.py` : Extraction de texte et chunking
  - `vector_store.py` : Gestion de Qdrant
  - `llm_service.py` : Interface avec Ollama/OpenAI/Anthropic
  - `storage.py` : Interface avec MinIO
  - `db.py` : Interface avec PostgreSQL

#### Service d'embeddings (`backend/services/embedding/`)
- Génération d'embeddings vectoriels
- Support de sentence-transformers
- Traitement par batch optimisé

### Infrastructure (Docker Compose)

Services déployés :
- **postgres** : Base de métadonnées (port 5432)
- **redis** : Cache et queue (port 6379)
- **minio** : Stockage d'objets (ports 9000, 9001)
- **qdrant** : Base vectorielle (ports 6333, 6334)
- **ollama** : Serveur LLM (port 11434)
- **embedding-service** : Service d'embeddings (port 8002)
- **orchestrator** : Orchestrateur (port 8001)
- **api** : API Gateway (port 8000)
- **prometheus** : Métriques (port 9090, optionnel)
- **grafana** : Dashboards (port 3000, optionnel)

### Documentation

Documentation complète avec Mintlify incluant :
- Guide de démarrage rapide
- Architecture détaillée
- Guides d'installation
- Référence API complète
- Guides d'utilisation

### Scripts

- `setup.sh` : Installation et configuration automatique
- `test.sh` : Suite de tests automatisés

### Makefile

Commandes utiles :
```bash
make install    # Installation complète
make start      # Démarrer les services
make stop       # Arrêter les services
make logs       # Voir les logs
make test       # Lancer les tests
make status     # Statut des services
make backup     # Sauvegarder les données
```

## Workflow principal

### 1. Ingestion de document
```
Client → API Gateway → Orchestrateur
    ↓
MinIO (stockage fichier)
    ↓
Document Processor (extraction + chunking)
    ↓
Embedding Service (vectorisation)
    ↓
Qdrant (indexation vecteurs)
    ↓
PostgreSQL (métadonnées)
```

### 2. Requête RAG
```
Client → API Gateway → Orchestrateur
    ↓
Embedding Service (vectorise la requête)
    ↓
Qdrant (recherche vecteurs similaires)
    ↓
PostgreSQL (récupère contenus)
    ↓
LLM Service (génère réponse)
    ↓
Client (réponse + sources)
```

## Technologies utilisées

### Backend
- **Python 3.11**
- **FastAPI** : Framework web
- **Uvicorn** : Serveur ASGI
- **Pydantic** : Validation de données
- **asyncpg** : Client PostgreSQL async
- **sentence-transformers** : Embeddings
- **LangChain** : Framework RAG

### Storage
- **PostgreSQL 16** : Base relationnelle
- **Redis 7** : Cache et queue
- **MinIO** : Stockage S3
- **Qdrant** : Base vectorielle

### AI/ML
- **Ollama** : LLM local
- **OpenAI/Anthropic** : LLM cloud (optionnel)
- **sentence-transformers** : Modèles d'embeddings

### Infrastructure
- **Docker & Docker Compose**
- **Prometheus & Grafana** : Monitoring (optionnel)

### Documentation
- **Mintlify** : Documentation interactive

## Volumes Docker

Données persistantes :
- `postgres_data` : Base de données PostgreSQL
- `redis_data` : Données Redis
- `minio_data` : Fichiers MinIO
- `qdrant_data` : Index Qdrant
- `ollama_data` : Modèles Ollama
- `models_cache` : Cache des modèles d'embeddings

## Ports exposés

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | API REST principale |
| Orchestrator | 8001 | Service interne |
| Embedding | 8002 | Service interne |
| PostgreSQL | 5432 | Base de données |
| Redis | 6379 | Cache |
| MinIO API | 9000 | API S3 |
| MinIO Console | 9001 | Interface web |
| Qdrant HTTP | 6333 | API REST |
| Qdrant gRPC | 6334 | API gRPC |
| Ollama | 11434 | API LLM |
| Prometheus | 9090 | Métriques |
| Grafana | 3000 | Dashboards |

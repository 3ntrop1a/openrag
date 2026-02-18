# Guide de démarrage rapide OpenRAG

Ce guide vous permet de démarrer rapidement avec OpenRAG.

## Installation en 3 étapes

### 1. Prérequis
- Docker & Docker Compose installés
- 4GB RAM minimum (8GB recommandé)
- 20GB d'espace disque

### 2. Installation

```bash
# Cloner le projet
git clone https://github.com/your-org/openrag.git
cd openrag

# Lancer l'installation automatique
make install

# Ou manuellement :
cp .env.example .env
docker-compose up -d
```

### 3. Premier test

```bash
# Attendre que les services démarrent (30 secondes)
docker-compose ps

# Créer un document de test
echo "OpenRAG est un système RAG open-source." > test.txt

# Uploader le document
curl -X POST http://localhost:8000/documents/upload -F "file=@test.txt"

# Attendre 10 secondes que le document soit traité

# Poser une question
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Qu'\''est-ce qu'\''OpenRAG ?"}'
```

## Accès aux interfaces

- **API Swagger** : http://localhost:8000/docs
- **MinIO Console** : http://localhost:9001 (admin/admin123456)
- **Qdrant Dashboard** : http://localhost:6333/dashboard

## Commandes utiles

```bash
make start      # Démarrer les services
make stop       # Arrêter les services
make logs       # Voir les logs
make test       # Lancer les tests
make status     # Voir le statut
```

## Configuration du LLM

Par défaut, OpenRAG utilise Ollama en local. Pour changer :

### Option 1 : Ollama (défaut)
```bash
# Télécharger un modèle
docker exec -it openrag-ollama ollama pull llama3.1:8b
```

### Option 2 : OpenAI
```env
# Dans .env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
OPENAI_API_KEY=sk-...
```

### Option 3 : Anthropic Claude
```env
# Dans .env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

## Structure du projet

```
openrag/
├── backend/
│   ├── api/              # API Gateway
│   ├── services/
│   │   ├── orchestrator/ # Orchestrateur principal
│   │   └── embedding/    # Service d'embeddings
│   └── database/         # Scripts SQL
├── docs/                 # Documentation Mintlify
├── scripts/              # Scripts utilitaires
├── docker-compose.yml    # Configuration Docker
└── .env                  # Configuration
```

## Troubleshooting

### Les services ne démarrent pas
```bash
docker-compose logs -f
```

### Pas de résultats pour les requêtes
Attendez que les documents soient traités :
```bash
curl http://localhost:8000/documents | jq '.documents[] | select(.status == "processed")'
```

### Ollama ne trouve pas le modèle
```bash
docker exec -it openrag-ollama ollama pull llama3.1:8b
```

## Documentation complète

Pour plus de détails, consultez la documentation complète :

```bash
cd docs
npx mintlify dev
```

Puis visitez http://localhost:3000

## Support

- 📚 Docs : https://docs.openrag.io
- 💬 Discord : https://discord.gg/openrag
- 🐛 Issues : https://github.com/your-org/openrag/issues

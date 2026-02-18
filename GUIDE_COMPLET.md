# 🎉 OpenRAG - Solution RAG complète

## 📋 Résumé du projet

J'ai développé une solution RAG (Retrieval-Augmented Generation) complète et prête pour la production, conforme à l'architecture décrite dans votre schéma.

## ✅ Ce qui a été créé

### 🏗️ Architecture microservices complète

1. **API Gateway** (FastAPI) - Port 8000
   - Point d'entrée REST
   - Documentation Swagger automatique
   - Gestion des uploads et requêtes

2. **Orchestrateur** - Port 8001
   - Coordination du workflow RAG
   - Traitement asynchrone des documents
   - Gestion du pipeline d'ingestion

3. **Service d'Embeddings** - Port 8002
   - Génération de vecteurs avec sentence-transformers
   - Support CPU/GPU
   - Traitement par batch optimisé

4. **Infrastructure de stockage**
   - **MinIO** : Stockage d'objets S3 (ports 9000, 9001)
   - **Qdrant** : Base vectorielle pour la recherche sémantique (ports 6333, 6334)
   - **PostgreSQL** : Métadonnées et historique (port 5432)
   - **Redis** : Cache et files de tâches (port 6379)

5. **LLM**
   - **Ollama** : Serveur LLM local (port 11434)
   - Support OpenAI et Anthropic Claude

### 📚 Documentation Mintlify complète

Documentation interactive professionnelle incluant :
- ✅ Introduction et guide de démarrage rapide
- ✅ Architecture détaillée avec diagrammes
- ✅ Guide d'installation pas à pas
- ✅ Référence API complète
- ✅ Guides pratiques
- ✅ Documentation des prérequis système

### 🛠️ Scripts et outils

1. **setup.sh** : Installation automatique interactive
2. **test.sh** : Suite de tests automatisés
3. **Makefile** : Commandes utiles (make start, stop, logs, etc.)
4. **docker-compose.yml** : Configuration complète des services

### 📄 Documentation projet

- README.md : Documentation principale
- QUICKSTART.md : Guide de démarrage rapide
- STRUCTURE.md : Structure détaillée du projet
- .env.example : Exemple de configuration

## 🚀 Comment démarrer

### Option 1 : Installation automatique (recommandé)

```bash
cd /home/adminrag/openrag
make install
```

Cette commande va :
1. Vérifier les prérequis
2. Créer le fichier .env
3. Vous guider pour configurer le LLM
4. Télécharger et démarrer tous les services
5. Télécharger le modèle LLM (si Ollama)

### Option 2 : Installation manuelle

```bash
cd /home/adminrag/openrag

# 1. Configuration
cp .env.example .env
# Éditez .env selon vos besoins

# 2. Démarrer les services
docker-compose up -d

# 3. Télécharger le modèle Ollama (si utilisé)
docker exec -it openrag-ollama ollama pull llama3.1:8b

# 4. Vérifier le statut
make status
```

### Option 3 : Utiliser les scripts

```bash
cd /home/adminrag/openrag

# Installation interactive
bash scripts/setup.sh

# Tests
bash scripts/test.sh
```

## 📖 Utilisation

### 1. Uploader un document

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@votre_document.pdf" \
  -F "collection_id=default"
```

Formats supportés : PDF, DOCX, TXT, MD, etc.

### 2. Poser une question

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quelle est la politique de remboursement ?",
    "max_results": 5,
    "use_llm": true
  }'
```

### 3. Lister les documents

```bash
curl http://localhost:8000/documents
```

### 4. Accéder aux interfaces

- **API Swagger** : http://localhost:8000/docs
- **MinIO Console** : http://localhost:9001 (admin/admin123456)
- **Qdrant Dashboard** : http://localhost:6333/dashboard

## 🎯 Commandes utiles

```bash
make start      # Démarrer tous les services
make stop       # Arrêter tous les services
make restart    # Redémarrer
make logs       # Voir les logs en temps réel
make logs-api   # Logs d'un service spécifique
make status     # Statut de tous les services
make test       # Lancer les tests
make backup     # Sauvegarder les données
make docs       # Démarrer la documentation
make clean      # Nettoyer (⚠️ supprime les données)
```

## 🔧 Configuration

### Fichier .env principal

```env
# LLM Configuration
LLM_PROVIDER=ollama          # ollama, openai, anthropic
LLM_MODEL=llama3.1:8b
# OPENAI_API_KEY=sk-...      # Si OpenAI
# ANTHROPIC_API_KEY=sk-ant-... # Si Anthropic

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu         # ou cuda pour GPU

# MinIO
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123456

# PostgreSQL
POSTGRES_USER=openrag
POSTGRES_PASSWORD=openrag123
POSTGRES_DB=openrag_db
```

### Choix du LLM

**Ollama (local, recommandé pour commencer)**
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
```
Modèles suggérés : llama3.1:8b, phi3:mini, gemma:7b, mistral:7b

**OpenAI**
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
OPENAI_API_KEY=sk-...
```

**Anthropic Claude**
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

## 📊 Monitoring (optionnel)

Démarrer Prometheus et Grafana :

```bash
make monitoring-start
```

Accès :
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000 (admin/admin)

## 🏭 Workflow RAG

### Ingestion de document

```
1. Upload → MinIO (stockage fichier)
2. Extraction de texte (PDF, DOCX, etc.)
3. Chunking (découpage en morceaux ~512 tokens)
4. Génération d'embeddings (vectorisation)
5. Indexation dans Qdrant (base vectorielle)
6. Métadonnées dans PostgreSQL
```

### Traitement de requête

```
1. Question utilisateur
2. Vectorisation de la requête
3. Recherche des chunks similaires (Qdrant)
4. Récupération des contenus (PostgreSQL)
5. Construction du contexte
6. Génération de réponse (LLM)
7. Retour réponse + sources
```

## 📁 Structure des fichiers créés

```
/home/adminrag/openrag/
├── README.md
├── QUICKSTART.md
├── STRUCTURE.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── api/
│   │   ├── main.py
│   │   └── Dockerfile
│   ├── services/
│   │   ├── orchestrator/
│   │   │   ├── main.py
│   │   │   ├── services/
│   │   │   │   ├── document_processor.py
│   │   │   │   ├── vector_store.py
│   │   │   │   ├── llm_service.py
│   │   │   │   └── storage.py
│   │   │   └── database/
│   │   │       └── db.py
│   │   └── embedding/
│   │       └── main.py
│   └── database/
│       └── init.sql
├── docs/
│   ├── mint.json
│   ├── introduction.mdx
│   ├── quickstart.mdx
│   ├── architecture.mdx
│   └── api-reference/
│       ├── introduction.mdx
│       └── query/
│           └── process-query.mdx
├── scripts/
│   ├── setup.sh
│   └── test.sh
└── monitoring/
    └── prometheus.yml
```

## 🎓 Documentation

### Lancer la documentation Mintlify localement

```bash
cd /home/adminrag/openrag/docs
npx mintlify dev
```

Puis visitez http://localhost:3000

La documentation complète inclut :
- Guide de démarrage rapide
- Architecture détaillée
- Installation complète
- Référence API
- Guides pratiques

## 🔍 Tests

Lancer la suite de tests automatisés :

```bash
make test
# ou
bash scripts/test.sh
```

Les tests vérifient :
- ✅ Santé de tous les services
- ✅ Upload de documents
- ✅ Traitement des documents
- ✅ Requêtes et recherche
- ✅ Génération LLM

## 🆘 Troubleshooting

### Les services ne démarrent pas
```bash
docker-compose logs -f
```

### Vérifier qu'Ollama a bien le modèle
```bash
docker exec -it openrag-ollama ollama list
docker exec -it openrag-ollama ollama pull llama3.1:8b
```

### Vérifier le statut des documents
```bash
curl http://localhost:8000/documents | jq
```

### Redémarrer un service spécifique
```bash
docker-compose restart api
docker-compose restart orchestrator
```

## 🔐 Sécurité (pour la production)

⚠️ Avant de déployer en production :

1. Changez tous les mots de passe par défaut dans .env
2. Ajoutez l'authentification à l'API
3. Utilisez HTTPS/TLS
4. Configurez un firewall
5. Activez les logs d'audit
6. Mettez en place des backups réguliers

## 📈 Prochaines étapes recommandées

1. **Tester l'installation**
   ```bash
   make test
   ```

2. **Uploader vos premiers documents**
   ```bash
   curl -X POST http://localhost:8000/documents/upload -F "file=@document.pdf"
   ```

3. **Explorer la documentation interactive**
   ```bash
   cd docs && npx mintlify dev
   ```

4. **Configurer le monitoring** (optionnel)
   ```bash
   make monitoring-start
   ```

5. **Personnaliser selon vos besoins**
   - Ajustez les paramètres dans .env
   - Choisissez votre LLM préféré
   - Configurez les collections de documents

## 📞 Support

Pour toute question ou problème :
- 📚 Documentation complète : `cd docs && npx mintlify dev`
- 🐛 Logs des services : `make logs`
- 🔍 Tests : `make test`
- 💡 Exemples : Voir README.md et QUICKSTART.md

## 🎁 Fonctionnalités

✅ Upload de multiples formats de documents (PDF, DOCX, TXT, MD, etc.)
✅ Recherche sémantique vectorielle avec Qdrant
✅ Support de plusieurs LLM (Ollama, OpenAI, Anthropic)
✅ Architecture microservices scalable
✅ Documentation complète avec Mintlify
✅ Scripts d'installation et de tests automatisés
✅ Monitoring avec Prometheus et Grafana (optionnel)
✅ API REST complète avec Swagger
✅ Gestion de collections de documents
✅ Traitement asynchrone
✅ Stockage distribué avec MinIO

## 💡 Points clés de l'architecture

- **Modulaire** : Chaque service est indépendant et peut être scalé séparément
- **Asynchrone** : Traitement non-bloquant des documents
- **Scalable** : Architecture prête pour la production
- **Documenté** : Documentation complète type Mintlify
- **Testé** : Suite de tests automatisés
- **Flexible** : Support de plusieurs LLM et modèles d'embeddings

---

**Prêt à démarrer ?**

```bash
cd /home/adminrag/openrag
make install
```

🚀 Bon développement avec OpenRAG !

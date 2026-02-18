# OpenRAG - Solution RAG Complète avec Interfaces Web

Solution RAG (Retrieval-Augmented Generation) complète avec orchestration, stockage distribué, génération de réponses intelligentes et interfaces web pour utilisateurs et administrateurs.

## Présentation

OpenRAG est une plateforme RAG professionnelle conçue pour interroger intelligemment une base documentaire technique (WTE, Cisco, etc.). Le système combine recherche vectorielle et génération de langage naturel pour fournir des réponses précises et détaillées sans mentionner les sources dans le texte.

**Caractéristiques principales:**
- Interface web chat utilisateur (pas besoin de curl)
- Panel d'administration complet
- Réponses naturelles et détaillées (pas de "Document 1, Document 2...")
- 928 vecteurs indexés (28 documents WTE/Cisco)
- 10 microservices orchestrés
- Documentation Mintlify complète

## Architecture

### Services (10 microservices)

| Service | Description | Port |
|---------|-------------|------|
| **frontend-user** | Interface web chat Streamlit | 8501 |
| **frontend-admin** | Panel administration Streamlit | 8502 |
| **api** | API Gateway FastAPI | 8000 |
| **orchestrator** | Coordination RAG workflow | - |
| **embedding** | Service vectorisation | - |
| **ollama** | LLM (llama3.1:8b) | 11434 |
| **postgres** | Métadonnées documents | 5432 |
| **redis** | Cache et files d'attente | 6379 |
| **qdrant** | Base de données vectorielle | 6333 |
| **minio** | Stockage objets S3-compatible | 9000/9001 |

### Flux de Données

```
User → Interface Web (8501) → API (8000) → Orchestrator
                                              ↓
                                        Vector Search
                                              ↓
                                    Qdrant (928 chunks)
                                              ↓
                                    Context Retrieval
                                              ↓
                                    LLM Generation
                                              ↓
                                    Natural Answer
```

## Accès Rapide

| Interface | URL | Description |
|-----------|-----|-------------|
| **Chat Utilisateur** | http://localhost:8501 | Interface de dialogue |
| **Panel Admin** | http://localhost:8502 | Gestion système |
| **API Swagger** | http://localhost:8000/docs | Documentation API |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Vector DB |
| **MinIO Console** | http://localhost:9001 | Stockage (admin/admin123456) |

## Démarrage Rapide

### Prérequis

- Docker 26+ et Docker Compose 2.26+
- 16 GB RAM minimum
- 50 GB espace disque

### Installation

```bash
# Cloner le projet
git clone <repo-url>
cd openrag

# Lancer tous les services
sudo docker-compose up -d

# Vérifier le statut (10 services doivent être "Up")
sudo docker-compose ps

# Attendre que Ollama télécharge le modèle (4.9 GB)
sudo docker-compose logs -f ollama

# Accéder à l'interface utilisateur
firefox http://localhost:8501
```

### Premier Test

**Via Interface Web:**
1. Ouvrir http://localhost:8501
2. Taper: "Comment configurer un standard automatique ?"
3. Recevoir réponse détaillée en français

**Via API:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quels sont les postes Cisco disponibles ?",
    "collection_id": "default",
    "max_results": 5,
    "use_llm": true
  }' | jq -r '.answer'
```

## Fonctionnalités

### Interface Utilisateur (Nouveau)

**URL:** http://localhost:8501

- Chat interactif avec historique
- Affichage des sources avec scores de pertinence
- Configuration de la recherche (collection, nb résultats)
- Mode avec/sans LLM
- Exemples de questions
- Statistiques en temps réel

**Fichier:** `frontend/app_user.py`

### Panel Administration (Nouveau)

**URL:** http://localhost:8502

**6 Sections:**
1. **Dashboard**: Métriques (docs, vecteurs, collections), graphiques
2. **Documents**: Liste filtrable, recherche, détails
3. **Collections**: Explorer collections Qdrant
4. **Upload**: Interface d'upload avec métadonnées
5. **Users**: Gestion utilisateurs (à venir)
6. **Configuration**: Paramètres système

**Fichier:** `frontend/app_admin.py`

### Qualité des Réponses (Amélioré)

**Avant:**
- Réponses vagues
- "D'après le Document 1, Document 2..."
- Courtes (max 2048 tokens)

**Après:**
- Réponses détaillées et structurées
- Langage naturel sans mention de sources
- Longues et complètes (max 4096 tokens)
- Temperature optimisée (0.3) pour précision
- Score threshold abaissé (0.25) pour plus de contexte

**Fichiers modifiés:**
- `backend/services/orchestrator/services/llm_service.py`
- `backend/services/orchestrator/main.py`

## Technologies

### Backend
- **Python 3.11+**: Backend et services
- **FastAPI 0.104+**: Framework API REST
- **asyncpg 0.29+**: PostgreSQL asyncrone
- **httpx**: Client HTTP async

### Frontend (Nouveau)
- **Streamlit 1.31+**: Interfaces web
- **Pandas 2.2+**: Manipulation données
- **Plotly 5.18+**: Graphiques interactifs

### Infrastructure
- **PostgreSQL 16**: Base de données relationnelle
- **Redis 7**: Cache et queues
- **MinIO**: Stockage S3-compatible
- **Qdrant**: Base de données vectorielle
- **Ollama + llama3.1:8b**: LLM local (4.9 GB)
- **sentence-transformers**: Embeddings (all-MiniLM-L6-v2, 384-dim)

### DevOps
- **Docker & Docker Compose**: Orchestration conteneurs
- **Mintlify**: Documentation

## Documentation

### Documentation Mintlify Complète

```bash
cd docs
npm install -g mintlify
mintlify dev
# Ouvrir http://localhost:3000
```

**Structure:**
- **Get Started**: Introduction, installation
- **Tests**: Installation (14 issues), Upload (31 docs), Queries (10 tests)
- **Components**: PostgreSQL, Qdrant, Ollama, Redis, MinIO
- **API Reference**: Tous les endpoints documentés
- **Advanced**: Configuration LLM, scaling, monitoring

### Fichiers de Référence

- [RAPPORT_AMELIORATIONS.md](./RAPPORT_AMELIORATIONS.md): Détails des 4 améliorations majeures
- [RECAPITULATIF_FINAL.md](./RECAPITULATIF_FINAL.md): État final du système
- [SUCCES.md](./SUCCES.md): Tests de validation réussis
- [docs/tests/](./docs/tests/): Tous les tests avec commandes et résultats

## Données Actuelles

- **Documents uploadés**: 31 PDF (WTE/Cisco)
- **Documents traités**: 28 (90%)
- **Vecteurs indexés**: 928 chunks
- **Collection**: default (status: green)
- **Dimension vecteurs**: 384
- **Similarité**: cosine

## Commandes Utiles

### Gestion Services

```bash
# Démarrer
sudo docker-compose up -d

# Arrêter
sudo docker-compose down

# Logs temps réel
sudo docker-compose logs -f

# Redémarrer un service
sudo docker-compose restart orchestrator

# Reconstruire après modification
sudo docker-compose build service-name
sudo docker-compose up -d service-name
```

### Vérifications

```bash
# Santé API
curl http://localhost:8000/health | jq

# Nombre de vecteurs
curl http://localhost:6333/collections/default | jq '.result.points_count'

# Documents traités
curl http://localhost:8000/documents | jq '[.documents[] | select(.status=="processed")] | length'

# Services actifs
sudo docker-compose ps
```

### Upload Document

**Via Interface**: http://localhost:8502 > Upload

**Via API**:
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@document.pdf" \
  -F "collection_id=default" \
  -F "metadata={\"category\":\"guide\",\"source\":\"WTE\"}"
```

## Tests et Validation

Tous les tests documentés dans `docs/tests/` avec:
- Commandes curl exactes
- Outputs JSON complets
- Résultats de performance
- Résolution de problèmes

**Taux de réussite**: 95.7% (45/47 tests)

Voir [docs/tests/overview.mdx](./docs/tests/overview.mdx)

## Performance

| Métrique | Valeur |
|----------|--------|
| Recherche vectorielle | 100-200 ms |
| LLM première requête | 50-75 s (chargement modèle) |
| LLM requêtes suivantes | 5-15 s |
| Vecteurs indexés | 928 |
| Services actifs | 10/10 |

## Roadmap

- [x] Interface web utilisateur
- [x] Panel administration
- [x] Réponses naturelles sans mention de sources
- [x] Documentation Mintlify complète
- [ ] Authentification utilisateurs
- [ ] API webhooks
- [ ] Support multi-langues
- [ ] Monitoring Prometheus/Grafana
- [ ] Clustering haute disponibilité

## Support

**Documentation**: `docs/` (Mintlify)  
**Tests**: `docs/tests/`  
**Composants**: `docs/components/`  
**API**: http://localhost:8000/docs

## Contribution

Contributions bienvenues ! Voir [CONTRIBUTING.md](./CONTRIBUTING.md)

## Licence

MIT License - voir [LICENSE](./LICENSE)

---

**Version**: 1.1.0  
**Status**: Production Ready ✓  
**Last Update**: 18 février 2026

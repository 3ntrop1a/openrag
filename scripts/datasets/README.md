# Dataset Download Scripts

Scripts pour télécharger et importer des datasets scientifiques dans OpenRAG.

## 🎯 Objectif

Tester OpenRAG avec des corpus conséquents (500-1000+ documents) pour valider les performances du système RAG, par opposition au corpus WTE limité (33 documents).

## 📚 Datasets Disponibles

### 1. Wikipedia FR - Sciences (Recommandé)
- **Source**: Wikipedia français, catégorie "Sciences"
- **Taille**: 1000 articles (configurable)
- **Langue**: Français
- **Format**: JSON
- **Temps**: ~30 minutes de téléchargement

### 2. arXiv - Computer Science
- **Source**: arXiv.org
- **Taille**: 1000 papers (configurable)
- **Langue**: Anglais
- **Format**: JSON (abstracts)
- **Temps**: ~20 minutes de téléchargement

## 🚀 Utilisation Rapide

### Option 1: Wikipedia FR Sciences (1000 articles)

```bash
# 1. Télécharger les articles
cd /home/adminrag/openrag
python scripts/datasets/download_wikipedia.py --limit 1000 --output /tmp/wikipedia_fr_1000.json

# 2. Vérifier le fichier
du -h /tmp/wikipedia_fr_1000.json
cat /tmp/wikipedia_fr_1000.json | head -50

# 3. S'assurer qu'OpenRAG tourne
docker-compose ps
# Tous les services doivent être "Up"

# 4. Importer dans OpenRAG
python scripts/datasets/import_to_openrag.py /tmp/wikipedia_fr_1000.json

# 5. Surveiller le processing
docker-compose logs -f orchestrator
# Attendre "✅ Success!" pour tous les documents

# 6. Tester
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Qui a découvert la relativité générale?", "use_llm": true}'
```

### Option 2: arXiv CS.AI (1000 papers)

```bash
# 1. Installer dépendance
pip install arxiv

# 2. Télécharger les papers
python scripts/datasets/download_arxiv.py --category cs.AI --limit 1000 --output /tmp/arxiv_1000.json

# 3. Importer
python scripts/datasets/import_to_openrag.py /tmp/arxiv_1000.json

# 4. Tester
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are transformer models?", "use_llm": true}'
```

## 📖 Scripts Détaillés

### download_wikipedia.py

Télécharge des articles Wikipedia français de la catégorie "Sciences".

**Arguments**:
- `--limit`: Nombre d'articles à télécharger (default: 1000)
- `--output`: Fichier de sortie JSON (default: /tmp/wikipedia_fr_sciences_1000.json)

**Exemple**:
```bash
python scripts/datasets/download_wikipedia.py --limit 500 --output /tmp/wiki_500.json
```

**Output**:
```json
[
  {
    "title": "Relativité générale",
    "content": "La relativité générale est une théorie...",
    "url": "https://fr.wikipedia.org/wiki/Relativité_générale",
    "source": "wikipedia_fr",
    "category": "Sciences",
    "page_id": "12345"
  },
  ...
]
```

### download_arxiv.py

Télécharge des papers arXiv d'une catégorie spécifique.

**Arguments**:
- `--category`: Catégorie arXiv (cs.AI, cs.CL, cs.LG, cs.CV, etc.)
- `--limit`: Nombre de papers (default: 1000)
- `--output`: Fichier de sortie JSON

**Catégories populaires**:
- `cs.AI`: Artificial Intelligence
- `cs.CL`: Computation and Language (NLP)
- `cs.CV`: Computer Vision
- `cs.LG`: Machine Learning
- `cs.IR`: Information Retrieval

**Exemple**:
```bash
python scripts/datasets/download_arxiv.py --category cs.CL --limit 500 --output /tmp/arxiv_nlp_500.json
```

**Output**:
```json
[
  {
    "title": "Attention Is All You Need",
    "content": "The dominant sequence transduction models...",
    "authors": ["Ashish Vaswani", "Noam Shazeer", ...],
    "url": "http://arxiv.org/abs/1706.03762",
    "published": "2017-06-12T17:58:16+00:00",
    "categories": ["cs.CL", "cs.LG"],
    "source": "arxiv"
  },
  ...
]
```

### import_to_openrag.py

Importe un dataset JSON dans OpenRAG via l'API.

**Arguments**:
- `dataset_file`: Chemin vers le fichier JSON (required)
- `--api`: URL de l'API OpenRAG (default: http://localhost:8000)

**Exemple**:
```bash
python scripts/datasets/import_to_openrag.py /tmp/wikipedia_fr_1000.json --api http://localhost:8000
```

**Ce qui se passe**:
1. Lit le fichier JSON
2. Pour chaque document:
   - Crée un fichier texte avec métadonnées
   - Upload via API `/upload`
   - Rate limiting (0.05s entre requêtes)
3. Affiche statistiques de succès/erreurs

**Format uploadé**:
```
Title: Relativité générale

Source: https://fr.wikipedia.org/wiki/Relativité_générale
Category: Sciences

Content:
La relativité générale est une théorie de la gravitation...
```

## ⏱️ Temps de Processing Estimés

| Dataset | Téléchargement | Upload | Processing | Total |
|---------|----------------|--------|------------|-------|
| Wikipedia 500 | ~15 min | ~5 min | ~30 min | ~50 min |
| Wikipedia 1000 | ~30 min | ~10 min | ~1h | ~1h40 |
| arXiv 500 | ~10 min | ~5 min | ~15 min | ~30 min |
| arXiv 1000 | ~20 min | ~10 min | ~30 min | ~1h |

**Processing** = Extraction texte + Chunking + Embedding 768D + Stockage Qdrant

## 🔍 Vérifications

### Vérifier nombre de documents importés
```bash
curl -s http://localhost:8000/documents | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Documents: {len(d)}')"
```

### Vérifier nombre de vecteurs dans Qdrant
```bash
curl -s http://localhost:6333/collections/documents_embeddings | python3 -m json.tool | grep points_count
```

### Vérifier statut processing
```bash
curl -s http://localhost:8000/documents | python3 -c "import sys, json; d=json.load(sys.stdin); statuses = {}; [statuses.update({doc['status']: statuses.get(doc['status'], 0) + 1}) for doc in d]; print(statuses)"
```

Expected: `{'processed': 1000}` quand tout est fini

## 🧪 Tests Suggérés

### Wikipedia FR (après import)

```bash
# Test 1: Question factuelle
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Qui a découvert la pénicilline?", "use_llm": true}'

# Test 2: Question théorique
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explique le principe de la photosynthèse", "use_llm": true}'

# Test 3: Comparaison
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Différence entre ADN et ARN", "use_llm": true}'
```

### arXiv CS.AI (après import)

```bash
# Test 1: Architecture
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are transformer models?", "use_llm": true}'

# Test 2: Technique
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does self-attention work?", "use_llm": true}'

# Test 3: Application
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Applications of reinforcement learning", "use_llm": true}'
```

## 📊 Comparaison Résultats

Comparer avec les résultats WTE documentés dans [`docs/experiments/wte-corpus-analysis.mdx`](../docs/experiments/wte-corpus-analysis.mdx).

**Métriques à observer**:
- Nombre de documents retournés pertinents
- Position des documents les plus pertinents
- Scores de similarité
- Qualité de la réponse LLM
- Temps de réponse

## 🐛 Troubleshooting

### Erreur: "Cannot connect to API"
```bash
# Vérifier que les services tournent
docker-compose ps

# Redémarrer si nécessaire
docker-compose restart api orchestrator
```

### Erreur: "arxiv module not found"
```bash
pip install arxiv
```

### Processing trop lent
```bash
# Augmenter les workers (dans .env)
EMBEDDING_BATCH_SIZE=64  # Default: 32

# Redémarrer
docker-compose restart embedding-service
```

### Out of memory
```bash
# Réduire batch size
EMBEDDING_BATCH_SIZE=16  # Default: 32

# Ou traiter par lots plus petits
python scripts/datasets/download_wikipedia.py --limit 100
python scripts/datasets/import_to_openrag.py /tmp/wikipedia_fr_100.json
# Répéter plusieurs fois
```

## 📝 Logs

### Voir logs de processing
```bash
docker-compose logs -f orchestrator
```

### Voir logs d'embedding
```bash
docker-compose logs -f embedding-service
```

### Voir logs Qdrant
```bash
docker-compose logs -f qdrant
```

## 🎓 Pour la Soutenance

1. ✅ Documenter corpus WTE (33 docs) = **échec prévisible**
2. ✅ Télécharger Wikipedia FR Sciences (1000 docs)
3. ✅ Importer et processer
4. ✅ Tester requêtes variées
5. ✅ Comparer résultats WTE vs Wikipedia
6. ✅ Montrer que volume de données critique pour RAG
7. ✅ Documenter dans [`docs/experiments/`](../docs/experiments/)

## 📚 Ressources

- [Wikipedia API Documentation](https://www.mediawiki.org/wiki/API:Main_page)
- [arXiv API Documentation](https://arxiv.org/help/api/)
- [OpenRAG Documentation](http://localhost:3000)

## 🔄 Prochaines Étapes

Voir [`docs/experiments/DATASET_RECOMMENDATIONS.md`](../docs/experiments/DATASET_RECOMMENDATIONS.md) pour plus de datasets et recommandations.

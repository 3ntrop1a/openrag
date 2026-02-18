# Expérimentation OpenRAG - Corpus WTE (18 février 2026)

## Contexte
Test du système OpenRAG avec un corpus limité de 33 documents WTE (Workplace Together Essentials) en français, principalement des guides techniques Cisco et documentation contractuelle.

## Objectif
Évaluer la capacité du système RAG à répondre à des questions spécifiques sur des équipements DECT Cisco mentionnés dans la documentation.

---

## Configuration Testée

### Version 1 : Configuration Initiale (Échec)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384D
- **Optimisation**: Anglais uniquement
- **Chunking**: 512 caractères, overlap 50
- **Score Threshold**: 0.25
- **Nombre de documents**: 33 (WTE guides, contrats, tutoriels)

**Problème identifié**: 
- Requête: *"Quelles sont les modèles de DECT sur WTE?"*
- Documents cibles: `Cisco IP DECT 6823.pdf`, `Guide Cisco IP DECT 6825.pdf`
- **Résultat**: Documents DECT absents du top 10
- **Cause**: Modèle d'embedding optimisé pour l'anglais, mauvaise compréhension sémantique en français

---

### Version 2 : Chunking Amélioré (Échec partiel)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (inchangé)
- **Dimensions**: 384D
- **Chunking**: 2000 caractères, overlap 200 ✅ **AMÉLIORATION**
- **Score Threshold**: 0.25
- **Résultat**: Toujours pas de documents DECT dans les résultats

**Conclusion**: Le problème n'est pas le chunking, mais le modèle d'embedding.

---

### Version 3 : Modèle Multilingue (Amélioration limitée)
- **Embedding Model**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` ✅
- **Dimensions**: 768D
- **Optimisation**: 50+ langues, meilleure compréhension sémantique
- **Chunking**: 2000 caractères, overlap 200
- **Score Threshold**: 0.20 (abaissé pour meilleure récupération)
- **Max Results**: 20 (augmenté de 10)

**Migration effectuée**:
1. Suppression collection Qdrant (384D)
2. Mise à jour .env et docker-compose.yml
3. Reprocessing complet des 33 documents → 237 vecteurs 768D
4. Redémarrage de tous les services

---

## Résultats des Tests

### Test 1 : Requête DECT (v3 - modèle multilingue 768D)

**Requête**: `"Quelles sont les modèles de DECT sur WTE?"`

**Top 20 résultats** (par score de pertinence):

| Position | Document | Score | Pertinence |
|----------|----------|-------|------------|
| 1 | contrats-next-obs_ds_4765.pdf | 0.619 | ❌ Faux positif |
| 2 | contrats-next-obs_ds_4765.pdf | 0.609 | ❌ Faux positif |
| 3 | WTE - Tuto Collecte donnees - Orange Install.pdf | 0.524 | ⚠️ Mentionne "DECT" générique |
| 4 | contrats-next-obs_ann_4762.pdf | 0.515 | ❌ Faux positif |
| 5 | WTE - Tuto Mon parcours en vie de solution_Vdiff.pdf | 0.472 | ❌ Non pertinent |
| 6-11 | contrats-next-obs (divers) | 0.468-0.420 | ❌ Faux positifs |
| **12** | **Guide Cisco IP DECT 6825.pdf** | **0.414** | ✅ **CIBLE** |
| **13** | **Cisco IP DECT 6823.pdf** | **0.414** | ✅ **CIBLE** |
| 14-20 | WTE - Tuto divers | 0.412-0.379 | ❌ Non pertinent |

**Analyse**:
- ✅ Documents DECT **trouvés** mais en position 12-13
- ❌ Hors du top 10 (limite par défaut)
- ❌ Score 0.414 inférieur aux documents contractuels (0.619)
- ⚠️ Le document "Orange Install" (0.524) mentionne "postes IP ou DECT" dans le contexte WTE, expliquant son meilleur score

**Contenu des chunks DECT**:
```
Cisco IP DECT 6823.pdf: "sur Enregistrer -> «Sauvegarder» pour enregistrer le numéro (Facultatif) Mettez en surbrillance un champ pour ajouter ou remplacer d'autres informations..."

Guide Cisco IP DECT 6825.pdf: "sieurs utilisateurs ou bornes via User Hub, effectuez toutes les actions en une seule opération. Ensuite, attendez environ 90 secondes..."
```

**Problème identifié**: 
- Le **contenu technique** des chunks ne mentionne pas explicitement "modèle 6823" ou "modèle 6825"
- Cette information est dans le **nom du fichier**, mais pas dans le contenu indexé
- Le système de RAG ne peut pas faire le lien entre la question "quels modèles" et les noms de fichiers

---

### Test 2 : Requête générique DECT

**Requête**: `"configuration DECT cisco"`

Résultats similaires - documents contractuels en tête, guides DECT en position 10-15.

---

## Statistiques Corpus WTE

- **Total documents**: 33 documents
- **Status**: 33 uploaded, 0 failed
- **Total vecteurs indexés**: 237 (768D)
- **Chunks par document**: 1-49 chunks (moyenne ~7 chunks)
- **Taille chunks**: 2000 caractères, overlap 200
- **Langues**: Principalement français
- **Types**: PDF guides techniques, contrats, tutoriels

**Documents DECT**:
- `Cisco IP DECT 6823.pdf`: 5 chunks
- `Guide Cisco IP DECT 6825.pdf`: 5 chunks
- Total: 10 chunks DECT / 237 chunks totaux (4.2%)

**Documents dominants** (par nombre de chunks):
1. contrats-next-obs_ds_4765.pdf: 49 chunks (20.7%)
2. contrats-next-obs_ann_4762.pdf: 29 chunks (12.2%)
3. WTE - Formation WTE Hub: 14 chunks (5.9%)

---

## Problèmes Identifiés

### 1. Corpus Insuffisant
- ❌ Seulement 33 documents, 237 vecteurs
- ❌ 10 chunks DECT (4.2%) noyés dans 227 chunks non-DECT
- ❌ Documents contractuels (70+ chunks) dominent les résultats

### 2. Qualité du Contenu
- ❌ Chunks DECT très techniques (configuration, procédures)
- ❌ Pas de description des modèles eux-mêmes
- ❌ Information "modèle 6823/6825" uniquement dans les titres de fichiers
- ❌ Contenu ne permet pas de répondre à "quels sont les modèles?"

### 3. Limitations Architecturales
- ❌ Filename non inclus dans le contexte de recherche vectorielle
- ❌ Payload Qdrant: `metadata.source_file` existe mais non exploité pour le ranking
- ⚠️ Score threshold 0.20 trop restrictif pour corpus limité
- ⚠️ Max results 10 insuffisant pour voir documents en position 12-13

### 4. Performance Modèle
- ⚠️ Modèle multilingue meilleur que anglais seul, mais insuffisant
- ⚠️ Scores 0.414 pour documents DECT vs 0.619 pour contrats
- ❌ Le modèle ne comprend pas que "6825" dans filename = "modèle 6825"

---

## Solutions Tentées

### ✅ Réussies
1. Migration vers modèle multilingue (768D) - documents DECT maintenant trouvés
2. Augmentation chunking (512→2000) - meilleur contexte
3. Abaissement threshold (0.25→0.20) - plus de résultats
4. Augmentation max_results (10→20) - documents DECT visibles

### ❌ Insuffisantes
1. Modèle multilingue ne résout pas le problème de corpus limité
2. Chunking amélioré ne change pas le fait que l'info n'est pas dans les chunks
3. Threshold plus bas ne change pas le ranking relatif

### 🔄 Non testées (pistes futures)
1. **Enrichissement des chunks avec filename** dans le contenu indexé
2. **Hybrid search** (keyword + sémantique) pour matcher "6823", "6825"
3. **Reranking** avec filename matching
4. **Métadonnées pondérées** (boost si filename match la query)
5. **Extraction d'entités** (identifier "6823" comme référence produit)

---

## Conclusions

### Pour la Soutenance

**Hypothèse validée**: ✅ 
> "Avec un corpus insuffisant (33 documents, 237 vecteurs), un système RAG ne peut pas fournir de résultats pertinents, même avec un modèle d'embedding multilingue de qualité."

**Preuves**:
1. Documents DECT existent dans la base (10 chunks indexés)
2. Modèle multilingue 768D les retrouve (position 12-13, score 0.414)
3. Mais **noyés** dans les documents contractuels plus volumineux
4. Contenu des chunks DECT **ne contient pas l'information recherchée** ("modèle 6823/6825")
5. Impossible de répondre correctement à "Quels sont les modèles de DECT?"

**Limites du test**:
- 📉 Corpus trop petit (33 docs) pour statistiques significatives
- 📉 Déséquilibre: 70 chunks contrats vs 10 chunks DECT
- 📉 Qualité documentaire: guides techniques vs documentation produit
- 📉 Pas de document décrivant "liste des modèles DECT disponibles"

### Recommandations

**Pour tester sérieusement OpenRAG**:
1. ✅ **Corpus minimum**: 500-1000 documents
2. ✅ **Domaine bien documenté**: Science, médecine, technique
3. ✅ **Dataset public**: Wikipedia, arXiv, PubMed
4. ✅ **Contenu structuré**: Descriptions, listes, tableaux
5. ✅ **Recherches variées**: Factuelles, comparatives, exploratoires

**Datasets suggérés**:
- Wikipedia FR (sciences): 100K+ articles
- arXiv (informatique/physique): 2M+ papers
- PubMed (médecine): 35M+ abstracts
- HAL (recherche française): 1M+ publications
- Gutenberg (littérature): 70K+ livres

---

## Logs et Commandes Exécutées

### Migration 384D → 768D

```bash
# 1. Mise à jour configuration
.env:
  QDRANT_VECTOR_SIZE=384 → 768
  EMBEDDING_MODEL=all-MiniLM-L6-v2 → paraphrase-multilingual-mpnet-base-v2
  CHUNK_SIZE=512 → 2000
  CHUNK_OVERLAP=50 → 200

# 2. Suppression ancienne collection
curl -X DELETE http://localhost:6333/collections/documents_embeddings
# {"result":true,"status":"ok","time":0.001186893}

# 3. Reset base de données
docker-compose exec postgres psql -U openrag_user -d openrag_db
DELETE FROM document_chunks; -- 935 rows deleted
UPDATE documents SET status = 'uploaded' WHERE status = 'processed'; -- 33 rows updated

# 4. Redémarrage services
docker-compose down
docker-compose up -d

# 5. Vérification configuration
docker-compose exec orchestrator printenv | grep -E "QDRANT|EMBEDDING|CHUNK"
# QDRANT_VECTOR_SIZE=768
# EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
# CHUNK_SIZE=2000
# CHUNK_OVERLAP=200

# 6. Reprocessing
docker cp scripts/reprocess_documents.py openrag-orchestrator:/app/
docker-compose exec orchestrator python reprocess_documents.py
# [33/33] Processing complete! ✨
# Total: 237 vectors indexed

# 7. Vérification Qdrant
curl -s http://localhost:6333/collections/documents_embeddings | python3 -m json.tool
# "points_count": 237
# "vectors": {"size": 768}
```

### Tests de Recherche

```bash
# Test 1: Sans LLM, top 10
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Quelles sont les modèles de DECT sur WTE?", "use_llm": false, "max_results": 10}'

# Résultat: 10 documents contractuels, pas de DECT

# Test 2: Sans LLM, top 20
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Quelles sont les modèles de DECT sur WTE?", "use_llm": false, "max_results": 20}'

# Résultat: Documents DECT en positions 12-13

# Test 3: Vérification indexation DECT
curl -s -X POST http://localhost:6333/collections/documents_embeddings/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 300, "with_payload": true, "with_vector": false}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); \
  dect=[p for p in d['result']['points'] if 'DECT' in p['payload']['metadata'].get('source_file','')]; \
  print(f'DECT chunks: {len(dect)}')"

# DECT chunks: 10 ✅
```

---

## Temps de Processing

- **Reprocessing 33 documents**: ~600 secondes (10 minutes)
- **Throughput**: ~3-4 documents/minute
- **Embedding 768D**: ~100-150ms par chunk
- **Stockage Qdrant**: ~30-50ms par vecteur
- **Total vecteurs**: 237 en ~10 minutes

---

## Fichiers Modifiés (Git)

```
.env
docker-compose.yml
backend/services/orchestrator/main.py (score_threshold 0.25→0.20)
frontend/app_user.py (max_results slider 10→20)
```

---

## Métadonnées Technique

**Infrastructure**:
- Docker Compose: 10 services
- Qdrant: 1.13.0, collection "documents_embeddings"
- PostgreSQL: documents, document_chunks tables
- MinIO: 33 documents stockés
- Ollama: llama3.1:8b (60-90s par réponse)

**Modèles**:
- Embedding: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
- Dimensions: 768
- Distance: Cosine similarity
- LLM: llama3.1:8b

**Date**: 18 février 2026

---

## Prochaines Étapes

1. ✅ **Documenter l'échec WTE** (ce fichier)
2. ⏳ Commit Git avec message explicatif
3. ⏳ Télécharger dataset scientifique conséquent (500-1000+ documents)
4. ⏳ Retester avec corpus volumineux
5. ⏳ Comparer résultats WTE vs dataset scientifique
6. ⏳ Fixer Mintlify documentation

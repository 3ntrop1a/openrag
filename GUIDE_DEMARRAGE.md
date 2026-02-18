# 🚀 GUIDE DÉMARRAGE RAPIDE - OpenRAG v1.1.0

## Première Utilisation - 3 Minutes

### Option 1: Interface Web (Recommandé)

**1. Ouvrir le chat utilisateur:**
```bash
firefox http://localhost:8501
```

**2. Poser une question:**
- Dans le champ texte, taper: `Comment configurer un standard automatique ?`
- Cliquer "Envoyer" ou appuyer sur Entrée
- Attendre la réponse (5-15 secondes)

**3. Observer la réponse:**
- ✓ Réponse détaillée en français
- ✓ Structurée (listes, étapes)
- ✓ **SANS mention de "Document 1, 2, 3..."**
- ✓ Sources affichées en bas avec scores

**4. Exemples de questions:**
- "Quels sont les postes Cisco disponibles ?"
- "Comment gérer les files d'attente dans WTE ?"
- "Configuration d'un poste téléphonique 6871"
- "Installation de la plateforme WTE"

### Option 2: Via API (Curl)

**Requête simple (sans LLM):**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Configuration téléphone Cisco",
    "collection_id": "default",
    "max_results": 5,
    "use_llm": false
  }' | jq
```

**Avec génération LLM:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Comment configurer un standard automatique ?",
    "collection_id": "default",
    "max_results": 5,
    "use_llm": true
  }' | jq -r '.answer'
```

## Panel Administration

**URL:** http://localhost:8502

**Sections disponibles:**

1. **Dashboard** - Vue d'ensemble
   - Nombre de documents: 31
   - Vecteurs indexés: 928
   - Collections: 1 (default)
   - Graphiques temps réel

2. **Documents** - Gestion documents
   - Liste complète avec filtres
   - Recherche par nom
   - Détails (métadonnées, chunks)
   - Status processing

3. **Collections** - Explorer Qdrant
   - Collections disponibles
   - Configuration vecteurs (384-dim, cosine)
   - Nombre de points

4. **Upload** - Ajouter documents
   - Sélectionner PDF
   - Ajouter métadonnées (category, source)
   - Upload et processing automatique

5. **Configuration** - Settings système
   - Endpoints services
   - Paramètres LLM
   - Embedding model
   - Base de données

## Vérifier l'État du Système

**Script de test automatique:**
```bash
./test-system.sh
```

**Résultat attendu:**
```
✓ Tous les services sont actifs (10/10)
✓ API opérationnelle
✓ 928 vecteurs indexés dans Qdrant
✓ 31 documents traités
✓ Interface utilisateur accessible sur http://localhost:8501
✓ Panel admin accessible sur http://localhost:8502
✓ Recherche fonctionnelle: 3 sources trouvées en 0.037989s
✓ LLM opérationnel (5-60s)
```

## Commandes Essentielles

### Gestion Services

```bash
# Voir état services
sudo docker-compose ps

# Démarrer tous les services
sudo docker-compose up -d

# Arrêter tous les services
sudo docker-compose down

# Redémarrer un service spécifique
sudo docker-compose restart orchestrator

# Voir les logs en temps réel
sudo docker-compose logs -f

# Voir logs d'un service spécifique
sudo docker-compose logs -f orchestrator
```

### Santé du Système

```bash
# API health
curl http://localhost:8000/health | jq

# Nombre de vecteurs Qdrant
curl http://localhost:6333/collections/default | jq '.result.points_count'

# Documents traités
curl http://localhost:8000/documents | jq '[.documents[] | select(.status=="processed")] | length'

# Statistiques collections
curl http://localhost:8000/collections | jq
```

### Upload de Documents

**Via interface web:**
1. http://localhost:8502
2. Section "Upload"
3. Choisir fichier PDF
4. Remplir métadonnées (optionnel)
5. Cliquer "Upload"

**Via API:**
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@mon_document.pdf" \
  -F "collection_id=default" \
  -F "metadata={\"category\":\"guide\",\"source\":\"WTE\",\"author\":\"Cisco\"}"
```

## URLs Importantes

| Service | URL | Identifiants |
|---------|-----|--------------|
| **Chat Utilisateur** | http://localhost:8501 | - |
| **Panel Admin** | http://localhost:8502 | - |
| **API Swagger** | http://localhost:8000/docs | - |
| **API Health** | http://localhost:8000/health | - |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | - |
| **MinIO Console** | http://localhost:9001 | admin / admin123456 |

## Troubleshooting Rapide

### Problème: Service ne démarre pas

```bash
# Voir les logs d'erreur
sudo docker-compose logs service-name

# Exemple: orchestrator
sudo docker-compose logs orchestrator

# Redémarrer
sudo docker-compose restart service-name
```

### Problème: LLM trop lent

**Première requête:** 50-75 secondes (chargement modèle normal)  
**Requêtes suivantes:** 5-15 secondes

Si toujours lent:
```bash
# Vérifier CPU/RAM
sudo docker stats openrag-ollama

# Redémarrer Ollama
sudo docker-compose restart ollama
```

### Problème: Interface web ne charge pas

```bash
# Vérifier status frontend
sudo docker-compose ps | grep frontend

# Voir logs
sudo docker-compose logs frontend-user
sudo docker-compose logs frontend-admin

# Redémarrer
sudo docker-compose restart frontend-user frontend-admin
```

### Problème: Pas de résultats à la recherche

**Vérifier vecteurs:**
```bash
curl http://localhost:6333/collections/default | jq '.result.points_count'
```

**Si 0 ou vide:**
```bash
# Ré-uploader documents
cd /home/adminrag/openrag
./upload_wte_docs.sh  # Si script existe

# Ou via interface admin
firefox http://localhost:8502
# Section Upload
```

### Problème: Réponse mentionne "Document 1, 2..."

**Vérifier version orchestrator:**
```bash
# Reconstruire avec nouveaux prompts
sudo docker-compose build orchestrator
sudo docker-compose up -d orchestrator

# Vérifier logs
sudo docker-compose logs orchestrator | grep "temperature"
```

## Documentation Complète

### Fichiers de Référence

```bash
# Guide principal
cat README.md

# Détails améliorations
cat RAPPORT_AMELIORATIONS.md

# État final système
cat RECAPITULATIF_FINAL.md

# Liste fichiers modifiés
cat FICHIERS_MODIFIES.md

# Ce guide
cat GUIDE_DEMARRAGE.md
```

### Documentation Mintlify

```bash
cd docs
npm install -g mintlify  # Si pas installé
mintlify dev
# Ouvrir http://localhost:3000
```

**Sections disponibles:**
- Get Started (introduction, installation)
- Tests (installation, upload, queries)
- Components (PostgreSQL, Qdrant, Ollama, etc.)
- API Reference (tous endpoints)
- Advanced (configuration, scaling)

## Exemples d'Utilisation Avancée

### Recherche dans collection spécifique

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Configuration SVI",
    "collection_id": "default",
    "max_results": 10,
    "score_threshold": 0.3,
    "use_llm": true
  }' | jq -r '.answer'
```

### Upload avec métadonnées détaillées

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@guide_wte_v2.pdf" \
  -F "collection_id=default" \
  -F "metadata={
    \"title\": \"Guide WTE v2.0\",
    \"category\": \"documentation\",
    \"source\": \"WTE\",
    \"author\": \"Cisco France\",
    \"version\": \"2.0\",
    \"language\": \"fr\",
    \"doc_type\": \"guide_utilisateur\"
  }"
```

### Interroger l'API directement (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={
        "query": "Comment créer un utilisateur dans WTE ?",
        "collection_id": "default",
        "max_results": 5,
        "use_llm": True
    }
)

data = response.json()
print(f"Réponse: {data['answer']}")
print(f"Sources: {len(data['sources'])}")
print(f"Temps: {data['processing_time']}s")
```

## Workflow Recommandé

### Pour l'Utilisateur Final

1. Ouvrir http://localhost:8501
2. Poser questions naturelles en français
3. Lire réponses détaillées (sans "Document X")
4. Consulter sources si besoin (scores en bas)
5. Ajuster paramètres dans sidebar si nécessaire

### Pour l'Administrateur

1. Ouvrir http://localhost:8502
2. Vérifier Dashboard (métriques)
3. Consulter Documents (liste, status)
4. Uploader nouveaux documents via Upload
5. Vérifier processing (section Documents)
6. Monitorer collections Qdrant
7. Ajuster configuration si besoin

### Pour le Développeur

1. Lire documentation API: http://localhost:8000/docs
2. Tester endpoints avec curl ou Postman
3. Consulter logs: `sudo docker-compose logs -f`
4. Modifier code dans `backend/`
5. Rebuild: `sudo docker-compose build service-name`
6. Redeploy: `sudo docker-compose up -d service-name`

## Prochaines Étapes

### Optionnel: Ajouter plus de documents

```bash
# Via interface admin
firefox http://localhost:8502
# Section Upload > Choisir PDFs > Upload

# Ou via script batch
for file in /path/to/pdfs/*.pdf; do
  curl -X POST http://localhost:8000/documents/upload \
    -F "file=@$file" \
    -F "collection_id=default"
  sleep 2
done
```

### Optionnel: Configurer authentification

Voir section Users dans admin panel (actuellement TODO)

### Optionnel: Monitoring avancé

Installer Prometheus + Grafana pour monitoring:
```bash
# À venir dans version 1.2.0
```

## Support

**Documentation:**
- README.md (présentation)
- RAPPORT_AMELIORATIONS.md (détails techniques)
- docs/ (Mintlify complète)

**Tests:**
- ./test-system.sh (vérification rapide)
- docs/tests/ (tests détaillés)

**Logs:**
```bash
sudo docker-compose logs -f
```

---

**Système opérationnel et prêt à l'emploi ✓**

Version: 1.1.0  
Date: 18 février 2026  
Status: Production Ready

**Bon travail avec OpenRAG !**

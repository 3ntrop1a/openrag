# 🚀 Guide de Démarrage d'OpenRAG

## ✅ Étapes complétées

1. ✅ Docker installé et configuré
2. ✅ Docker Compose installé
3. ✅ Projet OpenRAG créé
4. ✅ Configuration (.env) prête

## 🎯 Pour démarrer OpenRAG, 2 options :

### Option 1 : Script automatique (RECOMMANDÉ)

```bash
cd /home/adminrag/openrag
sudo bash scripts/start-manual.sh
```

Ce script va :
- Vérifier Docker
- Télécharger toutes les images
- Démarrer tous les services dans le bon ordre
- Vérifier que tout fonctionne

**Durée estimée : 5-10 minutes** (téléchargement des images)

---

### Option 2 : Commandes manuelles

Si vous préférez contrôler chaque étape :

#### 1. Démarrer Docker
```bash
sudo systemctl start docker
sudo systemctl status docker
```

#### 2. Télécharger les images Docker
```bash
cd /home/adminrag/openrag
sudo docker-compose pull
```

#### 3. Démarrer l'infrastructure
```bash
sudo docker-compose up -d postgres redis minio qdrant
```

#### 4. Attendre 30 secondes puis démarrer Ollama
```bash
sleep 30
sudo docker-compose up -d ollama
```

#### 5. Démarrer les services applicatifs
```bash
sleep 10
sudo docker-compose up -d embedding-service orchestrator api
```

#### 6. Vérifier le statut
```bash
sudo docker-compose ps
```

---

## 📊 Vérification

Une fois démarré, testez :

```bash
# Test de santé de l'API
curl http://localhost:8000/health

# Documentation interactive
firefox http://localhost:8000/docs &
# ou
google-chrome http://localhost:8000/docs &
```

---

## 🤖 Configuration du LLM (importante !)

Par défaut, Ollama est configuré mais **vous devez télécharger un modèle** :

```bash
# Télécharger le modèle llama3.1:8b (~4.7GB)
sudo docker exec -it openrag-ollama ollama pull llama3.1:8b

# Vérifier les modèles installés
sudo docker exec -it openrag-ollama ollama list
```

**Alternatives de modèles :**
- `phi3:mini` - Léger (~2.3GB), rapide
- `gemma:7b` - Bon équilibre (~4.8GB)
- `mistral:7b` - Excellent en français (~4.1GB)

Pour changer de modèle, éditez `.env` :
```bash
nano .env
# Modifiez la ligne LLM_MODEL=llama3.1:8b
```

---

## 🎯 Premier test complet

### 1. Créer un document de test

```bash
cd /home/adminrag/openrag
cat > test_document.txt << 'EOF'
OpenRAG est un système RAG (Retrieval-Augmented Generation) open-source.
Il permet d'interroger vos documents en utilisant des modèles de langage avancés.

Fonctionnalités principales :
- Upload de documents (PDF, DOCX, TXT, MD)
- Recherche sémantique vectorielle avec Qdrant
- Génération de réponses avec Ollama, OpenAI ou Anthropic
- Architecture microservices scalable

Pour commencer, uploadez vos documents et posez des questions en langage naturel.
EOF
```

### 2. Uploader le document

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test_document.txt" \
  -F "collection_id=test"
```

Vous devriez recevoir une réponse avec un `document_id`.

### 3. Attendre le traitement

Le document doit être traité (chunking + embedding + indexation).
Attendez environ **15-20 secondes**.

Vérifiez le statut :
```bash
curl http://localhost:8000/documents | jq '.documents[] | {filename, status}'
```

Attendez que le status soit `"processed"`.

### 4. Poser une question

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quelles sont les fonctionnalités principales d'\''OpenRAG ?",
    "max_results": 3,
    "use_llm": true
  }' | jq '.'
```

Vous devriez recevoir une réponse avec :
- `answer` : La réponse générée par le LLM
- `sources` : Les documents sources utilisés
- `execution_time_ms` : Temps de traitement

---

## 🌐 Interfaces web disponibles

Une fois démarré, vous pouvez accéder à :

| Service | URL | Identifiants |
|---------|-----|--------------|
| **API Swagger** | http://localhost:8000/docs | Aucun |
| **MinIO Console** | http://localhost:9001 | admin / admin123456 |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Aucun |

---

## 🛠️ Commandes utiles

```bash
# Voir les logs en temps réel
sudo docker-compose logs -f

# Logs d'un service spécifique
sudo docker-compose logs -f api
sudo docker-compose logs -f orchestrator

# Status de tous les services
sudo docker-compose ps

# Redémarrer tous les services
sudo docker-compose restart

# Redémarrer un service spécifique
sudo docker-compose restart api

# Arrêter tous les services
sudo docker-compose down

# Arrêter ET supprimer toutes les données (⚠️ ATTENTION)
sudo docker-compose down -v
```

---

## 🐛 Dépannage

### Les services ne démarrent pas

```bash
# Vérifier les logs
sudo docker-compose logs

# Redémarrer Docker
sudo systemctl restart docker
sudo docker-compose down
sudo docker-compose up -d
```

### L'API ne répond pas

```bash
# Attendre 1-2 minutes après le démarrage
# Vérifier les logs de l'API
sudo docker-compose logs api

# Redémarrer l'API
sudo docker-compose restart api
```

### Ollama ne trouve pas le modèle

```bash
# Vérifier les modèles installés
sudo docker exec -it openrag-ollama ollama list

# Télécharger le modèle
sudo docker exec -it openrag-ollama ollama pull llama3.1:8b
```

### Pas de résultats pour les requêtes

```bash
# Vérifier que les documents sont traités
curl http://localhost:8000/documents | jq '.documents[] | select(.status == "processed")'

# Vérifier Qdrant
curl http://localhost:6333/collections/documents_embeddings
```

---

## 📚 Documentation complète

Pour plus de détails, consultez :

```bash
cd /home/adminrag/openrag
cat GUIDE_COMPLET.md
cat QUICKSTART.md
cat README.md
```

Ou lancez la documentation Mintlify :

```bash
cd docs
npx mintlify dev
# Puis visitez http://localhost:3000
```

---

## 🆘 Besoin d'aide ?

1. Consultez les logs : `sudo docker-compose logs -f`
2. Vérifiez GUIDE_COMPLET.md pour plus de détails
3. Testez la santé : `curl http://localhost:8000/health`

---

## ✨ Félicitations !

Vous êtes maintenant prêt à utiliser OpenRAG ! 🎉

**Prochaines étapes recommandées :**

1. ⬇️  Télécharger le modèle LLM (si pas encore fait)
2. 📄 Uploader vos vrais documents
3. 🔍 Tester des requêtes
4. 📊 Explorer les interfaces web
5. 📚 Lire la documentation complète

Bon développement avec OpenRAG ! 🚀

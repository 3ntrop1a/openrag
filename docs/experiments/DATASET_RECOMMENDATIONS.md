# Dataset Recommendations for OpenRAG Testing

## Objectif
Tester OpenRAG avec un corpus conséquent (500-1000+ documents) sur un domaine bien documenté pour valider les performances du système RAG.

---

## Datasets Recommandés

### 1. 🥇 Wikipedia FR - Sciences (RECOMMANDÉ)
**Source**: Dumps Wikipedia en français  
**URL**: https://dumps.wikimedia.org/frwiki/

**Avantages**:
- ✅ Corpus massif (100K+ articles scientifiques)
- ✅ Contenu structuré et vérifié
- ✅ Domaine varié: physique, chimie, biologie, informatique
- ✅ Format exploitable (XML/JSON)
- ✅ Gratuit et open-source
- ✅ Français natif de qualité

**Inconvénients**:
- ⚠️ Très volumineux (plusieurs GB compressés)
- ⚠️ Nécessite parsing XML
- ⚠️ Mélange de qualité variable

**Taille**: 
- Full dump: ~20GB (compressé)
- Articles scientifiques: ~2-5GB
- Subset 1000 articles: ~50-100MB

**Format**: XML (MediaWiki format)

---

### 2. 🥈 arXiv - Computer Science Papers
**Source**: arXiv.org API  
**URL**: https://arxiv.org/help/api/

**Avantages**:
- ✅ Papers scientifiques de qualité (peer-reviewed)
- ✅ Métadonnées riches (auteurs, catégories, dates)
- ✅ API facile d'accès
- ✅ Abstracts en anglais (teste le modèle multilingue)
- ✅ PDFs disponibles
- ✅ Gratuit

**Inconvénients**:
- ❌ Principalement en anglais
- ⚠️ API rate-limited (3s entre requêtes)
- ⚠️ PDFs lourds

**Taille**:
- 2M+ papers disponibles
- Computer Science: ~500K papers
- Subset 1000 papers: ~1GB (PDFs) ou ~10MB (abstracts seulement)

**Format**: XML/JSON via API, PDFs

---

### 3. 🥉 HAL - Publications Scientifiques FR
**Source**: HAL (Archive ouverte française)  
**URL**: https://hal.science/

**Avantages**:
- ✅ Contenu français +++
- ✅ Recherche française de qualité
- ✅ API OAI-PMH disponible
- ✅ Métadonnées riches
- ✅ Multidisciplinaire
- ✅ PDFs open-access

**Inconvénients**:
- ⚠️ API complexe (OAI-PMH)
- ⚠️ Qualité variable (prépublications)
- ⚠️ Moins volumineux que Wikipedia

**Taille**:
- 1M+ documents
- Subset 1000 docs: ~500MB-1GB

**Format**: XML (OAI-PMH), PDFs

---

### 4. PubMed - Abstracts Médicaux
**Source**: PubMed Central (NIH)  
**URL**: https://pubmed.ncbi.nlm.nih.gov/

**Avantages**:
- ✅ 35M+ abstracts médicaux
- ✅ API gratuite et simple (E-utilities)
- ✅ Métadonnées structurées (MeSH terms)
- ✅ Contenu vérifié et cité
- ✅ Format XML propre

**Inconvénients**:
- ❌ Anglais uniquement
- ⚠️ Domaine très spécialisé (médecine)
- ⚠️ API rate-limited

**Taille**:
- 35M+ abstracts
- Subset 1000 abstracts: ~5MB

**Format**: XML, JSON via API

---

### 5. Project Gutenberg - Littérature Classique
**Source**: Project Gutenberg  
**URL**: https://www.gutenberg.org/

**Avantages**:
- ✅ 70K+ livres libres de droits
- ✅ Français disponible (~3K livres)
- ✅ Texte brut facile à parser
- ✅ Contenu narratif (teste compréhension contextuelle)
- ✅ Gratuit

**Inconvénients**:
- ⚠️ Pas scientifique (littérature)
- ⚠️ Français limité (3K livres)
- ⚠️ Ancien français parfois difficile

**Taille**:
- Livres FR: ~3K
- Subset 100 livres: ~50MB

**Format**: TXT, HTML, EPUB

---

## 💡 Recommandation pour Soutenance

### Option 1: Wikipedia FR Sciences (1000 articles)
**Meilleur choix pour démonstration équilibrée**

```bash
# Télécharger subset Wikipedia Sciences (préparé)
wget https://dumps.wikimedia.org/frwiki/latest/frwiki-latest-pages-articles.xml.bz2

# Ou utiliser script de parsing (à créer)
python scripts/download_wikipedia_fr.py --category "Sciences" --limit 1000
```

**Avantages pour soutenance**:
- ✅ Contenu français → montre gestion multilingue
- ✅ Domaine scientifique → relevant pour RAG technique
- ✅ 1000 articles = ~50-100MB → raisonnable à processer
- ✅ Diversité thématique → teste généralisation
- ✅ Questions variées possibles (physicien célèbre, théorie X, etc.)

**Temps de processing estimé**:
- 1000 articles × 2000 chars/chunk = ~5000-10000 chunks
- Embedding 768D: ~2-3h de processing
- Stockage Qdrant: ~500MB RAM

---

### Option 2: arXiv Computer Science (1000 abstracts)
**Bon choix pour domaine technique**

```bash
# Utiliser API arXiv
python scripts/download_arxiv.py --category "cs.AI" --limit 1000
```

**Avantages**:
- ✅ Domaine informatique/AI → pertinent pour projet RAG
- ✅ Abstracts courts → processing rapide
- ✅ Métadonnées riches → tests avancés
- ✅ Anglais → teste modèle multilingue

**Temps de processing**:
- 1000 abstracts × ~2000 chars = ~2000-3000 chunks
- Embedding: ~30-60 minutes
- Stockage: ~200MB RAM

---

## Scripts de Téléchargement

### Script 1: Wikipedia FR Sciences

```python
# scripts/datasets/download_wikipedia.py
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
import json

def download_wikipedia_fr_sciences(limit: int = 1000) -> List[Dict]:
    """
    Download French Wikipedia articles from Sciences category
    
    Args:
        limit: Number of articles to download
        
    Returns:
        List of articles with title, content, url
    """
    
    # Using Wikipedia API
    API_URL = "https://fr.wikipedia.org/w/api.php"
    
    articles = []
    
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": "Catégorie:Sciences",
        "cmlimit": limit,
        "cmnamespace": 0  # Main namespace only
    }
    
    response = requests.get(API_URL, params=params)
    members = response.json()["query"]["categorymembers"]
    
    for member in members[:limit]:
        # Get full article content
        content_params = {
            "action": "query",
            "format": "json",
            "titles": member["title"],
            "prop": "extracts",
            "explaintext": True
        }
        
        content_response = requests.get(API_URL, params=content_params)
        pages = content_response.json()["query"]["pages"]
        
        for page_id, page_data in pages.items():
            if "extract" in page_data:
                articles.append({
                    "title": page_data["title"],
                    "content": page_data["extract"],
                    "url": f"https://fr.wikipedia.org/wiki/{page_data['title'].replace(' ', '_')}",
                    "source": "wikipedia_fr"
                })
        
        if len(articles) >= limit:
            break
    
    return articles

if __name__ == "__main__":
    print("📥 Downloading Wikipedia FR Sciences articles...")
    articles = download_wikipedia_fr_sciences(limit=1000)
    
    # Save to JSON
    with open("/tmp/wikipedia_fr_sciences_1000.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Downloaded {len(articles)} articles")
    print(f"💾 Saved to /tmp/wikipedia_fr_sciences_1000.json")
```

---

### Script 2: arXiv Computer Science

```python
# scripts/datasets/download_arxiv.py
import arxiv
import time
from typing import List, Dict
import json

def download_arxiv_papers(category: str = "cs.AI", limit: int = 1000) -> List[Dict]:
    """
    Download arXiv papers from specific category
    
    Args:
        category: arXiv category (cs.AI, cs.CL, cs.LG, etc.)
        limit: Number of papers to download
        
    Returns:
        List of papers with title, abstract, authors, etc.
    """
    
    papers = []
    
    # Search query
    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=limit,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    for result in search.results():
        papers.append({
            "title": result.title,
            "content": result.summary,  # Abstract
            "authors": [author.name for author in result.authors],
            "url": result.entry_id,
            "published": result.published.isoformat(),
            "categories": result.categories,
            "source": "arxiv"
        })
        
        # Rate limiting
        time.sleep(0.1)
        
        if len(papers) % 100 == 0:
            print(f"📥 Downloaded {len(papers)}/{limit} papers...")
    
    return papers

if __name__ == "__main__":
    print("📥 Downloading arXiv Computer Science papers...")
    papers = download_arxiv_papers(category="cs.AI", limit=1000)
    
    # Save to JSON
    with open("/tmp/arxiv_cs_ai_1000.json", "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Downloaded {len(papers)} papers")
    print(f"💾 Saved to /tmp/arxiv_cs_ai_1000.json")
```

---

## Import dans OpenRAG

### Script d'Import Générique

```python
# scripts/datasets/import_to_openrag.py
import json
import requests
from pathlib import Path

def import_dataset_to_openrag(dataset_file: str, api_url: str = "http://localhost:8000"):
    """
    Import JSON dataset into OpenRAG
    
    Args:
        dataset_file: Path to JSON file with articles/papers
        api_url: OpenRAG API URL
    """
    
    with open(dataset_file, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    print(f"📚 Importing {len(documents)} documents into OpenRAG...")
    
    for i, doc in enumerate(documents):
        # Create text file
        filename = f"{doc['source']}_{i+1}_{doc['title'][:50].replace('/', '_')}.txt"
        content = f"Title: {doc['title']}\n\nContent:\n{doc['content']}\n\nSource: {doc['url']}"
        
        # Upload via API
        files = {"file": (filename, content.encode("utf-8"), "text/plain")}
        
        try:
            response = requests.post(f"{api_url}/upload", files=files)
            response.raise_for_status()
            
            if (i + 1) % 100 == 0:
                print(f"✅ Imported {i + 1}/{len(documents)} documents")
        
        except Exception as e:
            print(f"❌ Error importing {filename}: {e}")
    
    print(f"🎉 Import complete! {len(documents)} documents processed.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python import_to_openrag.py <dataset.json>")
        sys.exit(1)
    
    import_dataset_to_openrag(sys.argv[1])
```

---

## Commandes Rapides

### Wikipedia FR (1000 articles)
```bash
cd /home/adminrag/openrag

# Télécharger
python scripts/datasets/download_wikipedia.py

# Importer
python scripts/datasets/import_to_openrag.py /tmp/wikipedia_fr_sciences_1000.json

# Attendre processing (~2-3h)
docker-compose logs -f orchestrator

# Tester
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Qui a découvert la relativité générale?", "use_llm": true}'
```

### arXiv CS.AI (1000 papers)
```bash
# Installer dépendance
pip install arxiv

# Télécharger
python scripts/datasets/download_arxiv.py

# Importer
python scripts/datasets/import_to_openrag.py /tmp/arxiv_cs_ai_1000.json

# Tester
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main approaches to attention mechanisms in neural networks?", "use_llm": true}'
```

---

## Comparaison WTE vs Dataset Scientifique

| Métrique | WTE (actuel) | Wikipedia FR 1K | arXiv 1K |
|----------|--------------|----------------|----------|
| **Documents** | 33 | 1000 | 1000 |
| **Vecteurs** | 237 | 5000-10000 | 2000-3000 |
| **Taille** | ~35MB | ~100MB | ~10MB (abstracts) |
| **Langue** | FR | FR | EN |
| **Domaine** | Cisco/WTE | Sciences variées | Computer Science |
| **Processing** | 10 min | 2-3h | 30-60 min |
| **Qualité** | Technique | Encyclopédique | Académique |
| **Coverage** | ❌ Faible | ✅ Excellente | ✅ Bonne |

---

## Prochaines Étapes

1. ✅ Choisir dataset: **Wikipedia FR Sciences (1000 articles)** RECOMMANDÉ
2. ⏳ Créer scripts de téléchargement
3. ⏳ Télécharger dataset (~30 min)
4. ⏳ Importer dans OpenRAG (~1h)
5. ⏳ Attendre processing (~2-3h)
6. ⏳ Tester requêtes variées
7. ⏳ Comparer avec résultats WTE
8. ⏳ Documenter pour soutenance

**Temps total estimé**: ~4-5h (majoritairement automatisé)

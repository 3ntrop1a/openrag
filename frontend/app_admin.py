"""
Interface administrateur OpenRAG - Gestion du système
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict
import json

# Configuration
API_URL = "http://localhost:8000"
QDRANT_URL = "http://localhost:6333"

# Configuration de la page
st.set_page_config(
    page_title="OpenRAG - Administration",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #d32f2f;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 0.3rem;
        color: #155724;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 0.3rem;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Fonctions API
def get_api_health() -> Dict:
    """Vérifie la santé de l'API"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.json()
    except:
        return {"status": "unhealthy"}

def get_documents() -> List[Dict]:
    """Récupère tous les documents"""
    try:
        response = requests.get(f"{API_URL}/documents", timeout=10)
        response.raise_for_status()
        return response.json().get('documents', [])
    except:
        return []

def get_qdrant_collections() -> List[Dict]:
    """Récupère les collections Qdrant"""
    try:
        response = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        response.raise_for_status()
        collections = response.json().get('result', {}).get('collections', [])
        
        # Récupérer les détails de chaque collection
        detailed_collections = []
        for col in collections:
            try:
                detail_response = requests.get(f"{QDRANT_URL}/collections/{col['name']}", timeout=5)
                if detail_response.status_code == 200:
                    detailed_collections.append(detail_response.json().get('result', {}))
            except:
                pass
        
        return detailed_collections
    except:
        return []

def upload_document(file, collection_id: str, metadata: Dict) -> Dict:
    """Upload un document"""
    try:
        files = {'file': file}
        data = {
            'collection_id': collection_id,
            'metadata': json.dumps(metadata)
        }
        response = requests.post(f"{API_URL}/documents/upload", files=files, data=data, timeout=300)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Header
st.markdown('<div class="main-header">⚙️ OpenRAG - Panneau d\'Administration</div>', unsafe_allow_html=True)

# Sidebar - Navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Section",
        ["📊 Dashboard", "📁 Documents", "🗂️ Collections", "📤 Upload", "👥 Utilisateurs (TODO)", "🔧 Configuration"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Statut système
    st.subheader("Statut Système")
    health = get_api_health()
    
    if health.get('status') == 'healthy':
        st.success("✅ API Online")
    else:
        st.error("❌ API Offline")
    
    st.caption("OpenRAG Admin v1.0.0")

# PAGE: Dashboard
if page == "📊 Dashboard":
    st.header("📊 Vue d'ensemble du système")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    docs = get_documents()
    collections = get_qdrant_collections()
    
    wte_docs = [d for d in docs if any(x in d.get('filename', '').lower() for x in ['wte', 'cisco', 'contrat'])]
    processed_docs = [d for d in docs if d.get('status') == 'processed']
    
    total_vectors = sum([col.get('points_count', 0) for col in collections])
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(docs)}</div>
            <div class="stat-label">Documents Total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(processed_docs)}</div>
            <div class="stat-label">Traités</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{total_vectors}</div>
            <div class="stat-label">Vecteurs Indexés</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(collections)}</div>
            <div class="stat-label">Collections</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Documents par statut")
        if docs:
            status_counts = {}
            for doc in docs:
                status = doc.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            df_status = pd.DataFrame(list(status_counts.items()), columns=['Statut', 'Nombre'])
            st.bar_chart(df_status.set_index('Statut'))
        else:
            st.info("Aucun document")
    
    with col2:
        st.subheader("💾 Collections Qdrant")
        if collections:
            df_collections = pd.DataFrame([
                {
                    'Collection': col.get('name', 'N/A'),
                    'Vecteurs': col.get('points_count', 0),
                    'Statut': col.get('status', 'unknown')
                }
                for col in collections
            ])
            st.dataframe(df_collections, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune collection")
    
    # Documents récents
    st.divider()
    st.subheader("📄 Documents récents")
    
    if docs:
        recent_docs = sorted(docs, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
        df_recent = pd.DataFrame([
            {
                'Fichier': doc.get('filename', 'N/A'),
                'Statut': doc.get('status', 'unknown'),
                'Taille': f"{doc.get('size', 0) / 1024:.1f} KB" if doc.get('size') else 'N/A',
                'Date': doc.get('created_at', 'N/A')[:10] if doc.get('created_at') else 'N/A'
            }
            for doc in recent_docs
        ])
        st.dataframe(df_recent, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun document")

# PAGE: Documents
elif page == "📁 Documents":
    st.header("📁 Gestion des documents")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Rechercher", placeholder="Nom de fichier...")
    
    with col2:
        status_filter = st.selectbox("Statut", ["Tous", "processed", "pending", "failed", "uploaded"])
    
    with col3:
        sort_by = st.selectbox("Trier par", ["Date (récent)", "Date (ancien)", "Nom", "Taille"])
    
    # Liste des documents
    docs = get_documents()
    
    # Filtrage
    if search_term:
        docs = [d for d in docs if search_term.lower() in d.get('filename', '').lower()]
    
    if status_filter != "Tous":
        docs = [d for d in docs if d.get('status') == status_filter]
    
    # Tri
    if sort_by == "Date (récent)":
        docs = sorted(docs, key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_by == "Date (ancien)":
        docs = sorted(docs, key=lambda x: x.get('created_at', ''))
    elif sort_by == "Nom":
        docs = sorted(docs, key=lambda x: x.get('filename', ''))
    elif sort_by == "Taille":
        docs = sorted(docs, key=lambda x: x.get('size', 0), reverse=True)
    
    st.info(f"📊 {len(docs)} document(s) affiché(s)")
    
    # Affichage des documents
    if docs:
        for doc in docs:
            with st.expander(f"📄 {doc.get('filename', 'N/A')} - {doc.get('status', 'unknown')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**ID:** {doc.get('id', 'N/A')}")
                    st.write(f"**Statut:** {doc.get('status', 'unknown')}")
                
                with col2:
                    size_kb = doc.get('size', 0) / 1024 if doc.get('size') else 0
                    st.write(f"**Taille:** {size_kb:.1f} KB")
                    st.write(f"**Type:** {doc.get('file_type', 'N/A')}")
                
                with col3:
                    st.write(f"**Créé:** {doc.get('created_at', 'N/A')[:19] if doc.get('created_at') else 'N/A'}")
                    st.write(f"**Collection:** {doc.get('collection_id', 'N/A')}")
                
                if doc.get('metadata'):
                    st.json(doc['metadata'])
    else:
        st.warning("Aucun document trouvé")

# PAGE: Collections
elif page == "🗂️ Collections":
    st.header("🗂️ Gestion des collections Qdrant")
    
    collections = get_qdrant_collections()
    
    if collections:
        for col in collections:
            with st.container():
                st.subheader(f"📦 {col.get('name', 'N/A')}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Vecteurs", col.get('points_count', 0))
                
                with col2:
                    st.metric("Dimension", col.get('config', {}).get('params', {}).get('vectors', {}).get('size', 'N/A'))
                
                with col3:
                    status = col.get('status', 'unknown')
                    status_color = "🟢" if status == "green" else "🔴"
                    st.metric("Statut", f"{status_color} {status}")
                
                with col4:
                    distance = col.get('config', {}).get('params', {}).get('vectors', {}).get('distance', 'N/A')
                    st.metric("Distance", distance)
                
                with st.expander("Détails de la configuration"):
                    st.json(col.get('config', {}))
                
                st.divider()
    else:
        st.warning("Aucune collection trouvée")

# PAGE: Upload
elif page == "📤 Upload":
    st.header("📤 Upload de documents")
    
    st.info("💡 Formats supportés: PDF, TXT, DOCX, MD")
    
    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "Choisir un fichier",
            type=['pdf', 'txt', 'docx', 'md'],
            help="Sélectionnez un document à indexer"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            collection_id = st.text_input(
                "Collection ID",
                value="default",
                help="Nom de la collection Qdrant"
            )
        
        with col2:
            category = st.selectbox(
                "Catégorie",
                ["documentation", "tutorial", "guide", "contract", "manual"]
            )
        
        metadata_source = st.text_input("Source", value="WTE Orange")
        metadata_author = st.text_input("Auteur (optionnel)")
        
        submit = st.form_submit_button("🚀 Uploader et indexer", use_container_width=True)
        
        if submit and uploaded_file:
            metadata = {
                "source": metadata_source,
                "category": category
            }
            if metadata_author:
                metadata["author"] = metadata_author
            
            with st.spinner(f"📤 Upload de {uploaded_file.name} en cours..."):
                result = upload_document(uploaded_file, collection_id, metadata)
            
            if "error" in result:
                st.error(f"❌ Erreur: {result['error']}")
            else:
                st.success(f"✅ Document uploadé avec succès!")
                st.json(result)

# PAGE: Utilisateurs
elif page == "👥 Utilisateurs (TODO)":
    st.header("👥 Gestion des utilisateurs")
    
    st.info("🚧 Cette fonctionnalité sera implémentée prochainement")
    
    st.markdown("""
    ### Fonctionnalités prévues:
    
    - Création et gestion des comptes utilisateurs
    - Attribution des rôles et permissions
    - Gestion des quotas d'utilisation
    - Historique des requêtes par utilisateur
    - Tableau de bord par utilisateur
    - Authentification et sécurité
    """)
    
    # Preview de la structure
    st.subheader("Aperçu de la structure utilisateur")
    
    sample_users = pd.DataFrame([
        {"ID": "user001", "Nom": "Jean Dupont", "Email": "jean.dupont@example.com", "Rôle": "admin", "Statut": "actif"},
        {"ID": "user002", "Nom": "Marie Martin", "Email": "marie.martin@example.com", "Rôle": "user", "Statut": "actif"},
        {"ID": "user003", "Nom": "Pierre Durand", "Email": "pierre.durand@example.com", "Rôle": "user", "Statut": "inactif"},
    ])
    
    st.dataframe(sample_users, use_container_width=True, hide_index=True)

# PAGE: Configuration
elif page == "🔧 Configuration":
    st.header("🔧 Configuration du système")
    
    tabs = st.tabs(["API", "LLM", "Embedding", "Qdrant", "Base de données"])
    
    with tabs[0]:
        st.subheader("API Configuration")
        health = get_api_health()
        
        st.json(health)
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("API URL", value=API_URL, disabled=True)
        with col2:
            st.text_input("Version", value=health.get('version', 'N/A'), disabled=True)
    
    with tabs[1]:
        st.subheader("LLM Configuration")
        
        st.text_input("Provider", value="ollama", help="ollama, openai, anthropic")
        st.text_input("Model", value="llama3.1:8b")
        st.slider("Temperature", 0.0, 1.0, 0.3, help="Créativité du modèle")
        st.number_input("Max Tokens", value=4096, help="Longueur maximale de la réponse")
    
    with tabs[2]:
        st.subheader("Embedding Configuration")
        
        st.text_input("Model", value="all-MiniLM-L6-v2", disabled=True)
        st.number_input("Dimension", value=384, disabled=True)
    
    with tabs[3]:
        st.subheader("Qdrant Configuration")
        
        st.text_input("Qdrant URL", value=QDRANT_URL, disabled=True)
        
        collections = get_qdrant_collections()
        st.metric("Collections actives", len(collections))
        
        total_vectors = sum([col.get('points_count', 0) for col in collections])
        st.metric("Vecteurs totaux", total_vectors)
    
    with tabs[4]:
        st.subheader("PostgreSQL Configuration")
        
        st.text_input("Host", value="postgres", disabled=True)
        st.text_input("Port", value="5432", disabled=True)
        st.text_input("Database", value="openrag_db", disabled=True)

# Footer
st.divider()
st.caption("OpenRAG Administration Panel v1.0.0")

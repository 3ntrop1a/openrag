"""
Interface utilisateur OpenRAG - Chat avec la base documentaire
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict

# Configuration
API_URL = "http://localhost:8000"

# Configuration de la page
st.set_page_config(
    page_title="OpenRAG - Assistant Documentation",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .source-box {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialisation du state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'collection_id' not in st.session_state:
    st.session_state.collection_id = "default"

def query_api(question: str, collection_id: str, max_results: int = 5, use_llm: bool = True) -> Dict:
    """Interroge l'API OpenRAG"""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={
                "query": question,
                "collection_id": collection_id,
                "max_results": max_results,
                "use_llm": use_llm
            },
            timeout=180
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API: {str(e)}")
        return None

def get_documents() -> List[Dict]:
    """Récupère la liste des documents"""
    try:
        response = requests.get(f"{API_URL}/documents", timeout=10)
        response.raise_for_status()
        return response.json().get('documents', [])
    except:
        return []

def format_source(source: Dict) -> str:
    """Formate une source pour l'affichage"""
    score_percent = int(source.get('relevance_score', 0) * 100)
    return f"📄 {source.get('filename', 'N/A')} (pertinence: {score_percent}%)"

# Header
st.markdown('<div class="main-header">📚 OpenRAG - Assistant Documentation WTE/Cisco</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Collection selection
    st.session_state.collection_id = st.text_input(
        "Collection",
        value=st.session_state.collection_id,
        help="Nom de la collection à interroger"
    )
    
    # Paramètres de recherche
    max_results = st.slider(
        "Nombre de résultats",
        min_value=1,
        max_value=10,
        value=5,
        help="Nombre maximum de documents à utiliser pour la réponse"
    )
    
    use_llm = st.checkbox(
        "Utiliser l'IA pour générer la réponse",
        value=True,
        help="Si désactivé, seules les sources seront affichées"
    )
    
    st.divider()
    
    # Statistiques
    st.header("📊 Statistiques")
    docs = get_documents()
    
    if docs:
        wte_docs = [d for d in docs if any(x in d.get('filename', '').lower() for x in ['wte', 'cisco', 'contrat'])]
        processed = [d for d in wte_docs if d.get('status') == 'processed']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents WTE", len(wte_docs))
        with col2:
            st.metric("Traités", len(processed))
    
    st.divider()
    
    # Actions
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.messages = []
        st.rerun()
    
    # Informations
    st.caption("OpenRAG v1.0.0")
    st.caption("Plateforme RAG pour documentation technique")

# Zone de chat principale
chat_container = st.container()

with chat_container:
    # Affichage de l'historique des messages
    for message in st.session_state.messages:
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 Vous</strong>
                <p>{message['content']}</p>
                <small>{message['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant</strong>
                <p>{message['content']}</p>
            """, unsafe_allow_html=True)
            
            # Affichage des sources
            if 'sources' in message and message['sources']:
                st.markdown('<div class="source-box">', unsafe_allow_html=True)
                st.markdown("**Sources consultées:**")
                for source in message['sources'][:5]:
                    st.markdown(f"- {format_source(source)}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if 'execution_time' in message:
                st.caption(f"⏱️ Temps de réponse: {message['execution_time']/1000:.1f}s | {message['timestamp']}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# Zone de saisie
st.divider()

# Exemples de questions
with st.expander("💡 Exemples de questions"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Configuration:**
        - Comment configurer un standard automatique ?
        - Comment créer des groupements d'utilisateurs ?
        - Comment gérer les files d'attente ?
        - Comment intégrer MS Teams avec Webex ?
        """)
    with col2:
        st.markdown("""
        **Matériel:**
        - Quels sont les postes Cisco disponibles ?
        - Comment configurer le poste Cisco 6871 ?
        - Comment utiliser le téléphone de conférence 8832 ?
        - Comment configurer la messagerie vocale ?
        """)

# Formulaire de question
with st.form(key='question_form', clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    
    with col1:
        question = st.text_input(
            "Posez votre question:",
            placeholder="Ex: Comment configurer un standard automatique dans WTE ?",
            label_visibility="collapsed"
        )
    
    with col2:
        submit = st.form_submit_button("🚀 Envoyer", use_container_width=True)

# Traitement de la question
if submit and question:
    # Ajout de la question à l'historique
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        'role': 'user',
        'content': question,
        'timestamp': timestamp
    })
    
    # Affichage du spinner
    with st.spinner('🔍 Recherche en cours...'):
        result = query_api(question, st.session_state.collection_id, max_results, use_llm)
    
    if result:
        # Ajout de la réponse à l'historique
        if use_llm and result.get('answer'):
            answer_content = result['answer']
        else:
            answer_content = "Voici les documents pertinents trouvés:"
        
        st.session_state.messages.append({
            'role': 'assistant',
            'content': answer_content,
            'sources': result.get('sources', []),
            'execution_time': result.get('execution_time_ms', 0),
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
        # Rafraîchir l'affichage
        st.rerun()

# Footer
st.divider()
st.caption("Propulsé par OpenRAG - Système de Retrieval-Augmented Generation")

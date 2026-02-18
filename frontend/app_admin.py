"""
OpenRAG Admin Interface - System Management
"""

import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict
import json

# Configuration - use environment variable or fallback to Docker service name
API_URL = os.getenv("API_URL", "http://api:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

# Page configuration
st.set_page_config(
    page_title="OpenRAG - Admin Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern black & white CSS - NextJS inspired
st.markdown("""
<style>
    /* Global styles */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Header */
    .app-header {
        background: linear-gradient(135deg, #1a1a1a 0%, #000000 100%);
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #2a2a2a;
        margin-bottom: 2rem;
    }
    
    .app-title {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        color: #ffffff;
    }
    
    .app-subtitle {
        font-size: 0.9rem;
        color: #888888;
        margin-top: 0.5rem;
    }
    
    /* Stats cards */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 1.5rem;
        transition: all 0.2s ease;
    }
    
    .stat-card:hover {
        border-color: #ffffff;
        transform: translateY(-2px);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1;
    }
    
    .stat-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #666666;
        margin-top: 0.5rem;
    }
    
    .stat-change {
        font-size: 0.875rem;
        color: #888888;
        margin-top: 0.25rem;
    }
    
    /* Tables */
    .dataframe {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
    }
    
    .dataframe th {
        background: #0a0a0a;
        color: #888888;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.1em;
        padding: 1rem;
        border-bottom: 1px solid #2a2a2a;
    }
    
    .dataframe td {
        padding: 1rem;
        border-bottom: 1px solid #1a1a1a;
        color: #ffffff;
    }
    
    /* Buttons */
    .stButton > button {
        background: #ffffff;
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #e0e0e0;
        transform: translateY(-1px);
    }
    
    /* File uploader */
    .stFileUploader {
        background: #1a1a1a;
        border: 2px dashed #2a2a2a;
        border-radius: 8px;
        padding: 2rem;
    }
    
    .stFileUploader:hover {
        border-color: #ffffff;
    }
    
    /* Alerts */
    .stSuccess {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-left: 3px solid #ffffff;
        color: #ffffff;
    }
    
    .stError {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-left: 3px solid #666666;
        color: #ffffff;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #ffffff;
        box-shadow: 0 0 0 1px #ffffff;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        color: #ffffff;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #ffffff;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #2a2a2a;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: #1a1a1a;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2a2a2a;
    }
    
    .stRadio label {
        color: #ffffff;
        padding: 0.5rem;
    }
    
    /* Divider */
    hr {
        border-color: #2a2a2a;
        margin: 2rem 0;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-online {
        background: #1a1a1a;
        color: #ffffff;
        border: 1px solid #ffffff;
    }
    
    .status-offline {
        background: #1a1a1a;
        color: #666666;
        border: 1px solid #2a2a2a;
    }
</style>
""", unsafe_allow_html=True)

# API Functions
def get_api_health() -> Dict:
    """Check API health"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def get_documents() -> List[Dict]:
    """Retrieve all documents"""
    try:
        response = requests.get(f"{API_URL}/documents", timeout=10)
        response.raise_for_status()
        return response.json().get('documents', [])
    except Exception as e:
        st.error(f"Failed to fetch documents: {str(e)}")
        return []

def get_qdrant_collections() -> List[Dict]:
    """Retrieve Qdrant collections"""
    try:
        response = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        response.raise_for_status()
        collections = response.json().get('result', {}).get('collections', [])
        
        detailed_collections = []
        for col in collections:
            try:
                detail_response = requests.get(f"{QDRANT_URL}/collections/{col['name']}", timeout=5)
                if detail_response.status_code == 200:
                    detailed_collections.append(detail_response.json().get('result', {}))
            except:
                pass
        
        return detailed_collections
    except Exception as e:
        st.error(f"Failed to fetch collections: {str(e)}")
        return []

def upload_document(file, collection_id: str, metadata: Dict) -> Dict:
    """Upload a document"""
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

def delete_document(doc_id: str) -> bool:
    """Delete a document"""
    try:
        response = requests.delete(f"{API_URL}/documents/{doc_id}", timeout=10)
        response.raise_for_status()
        return True
    except:
        return False

# Header
st.markdown('''
<div class="app-header">
    <h1 class="app-title">⚙️ OpenRAG Admin Dashboard</h1>
    <p class="app-subtitle">System Management & Monitoring</p>
</div>
''', unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio(
        "Select Page",
        ["📊 Dashboard", "📁 Documents", "🗂️ Collections", "📤 Upload"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # System Status
    st.markdown("### System Status")
    health = get_api_health()
    
    if health.get('status') == 'healthy':
        st.markdown('<span class="status-badge status-online">● API Online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-offline">● API Offline</span>', unsafe_allow_html=True)
    
    st.divider()
    st.caption(f"API: {API_URL}")
    st.caption("OpenRAG Admin v1.1.0")

# PAGE: Dashboard
if page == "📊 Dashboard":
    st.markdown("### System Overview")
    
    # Fetch data
    docs = get_documents()
    collections = get_qdrant_collections()
    
    processed_docs = [d for d in docs if d.get('status') == 'processed']
    processing_docs = [d for d in docs if d.get('status') == 'processing']
    total_vectors = sum([col.get('points_count', 0) for col in collections])
    
    # Stats cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(docs)}</div>
            <div class="stat-label">Total Documents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(processed_docs)}</div>
            <div class="stat-label">Processed</div>
            <div class="stat-change">{len(processing_docs) in processing</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{total_vectors}</div>
            <div class="stat-label">Vectors Indexed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(collections)}</div>
            <div class="stat-label">Collections</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Collections table
    if collections:
        st.markdown("### Collections")
        collections_data = []
        for col in collections:
            collections_data.append({
                "Name": col.get('name', 'N/A'),
                "Vectors": col.get('points_count', 0),
                "Dimensions": col.get('config', {}).get('params', {}).get('vectors', {}).get('size', 'N/A'),
                "Status": col.get('status', 'N/A')
            })
        
        df = pd.DataFrame(collections_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Recent documents
    if docs:
        st.markdown("### Recent Documents")
        recent_docs = sorted(docs, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
        docs_data = []
        for doc in recent_docs:
            docs_data.append({
                "Filename": doc.get('filename', 'N/A'),
                "Status": doc.get('status', 'N/A'),
                "Collection": doc.get('collection_id', 'default'),
                "Size": f"{doc.get('file_size', 0) / 1024:.1f} KB" if doc.get('file_size') else 'N/A',
                "Created": doc.get('created_at', 'N/A')[:19] if doc.get('created_at') else 'N/A'
            })
        
        df = pd.DataFrame(docs_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

# PAGE: Documents
elif page == "📁 Documents":
    st.markdown("### Document Management")
    
    docs = get_documents()
    
    if not docs:
        st.info("No documents found. Upload some documents to get started.")
    else:
        # Search
        search = st.text_input("🔍 Search documents", placeholder="Search by filename...")
        
        # Filter
        filtered_docs = docs
        if search:
            filtered_docs = [d for d in docs if search.lower() in d.get('filename', '').lower()]
        
        # Documents table
        docs_data = []
        for doc in filtered_docs:
            docs_data.append({
                "ID": doc.get('id', 'N/A')[:8],
                "Filename": doc.get('filename', 'N/A'),
                "Status": doc.get('status', 'N/A'),
                "Collection": doc.get('collection_id', 'default'),
                "Chunks": doc.get('chunks_count', 0),
                "Size": f"{doc.get('file_size', 0) / 1024:.1f} KB" if doc.get('file_size') else 'N/A',
                "Created": doc.get('created_at', 'N/A')[:19] if doc.get('created_at') else 'N/A'
            })
        
        df = pd.DataFrame(docs_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.caption(f"Showing {len(filtered_docs)} of {len(docs)} documents")
        
        # Delete document
        with st.expander("🗑️ Delete Document"):
            doc_id = st.text_input("Enter document ID to delete", placeholder="e.g., 12345678")
            if st.button("Delete", type="primary"):
                if doc_id:
                    if delete_document(doc_id):
                        st.success(f"✅ Document {doc_id} deleted successfully")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete document")

# PAGE: Collections
elif page == "🗂️ Collections":
    st.markdown("### Vector Collections")
    
    collections = get_qdrant_collections()
    
    if not collections:
        st.info("No collections found.")
    else:
        for col in collections:
            with st.expander(f"📦 {col.get('name', 'Unknown')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Vectors", col.get('points_count', 0))
                with col2:
                    st.metric("Dimensions", col.get('config', {}).get('params', {}).get('vectors', {}).get('size', 'N/A'))
                with col3:
                    st.metric("Status", col.get('status', 'N/A'))
                
                # Details
                st.json(col.get('config', {}))

# PAGE: Upload
elif page == "📤 Upload":
    st.markdown("### Upload Documents")
    
    with st.form("upload_form"):
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'docx', 'txt', 'md'],
            help="Supported formats: PDF, DOCX, TXT, Markdown"
        )
        
        # Collection
        collection_id = st.text_input(
            "Collection ID",
            value="default",
            help="Collection to store the document in"
        )
        
        # Metadata
        col1, col2 = st.columns(2)
        with col1:
            category = st.text_input("Category (optional)", placeholder="e.g., technical")
        with col2:
            source = st.text_input("Source (optional)", placeholder="e.g., documentation")
        
        # Submit
        submit = st.form_submit_button("📤 Upload Document", use_container_width=True)
        
        if submit and uploaded_file:
            metadata = {}
            if category:
                metadata['category'] = category
            if source:
                metadata['source'] = source
            
            with st.spinner("Uploading and processing document..."):
                result = upload_document(uploaded_file, collection_id, metadata)
            
            if 'error' in result:
                st.error(f"❌ Upload failed: {result['error']}")
            else:
                st.success(f"✅ Document uploaded successfully!")
                st.json(result)
                st.info("The document is being processed. Check the Dashboard for status.")

# Footer
st.divider()
st.caption("Powered by OpenRAG - Retrieval-Augmented Generation System")

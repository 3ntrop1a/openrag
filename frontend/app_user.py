"""
OpenRAG User Interface - Chat with Document Database
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime
from typing import List, Dict

# Configuration - use environment variable or fallback to Docker service name
API_URL = os.getenv("API_URL", "http://api:8000")

# Page configuration
st.set_page_config(
    page_title="OpenRAG - AI Document Assistant",
    page_icon="🤖",
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
        max-width: 1200px;
    }
    
    /* Header */
    .app-header {
        background: linear-gradient(135deg, #1a1a1a 0%, #000000 100%);
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #2a2a2a;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 0%, #999999 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .app-subtitle {
        font-size: 1rem;
        color: #888888;
        margin-top: 0.5rem;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #2a2a2a;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: #1a1a1a;
        border-left: 3px solid #ffffff;
        margin-left: 10%;
    }
    
    .assistant-message {
        background: #0a0a0a;
        border-left: 3px solid #666666;
        margin-right: 10%;
    }
    
    .message-role {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #666666;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .message-content {
        color: #ffffff;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    .message-time {
        font-size: 0.75rem;
        color: #666666;
        margin-top: 0.5rem;
    }
    
    /* Sources */
    .sources-container {
        margin-top: 1rem;
        padding: 1rem;
        background: #000000;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
    }
    
    .source-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #888888;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }
    
    .source-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid #1a1a1a;
        color: #cccccc;
        font-size: 0.9rem;
    }
    
    .source-item:last-child {
        border-bottom: none;
    }
    
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        background: #1a1a1a;
        border-radius: 4px;
        font-size: 0.75rem;
        color: #ffffff;
        margin-left: 0.5rem;
    }
    
    /* Input area */
    .stTextInput > div > div > input {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 1rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #ffffff;
        box-shadow: 0 0 0 1px #ffffff;
    }
    
    /* Buttons */
    .stButton > button {
        background: #ffffff;
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #e0e0e0;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255,255,255,0.1);
    }
    
    /* Sidebar */
    .css-1d391kg, .css-1v0mbdj {
        background-color: #0a0a0a;
    }
    
    .sidebar .sidebar-content {
        background-color: #0a0a0a;
    }
    
    /* Metrics */
    .metric-container {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #666666;
        margin-top: 0.25rem;
    }
    
    /* Divider */
    hr {
        border-color: #2a2a2a;
        margin: 2rem 0;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #ffffff;
    }
    
    /* Input container styling */
    .input-container {
        position: sticky;
        top: 0;
        background: #000000;
        padding: 1rem 0;
        z-index: 100;
        border-bottom: 1px solid #2a2a2a;
        margin-bottom: 1rem;
    }
    
    /* Chat container */
    .chat-history {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem 0;
    }
    
    /* Info box */
    .stAlert {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-left: 3px solid #ffffff;
        color: #ffffff;
    }
</style>

<script>
    // Auto-scroll to bottom of chat
    function scrollToBottom() {
        window.scrollTo(0, document.body.scrollHeight);
    }
    setTimeout(scrollToBottom, 100);
</script>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'collection_id' not in st.session_state:
    st.session_state.collection_id = "default"

def query_api(question: str, collection_id: str, max_results: int = 15, use_llm: bool = True) -> Dict:
    """Query the OpenRAG API"""
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
        st.error(f"⚠️ API Connection Error: {str(e)}")
        st.info(f"Attempting to connect to: {API_URL}")
        return None

def get_documents() -> List[Dict]:
    """Retrieve list of documents"""
    try:
        response = requests.get(f"{API_URL}/documents", timeout=10)
        response.raise_for_status()
        return response.json().get('documents', [])
    except:
        return []

def format_source(source: Dict) -> str:
    """Format a source for display"""
    score_percent = int(source.get('relevance_score', 0) * 100)
    filename = source.get('filename', 'Unknown')
    return f"""
    <div class="source-item">
        {filename}
        <span class="score-badge">{score_percent}%</span>
    </div>
    """

# Header
st.markdown('''
<div class="app-header">
    <h1 class="app-title">OpenRAG</h1>
    <p class="app-subtitle">AI-Powered Document Assistant</p>
</div>
''', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Collection selection
    st.session_state.collection_id = st.text_input(
        "Collection",
        value=st.session_state.collection_id,
        help="Collection to query"
    )
    
    # Search parameters
    max_results = st.slider(
        "Max Results",
        min_value=1,
        max_value=20,
        value=15,
        help="Maximum number of documents to retrieve"
    )
    
    use_llm = st.checkbox(
        "Use AI for Response Generation",
        value=True,
        help="If disabled, only source documents will be shown"
    )
    
    st.divider()
    
    # Statistics
    st.markdown("### 📊 Statistics")
    docs = get_documents()
    
    if docs:
        processed = [d for d in docs if d.get('status') == 'processed']
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'''
            <div class="metric-container">
                <div class="metric-value">{len(docs)}</div>
                <div class="metric-label">Total</div>
            </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="metric-container">
                <div class="metric-value">{len(processed)}</div>
                <div class="metric-label">Processed</div>
            </div>
            ''', unsafe_allow_html=True)
    
    st.divider()
    
    # Actions
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()
    
    st.caption("OpenRAG v1.1.0")

# Question input form (at top for better UX)
question_input = st.text_input(
    "💬 Ask your question:",
    placeholder="e.g., What are the main features of this system?",
    key="question_input"
)

col1, col2 = st.columns([1, 5])
with col1:
    send_button = st.button("🚀 Send", use_container_width=True, type="primary")
with col2:
    if st.session_state.messages:
        st.caption(f"💬 {len(st.session_state.messages)//2} messages in conversation")

st.divider()

# Process question BEFORE displaying chat
if send_button and question_input:
    # Add question to history
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        'role': 'user',
        'content': question_input,
        'timestamp': timestamp
    })
    
    # Display spinner and query API
    with st.spinner('🔍 Searching through documents...'):
        result = query_api(question_input, st.session_state.collection_id, max_results, use_llm)
    
    if result:
        # Add response to history
        if use_llm and result.get('answer'):
            answer_content = result['answer']
        elif use_llm:
            # LLM was requested but no answer generated
            answer_content = "⚠️ The AI model did not generate a response. This may be due to timeout or processing issues. Here are the relevant documents:"  
        else:
            answer_content = "Here are the relevant documents found:"
        
        st.session_state.messages.append({
            'role': 'assistant',
            'content': answer_content,
            'sources': result.get('sources', []),
            'execution_time': result.get('execution_time_ms', 0),
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
    
    # Rerun to refresh and clear input
    st.rerun()

# Chat history container
chat_container = st.container()

with chat_container:
    # Display all message history
    if not st.session_state.messages:
        st.info("👋 Welcome! Ask me anything about your documents.")
    else:
        for idx, message in enumerate(st.session_state.messages):
            if message['role'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div class="message-role">You</div>
                    <div class="message-content">{message['content']}</div>
                    <div class="message-time">{message['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                sources_html = ""
                if 'sources' in message and message['sources']:
                    sources_list = "".join([format_source(s) for s in message['sources'][:5]])
                    sources_html = f"""
                    <div class="sources-container">
                        <div class="source-title">Sources</div>
                        {sources_list}
                    </div>
                    """
                
                exec_time = ""
                if 'execution_time' in message:
                    exec_time = f"⏱️ {message['execution_time']/1000:.1f}s"
                
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div class="message-role">Assistant</div>
                    <div class="message-content">{message['content']}</div>
                    {sources_html}
                    <div class="message-time">{exec_time} • {message['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)

# Footer
st.divider()
st.caption("Powered by OpenRAG - Retrieval-Augmented Generation System")

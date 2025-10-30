import streamlit as st
import requests
import json
from typing import Dict, List, Optional
import os

# Configure page
st.set_page_config(
    page_title="Intelligent Document Chat",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/upload"
CHAT_ENDPOINT = f"{BACKEND_URL}/api/chat"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_id" not in st.session_state:
    st.session_state.document_id = None
if "document_stats" not in st.session_state:
    st.session_state.document_stats = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .upload-section {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stats-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
    }
    .chat-message {
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .source-card {
        background-color: #fff8e1;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 0.9em;
    }
    .rephrased-query {
        background-color: #e8f5e9;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-style: italic;
    }
    .followup-question {
        background-color: #fff3e0;
        padding: 8px 12px;
        border-radius: 5px;
        margin: 5px;
        display: inline-block;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

def upload_pdf(uploaded_file) -> Optional[Dict]:
    """Upload PDF to backend and return document stats."""
    try:
        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
        response = requests.post(UPLOAD_ENDPOINT, files=files, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return None

def send_chat_message(message: str, document_id: str, history: List[Dict]) -> Optional[Dict]:
    """Send chat message to backend and return response."""
    try:
        payload = {
            "message": message,
            "document_id": document_id,
            "history": history
        }
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Chat request failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return None

# Main app layout
st.title("📚 Intelligent Document Chat")
st.markdown("Upload a PDF document and chat with it using natural language queries powered by Gemini AI.")

# Sidebar for document upload
with st.sidebar:
    st.header("📄 Document Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF document to analyze and chat with"
    )
    
    if uploaded_file is not None:
        if st.button("🚀 Process Document", use_container_width=True):
            with st.spinner("Uploading and processing document..."):
                result = upload_pdf(uploaded_file)
                
                if result:
                    st.session_state.document_id = result.get("document_id")
                    st.session_state.document_stats = result
                    st.session_state.messages = []
                    st.session_state.chat_history = []
                    st.success("✅ Document processed successfully!")
                    st.rerun()
    
    # Display document stats
    if st.session_state.document_stats:
        st.markdown("---")
        st.subheader("📊 Document Statistics")
        
        stats = st.session_state.document_stats
        
        st.markdown(f"""
        <div class="stats-card">
            <strong>Document ID:</strong><br/>
            <code>{stats.get('document_id', 'N/A')}</code>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stats-card">
            <strong>Chunk Count:</strong><br/>
            <span style="font-size: 24px; color: #1f77b4;">{stats.get('chunk_count', 0)}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if "filename" in stats:
            st.markdown(f"""
            <div class="stats-card">
                <strong>Filename:</strong><br/>
                {stats.get('filename')}
            </div>
            """, unsafe_allow_html=True)
        
        if "page_count" in stats:
            st.markdown(f"""
            <div class="stats-card">
                <strong>Pages:</strong><br/>
                {stats.get('page_count')}
            </div>
            """, unsafe_allow_html=True)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()

# Main chat interface
if st.session_state.document_id:
    st.markdown("### 💬 Chat with Your Document")
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong><br/>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Assistant:</strong><br/>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # Display rephrased query if available
                if "rephrased_query" in message and message["rephrased_query"]:
                    st.markdown(f"""
                    <div class="rephrased-query">
                        <strong>🔄 Rephrased Query:</strong> {message['rephrased_query']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display sources
                if "sources" in message and message["sources"]:
                    with st.expander("📚 View Sources", expanded=False):
                        for idx, source in enumerate(message["sources"], 1):
                            st.markdown(f"""
                            <div class="source-card">
                                <strong>Source {idx}:</strong><br/>
                                {source.get('content', '')}<br/>
                                <small><em>Score: {source.get('score', 'N/A')}</em></small>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Display follow-up questions
                if "followup_questions" in message and message["followup_questions"]:
                    st.markdown("<strong>💡 Suggested Follow-up Questions:</strong>", unsafe_allow_html=True)
                    cols = st.columns(min(len(message["followup_questions"]), 3))
                    for idx, question in enumerate(message["followup_questions"]):
                        col_idx = idx % 3
                        with cols[col_idx]:
                            if st.button(question, key=f"followup_{len(st.session_state.messages)}_{idx}"):
                                # Trigger new query with follow-up question
                                st.session_state.temp_query = question
                                st.rerun()
    
    # Handle temporary query from follow-up button
    query_input = ""
    if hasattr(st.session_state, 'temp_query'):
        query_input = st.session_state.temp_query
        delattr(st.session_state, 'temp_query')
    
    # Chat input
    user_query = st.chat_input(
        "Ask a question about your document...",
        key="chat_input"
    )
    
    if user_query or query_input:
        query = user_query or query_input
        
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": query
        })
        
        # Send to backend
        with st.spinner("🤔 Thinking..."):
            response = send_chat_message(
                query,
                st.session_state.document_id,
                st.session_state.chat_history
            )
            
            if response:
                # Extract response components
                assistant_message = {
                    "role": "assistant",
                    "content": response.get("response", "")
                }
                
                # Add optional components
                if "rephrased_query" in response:
                    assistant_message["rephrased_query"] = response["rephrased_query"]
                
                if "sources" in response:
                    assistant_message["sources"] = response["sources"]
                
                if "followup_questions" in response:
                    assistant_message["followup_questions"] = response["followup_questions"]
                
                # Add to messages
                st.session_state.messages.append(assistant_message)
                
                # Update chat history for context
                st.session_state.chat_history.append({
                    "user": query,
                    "assistant": response.get("response", "")
                })
                
                st.rerun()

else:
    # Welcome screen
    st.info("👈 Please upload a PDF document using the sidebar to get started.")
    
    st.markdown("""
    ### How to use this app:
    
    1. **Upload a PDF**: Click on the sidebar and select a PDF file to upload
    2. **Process Document**: Click the "Process Document" button to analyze the PDF
    3. **Start Chatting**: Once processed, ask questions about your document in the chat interface
    4. **Explore Features**:
       - View source citations for each response
       - See how your query was rephrased for better results
       - Click on suggested follow-up questions
    
    ### Features:
    
    - 🤖 **AI-Powered**: Uses Google Gemini API for intelligent responses
    - 🔍 **Context Retrieval**: Finds relevant sections from your document
    - 📊 **Source Citations**: See exactly where information comes from
    - 💡 **Smart Suggestions**: Get follow-up questions to explore further
    - 🎨 **Clean Interface**: Material-inspired design for better UX
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Powered by Streamlit, Google Gemini API, and Context Retrieval"
    "</div>",
    unsafe_allow_html=True
)

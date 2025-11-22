import streamlit as st
import requests
from datetime import datetime
import time

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

# Page config
st.set_page_config(
    page_title="BOT GPT",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.user-message {
    background-color: #e3f2fd;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.assistant-message {
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.conversation-item {
    padding: 8px;
    margin: 5px 0;
    border-radius: 5px;
    cursor: pointer;
    background-color: #f0f0f0;
}
.conversation-item:hover {
    background-color: #e0e0e0;
}
.active-conversation {
    background-color: #d0d0d0;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode" not in st.session_state:
    st.session_state.mode = "open_chat"
if "document_id" not in st.session_state:
    st.session_state.document_id = None
if "conversations_list" not in st.session_state:
    st.session_state.conversations_list = []
if "refresh_list" not in st.session_state:
    st.session_state.refresh_list = True
if "current_document_name" not in st.session_state:
    st.session_state.current_document_name = None


# ==================== API FUNCTIONS ====================

def get_all_conversations():
    """Fetch all conversations from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/conversations")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching conversations: {str(e)}")
        return {"conversations": []}


def get_conversation(conversation_id: str):
    """Get specific conversation by ID"""
    try:
        response = requests.get(f"{API_BASE_URL}/conversations/{conversation_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error loading conversation: {str(e)}")
        return None


def get_document(document_id: str):
    """Get document info by ID"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{document_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


def get_all_documents():
    """Fetch all uploaded documents"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # st.error(f"Error fetching documents: {str(e)}")
        return {"documents": []}


def create_conversation(first_message: str, mode: str, document_id: str = None):
    """Create new conversation"""
    try:
        payload = {
            "mode": mode,
            "first_message": first_message,
            "document_id": document_id
        }
        
        response = requests.post(f"{API_BASE_URL}/conversations", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data
    except Exception as e:
        st.error(f"Error creating conversation: {str(e)}")
        return None


def send_message(conversation_id: str, message: str):
    """Send message to existing conversation"""
    try:
        payload = {"content": message}
        
        response = requests.post(
            f"{API_BASE_URL}/conversations/{conversation_id}/messages",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return data
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return None


def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    try:
        response = requests.delete(f"{API_BASE_URL}/conversations/{conversation_id}")
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error deleting conversation: {str(e)}")
        return False


def delete_document(document_id: str):
    """Delete a document"""
    try:
        response = requests.delete(f"{API_BASE_URL}/documents/{document_id}")
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error deleting document: {str(e)}")
        return False


def upload_document(file):
    """Upload document for RAG"""
    try:
        files = {"file": (file.name, file, file.type)}
        
        response = requests.post(f"{API_BASE_URL}/documents", files=files)
        response.raise_for_status()
        
        data = response.json()
        return data
    except Exception as e:
        st.error(f"Error uploading document: {str(e)}")
        return None


# ==================== HELPER FUNCTIONS ====================

def load_conversation(conv_id: str):
    """Load a conversation into session state"""
    conv_data = get_conversation(conv_id)
    if conv_data:
        st.session_state.conversation_id = conv_data["conversation_id"]
        st.session_state.messages = conv_data["messages"]
        st.session_state.mode = conv_data["mode"]
        
        # Load document name if RAG mode
        if conv_data["mode"] == "rag" and conv_data.get("document_id"):
            doc_info = get_document(conv_data["document_id"])
            if doc_info:
                st.session_state.current_document_name = doc_info["filename"]
                st.session_state.document_id = conv_data["document_id"]
        else:
            st.session_state.current_document_name = None
        
        st.rerun()


def start_new_conversation():
    """Start a new conversation"""
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.session_state.current_document_name = None
    st.session_state.refresh_list = True
    st.rerun()


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to max length"""
    return text[:max_length] + "..." if len(text) > max_length else text


# ==================== SIDEBAR ====================

with st.sidebar:
    st.title("🤖 BOT GPT")
    
    # New Conversation Button
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        start_new_conversation()
    
    st.markdown("---")
    
    # Mode Selection
    st.subheader("⚙️ Settings")
    mode = st.radio(
        "Conversation Mode",
        options=["open_chat", "rag"],
        format_func=lambda x: "💬 Open Chat" if x == "open_chat" else "📚 RAG Mode",
        index=0 if st.session_state.mode == "open_chat" else 1,
        key="mode_selector"
    )
    
    # Update mode if changed
    if mode != st.session_state.mode and not st.session_state.conversation_id:
        st.session_state.mode = mode
    
    # RAG Document Upload
    if mode == "rag":
        st.markdown("### 📄 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["txt", "pdf"],
            help="Upload a document to chat with",
            key="file_uploader"
        )
        
        if uploaded_file and st.button("Upload Document"):
            with st.spinner("Processing document..."):
                doc_data = upload_document(uploaded_file)
                
                if doc_data:
                    st.session_state.document_id = doc_data["document_id"]
                    st.session_state.current_document_name = doc_data["filename"]
                    st.success(f"✅ {doc_data['filename']}")
                    st.info(f"📊 Chunks: {doc_data['total_chunks']}")
        
        if st.session_state.document_id:
            st.success(f"📄 Ready: {st.session_state.current_document_name}")
    
    st.markdown("---")
    
    # Document Library Section
    with st.expander("📚 Document Library", expanded=False):
        st.caption("Uploaded documents for RAG")
        
        # Refresh documents button
        if st.button("🔄 Refresh Documents", key="refresh_docs"):
            st.rerun()
        
        try:
            # Fetch documents
            docs_data = get_all_documents()
            documents = docs_data.get("documents", [])
            
            if documents:
                for doc in documents:
                    doc_id = doc["document_id"]
                    filename = doc["filename"]
                    chunks = doc.get("total_chunks", 0)
                    uploaded_at = doc.get("uploaded_at", "")[:10]  # Date only
                    
                    # Create container for each document
                    doc_col1, doc_col2 = st.columns([4, 1])
                    
                    with doc_col1:
                        st.markdown(f"**{truncate_text(filename, 25)}**")
                        st.caption(f"📊 {chunks} chunks • {uploaded_at}")
                    
                    with doc_col2:
                        if st.button("🗑️", key=f"del_doc_{doc_id}", help="Delete document"):
                            if delete_document(doc_id):
                                st.success("✅")
                                time.sleep(0.5)
                                st.rerun()
                    
                    st.markdown("---")
            else:
                st.info("No documents uploaded yet")
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")
    
    st.markdown("---")
    
    # Conversation History
    st.subheader("💬 Conversation History")
    
    # Refresh button for conversation list
    if st.button("🔄 Refresh", use_container_width=True):
        st.session_state.refresh_list = True
        st.rerun()
    
    # Refresh conversations list
    if st.session_state.refresh_list:
        conversations_data = get_all_conversations()
        st.session_state.conversations_list = conversations_data.get("conversations", [])
        st.session_state.refresh_list = False
    
    # Display conversation history with elegant design
    if st.session_state.conversations_list:
        for conv in st.session_state.conversations_list:
            conv_id = conv["conversation_id"]
            preview = conv.get("preview", "New conversation")
            mode_icon = "📚" if conv["mode"] == "rag" else "💬"
            document_name = conv.get("document_name")
            
            # Determine if active
            is_active = conv_id == st.session_state.conversation_id
            
            # Create expandable container
            with st.container():
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    # Main conversation button
                    button_label = f"{mode_icon} {truncate_text(preview, 35)}"
                    button_type = "primary" if is_active else "secondary"
                    
                    if st.button(
                        button_label,
                        key=f"conv_{conv_id}",
                        use_container_width=True,
                        type=button_type
                    ):
                        load_conversation(conv_id)
                    
                    # Show document name below if RAG mode
                    if conv["mode"] == "rag" and document_name:
                        st.caption(f"📄 Document: {truncate_text(document_name, 35)}")
                
                with col2:
                    # Delete button
                    if st.button("🗑️", key=f"del_{conv_id}", help="Delete"):
                        if delete_conversation(conv_id):
                            st.success("✅")
                            st.session_state.refresh_list = True
                            if conv_id == st.session_state.conversation_id:
                                start_new_conversation()
                            st.rerun()
                
                st.markdown("---")  # Separator between conversations
    else:
        st.info("No conversations yet. Start a new one!")
    
    st.markdown("---")
    
    # Health Check
    try:
        health = requests.get("http://localhost:8000/").json()
        st.success("✅ Backend: Online")
    except:
        st.error("❌ Backend: Offline")


# ==================== MAIN CHAT AREA ====================

# Title
st.title("💬 Chat with BOT GPT")

# Show document info if RAG conversation is active
if st.session_state.conversation_id and st.session_state.mode == "rag":
    if st.session_state.current_document_name:
        st.info(f"📄 **Chatting with document:** {st.session_state.current_document_name}")
    else:
        # Try to fetch document info
        current_conv = get_conversation(st.session_state.conversation_id)
        if current_conv and current_conv.get("document_id"):
            doc_info = get_document(current_conv["document_id"])
            if doc_info:
                st.session_state.current_document_name = doc_info["filename"]
                st.info(f"📄 **Chatting with document:** {doc_info['filename']} ({doc_info['total_chunks']} chunks)")

# Check if RAG mode requires document
if mode == "rag" and not st.session_state.document_id and not st.session_state.conversation_id:
    st.info("📚 Please upload a document in the sidebar to start chatting in RAG mode")
else:
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]
            timestamp = message.get("timestamp", "")
            
            with st.chat_message(role):
                st.markdown(content)
                if timestamp:
                    st.caption(f"⏰ {timestamp[:19]}")
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to UI immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # First message - create conversation
        if not st.session_state.conversation_id:
            with st.spinner("Creating conversation..."):
                conv_data = create_conversation(
                    first_message=user_input,
                    mode=mode,
                    document_id=st.session_state.document_id if mode == "rag" else None
                )
                
                if conv_data:
                    st.session_state.conversation_id = conv_data["conversation_id"]
                    st.session_state.messages = conv_data["messages"]
                    st.session_state.mode = mode
                    st.session_state.refresh_list = True
                    
                    # Show assistant response
                    with st.chat_message("assistant"):
                        st.markdown(st.session_state.messages[-1]["content"])
                    
                    st.rerun()
        
        # Subsequent messages
        else:
            with st.spinner("Thinking..."):
                response_data = send_message(
                    conversation_id=st.session_state.conversation_id,
                    message=user_input
                )
                
                if response_data:
                    st.session_state.messages.append(response_data["user_message"])
                    st.session_state.messages.append(response_data["assistant_message"])
                    
                    # Show assistant response
                    with st.chat_message("assistant"):
                        st.markdown(response_data["assistant_message"]["content"])
                    
                    st.rerun()


# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.conversation_id:
        st.caption(f"**Conversation ID:** {st.session_state.conversation_id[:8]}...")

with col2:
    mode_display = "Open Chat" if st.session_state.mode == "open_chat" else "RAG Mode"
    st.caption(f"**Mode:** {mode_display}")

with col3:
    if st.session_state.messages:
        st.caption(f"**Messages:** {len(st.session_state.messages)}")

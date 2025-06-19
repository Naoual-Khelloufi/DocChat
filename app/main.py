# Application entry point
import streamlit as st
from components.sidebar import show_sidebar
from components.chat import chat_interface
from components.pdf_viewer import display_pdf_viewer
from core.document import DocumentProcessor
from core.embeddings import VectorStore
import tempfile
import os

def init_session_state():
    if 'vector_db' not in st.session_state:
        st.session_state.vector_db = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def main():
    init_session_state()
    st.set_page_config(page_title="Ollama RAG", layout="wide")
    
    st.title("📚 RAG Local avec Ollama")
    
    # Sidebar pour upload et configuration
    temp_dir = show_sidebar()
    
    # Colonnes principales
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if 'uploaded_files' in st.session_state and st.session_state.uploaded_files:
            display_pdf_viewer(temp_dir)
    
    with col2:
        chat_interface()

if __name__ == "__main__":
    main()
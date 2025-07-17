import streamlit as st
from core.document import DocumentProcessor
from core.embeddings import VectorStore
import tempfile
from pathlib import Path 
from core.auth import crud, database


def process_files(uploaded_files):
    processor = DocumentProcessor()
    vector_store = VectorStore()
    temp_dir = tempfile.mkdtemp()
    
    all_docs = []
    for uploaded_file in uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = Path(temp_dir) / uploaded_file.name  
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        docs = processor.load_document(file_path)  
        chunks = processor.split_documents(docs)
        all_docs.extend(chunks)
    
    if all_docs:
        st.session_state.vector_db = vector_store.create_vector_db(all_docs)
    return temp_dir

def show_sidebar():
    with st.sidebar:
        #st.header("⚙️ Configuration")
        
        uploaded_files = st.file_uploader(
            "Téléversez vos documents",
            type=['pdf', 'txt', 'docx'],
            accept_multiple_files=True
        )
        
        temp_dir = None
        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files
            temp_dir = process_files(uploaded_files)
            st.success(f"{len(uploaded_files)} fichier(s) chargé(s)")
        
        st.selectbox(
            "Modèle Ollama",
            ["llama3.2:latest","llama2:7b", "mistral", "gemma"],
            key="selected_model"
        )
        
        if st.button("Effacer la conversation"):
            st.session_state.chat_history = []
            st.rerun()

        # Récupère l'objet user ou {} par défaut
        user = st.session_state.get("user", {})

        # Normalise : si la clé id n'existe pas, force-la à None
        if "id" not in user:
            user["id"] = None
            st.session_state["user"] = user  # on ré-injecte la version propre

        # Crée user_id dans la session si manquant
        if "user_id" not in st.session_state:
            st.session_state["user_id"] = user["id"]
        #if "user_id" not in st.session_state and "user" in st.session_state:
        #    st.session_state["user_id"] = st.session_state["user"]["id"]

        #user = st.session_state.get("user", {})
        #if "user_id" not in st.session_state:
        #    st.session_state["user_id"] = user.get("id")     #guest


        user_id = st.session_state.get("user_id")      # None pour guest

        # ───────── Section Admin (visible seulement pour role=admin) ─────────
        if st.session_state.user["role"] == "admin":
            st.markdown("---")
        if st.button("🔧 Admin Dashboard"):
            st.switch_page("admin_dashboard")   # ou st.session_state.current_screen = "admin_dashboard"




        # On rend le bouton seulement si user_id existe
        if user_id is not None and st.button("Afficher mon historique"):
        
            db = database.SessionLocal()
            history = crud.get_user_history(db, user_id, limit=10)

            if not history:
                st.warning("Aucun historique trouvé.")
            else:
                for h in history:
                    st.markdown(f"**🕑 {h.timestamp.strftime('%d/%m %H:%M')}**")
                    st.markdown(f"**❓ Q :** {h.question}")
                    st.markdown(f"**💬 R :** {h.answer[:100]}...")
                    st.markdown('-----')



    return temp_dir
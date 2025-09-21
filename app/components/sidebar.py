import streamlit as st
from core.document import DocumentProcessor
from core.embeddings import VectorStore
from pathlib import Path 
from core.auth import crud, database, models
from utils.nav import navigate
from reporting.log import log_event
import uuid


def process_files(uploaded_files):
    if not uploaded_files:
        return

    db  = database.SessionLocal()
    uid = st.session_state["user_id"]
    user_dir = Path("data") / "docs" / f"user_{uid}"
    user_dir.mkdir(parents=True, exist_ok=True)

    processor     = DocumentProcessor()
    vector_store  = VectorStore()
    new_chunks    = []

    for up in uploaded_files:
        # Check if the file already exists in the DB
        already = db.query(models.Document).filter_by(
            owner_id=uid, title=up.name
        ).first()
        if already:
            continue   # avoid duplicate

        # Copy into the persistent folder
        dest = user_dir / up.name
        with open(dest, "wb") as f:
            f.write(up.getbuffer())

        # Meta storage
        doc = crud.save_document(db, uid, up.name, str(dest))
        st.session_state.current_doc_id = doc.id

        # LOG upload : Reporting
        log_event(
            event_type="upload",
            user_id=st.session_state.get("user_id"),
            session_id=st.session_state.get("session_id"),
            payload={
                "filename": up.name,
                "size": getattr(up, "size", None),
                "path": str(dest),
                "doc_id": doc.id
            }
        )

        # Vectorization
        raw    = processor.load_document(dest)
        chunks = processor.split_documents(raw)
        new_chunks.extend(chunks)

    # Update the semantic index only once
    if new_chunks:
        st.session_state.vector_db = vector_store.create_vector_db(new_chunks)

    # Clear the list to avoid reprocessing on rerun
    st.session_state.uploaded_files.clear()


def show_sidebar():
    with st.sidebar:
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())

        # Normalize user and user_id before upload
        user = st.session_state.get("user", {})

        # If no id key we set None and re-inject
        if "id" not in user:
            user["id"] = None
            st.session_state["user"] = user

        # Create the user_id key if missing
        if "user_id" not in st.session_state:
            st.session_state["user_id"] = user["id"]

        if user and user.get("role") != "guest":
            if st.button("Profil", key="btn_profile"):
                navigate("profile")

        uploaded_files = st.file_uploader(
            "Téléversez vos documents",
            type=['pdf', 'txt', 'docx', 'csv'],
            accept_multiple_files=True
        )
        
        temp_dir = None
        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files
            temp_dir = process_files(uploaded_files)
            st.success(f"{len(uploaded_files)} fichier(s) chargé(s)")
        
        st.selectbox(
            "Modèle Ollama",
            ["llama3.2:latest","llama2:7b"],
            key="selected_model"
        )
        
        if st.button("Effacer la conversation"):
            st.session_state.chat_history = []
            st.rerun()

        # Retrieve the user object or {} by default
        user = st.session_state.get("user", {})

        # Normalize : if the id do not exist we make it None
        if "id" not in user:
            user["id"] = None
            st.session_state["user"] = user  # re-inject the cleaned version

        # Create user_id in the session if needed
        if "user_id" not in st.session_state:
            st.session_state["user_id"] = user["id"]

        # Section Admin (only visible role=admin)
        if st.session_state.user["role"] == "admin":
            st.markdown("---")
            if st.button("Admin Dashboard"):
                navigate("admin_dashboard")
            
        _show_library()
        _show_history_dates()

        #  Deconnect button
        if user.get("role") != "guest" and st.session_state.get("user_id"):
            if st.button("Se déconnecter", key="logout_btn"):
                _logout()  
    return temp_dir

def _show_library():
    if "user_id" not in st.session_state:
        return
    if not st.session_state.get("user_id"):
        return
    db = database.SessionLocal()
    docs = crud.list_user_documents(db, st.session_state["user_id"])
    if not docs:
        return

    st.markdown("### Ma bibliothèque")
    for d in docs:
        row = st.columns([6, 1])
        if row[0].button(d.title, key=f"doc-{d.id}"):
            st.session_state.current_doc_id = d.id
            st.session_state.chat_mode = "regular"
            st.rerun()
        if row[1].button("Supprimer", key=f"del-{d.id}"):
            crud.delete_document(db, d.id, st.session_state["user_id"])

def _show_history_dates():
    if "user_id" not in st.session_state:
        return
    db = database.SessionLocal()
    hist = crud.get_user_history(db, st.session_state["user_id"])
    dates = sorted({h.timestamp.strftime("%Y-%m-%d") for h in hist}, reverse=True)
    if not dates:
        return
    st.markdown("### Mes dates")
    for d in dates:
        if st.button(d, key=f"date-{d}"):
            st.session_state.selected_date = d
            st.session_state.chat_mode = "history"
            st.rerun()

def _logout():
    """Nettoie les infos d’auth et réinitialise la session."""
    for k in ("user", "user_id", "auth_action"):
        st.session_state.pop(k, None)
    navigate("landing")
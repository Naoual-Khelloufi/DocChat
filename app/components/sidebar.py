import streamlit as st
from core.document import DocumentProcessor
from core.embeddings import VectorStore
from pathlib import Path 
from core.auth import crud, database, models


def process_files(uploaded_files):
    if not uploaded_files:               # rien à faire
        return

    db  = database.SessionLocal()
    uid = st.session_state["user_id"]

    # ------------------------------------------------------------------
    # Dossier *persistant* pour l'utilisateur (voir Correctif 2)
    # ------------------------------------------------------------------
    user_dir = Path("data") / "docs" / f"user_{uid}"
    user_dir.mkdir(parents=True, exist_ok=True)

    processor     = DocumentProcessor()
    vector_store  = VectorStore()
    new_chunks    = []

    for up in uploaded_files:
        # --- 1 Vérifie si le fichier existe déjà en BD -------------
        already = db.query(models.Document).filter_by(
            owner_id=uid, title=up.name
        ).first()
        if already:
            continue                               # évite le doublon

        # --- 2  Copie dans le dossier persistant --------------------
        dest = user_dir / up.name
        with open(dest, "wb") as f:
            f.write(up.getbuffer())

        # --- 3  Sauvegarde meta -------------------------------------
        doc = crud.save_document(db, uid, up.name, str(dest))
        st.session_state.current_doc_id = doc.id

        # --- 4  Vectorisation ---------------------------------------
        raw    = processor.load_document(dest)
        chunks = processor.split_documents(raw)
        new_chunks.extend(chunks)

    # --- 5  Met à jour l’index sémantique une seule fois ------------
    if new_chunks:
        st.session_state.vector_db = vector_store.create_vector_db(new_chunks)

    # 6  Vider la liste pour éviter de retraiter au rerun ----------
    st.session_state.uploaded_files.clear()


def show_sidebar():
    with st.sidebar:
        # Affichage de l'icône profil pour tout utilisateur connecté
        #if st.session_state.get("user"):
        user = st.session_state.get("user")          # dict ou None
        if user and user.get("role") != "guest":
            if st.button("👤 Profil", key="btn_profile"):
                st.session_state.current_screen = "profile"   # nouvelle page
        
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


        #user_id = st.session_state.get("user_id")      # None pour guest

        # ───────── Section Admin (visible seulement pour role=admin) ─────────
        if st.session_state.user["role"] == "admin":
            st.markdown("---")
            if st.button("🔧 Admin Dashboard"):
                st.session_state.current_screen = "admin_dashboard"


        _show_library()
        _show_history_dates()

        #  bouton Déconnexion
        if user.get("role") != "guest" and st.session_state.get("user_id"):
            if st.button("Se déconnecter", key="logout_btn"):
                _logout()  
        #if st.button(" Se déconnecter", key="logout_btn"):
            #_logout()

        # On rend le bouton seulement si user_id existe
        #if user_id is not None and st.button("Afficher mon historique"):
            #db = database.SessionLocal()
            #history = crud.get_user_history(db, user_id, limit=10)

            #if not history:
            #    st.warning("Aucun historique trouvé.")
            #else:
            #    for h in history:
            #        st.markdown(f"**🕑 {h.timestamp.strftime('%d/%m %H:%M')}**")
            #        st.markdown(f"**❓ Q :** {h.question}")
            #        st.markdown(f"**💬 R :** {h.answer[:100]}...")
            #        st.markdown('-----')

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

    st.markdown("### 📂 Ma bibliothèque")
    for d in docs:
        row = st.columns([6, 1])
        if row[0].button(d.title, key=f"doc-{d.id}"):
            st.session_state.current_doc_id = d.id
            st.session_state.chat_mode = "regular"
            st.rerun()
        if row[1].button("🗑️", key=f"del-{d.id}"):
            crud.delete_document(db, d.id, st.session_state["user_id"])

def _show_history_dates():
    if "user_id" not in st.session_state:
        return
    db = database.SessionLocal()
    hist = crud.get_user_history(db, st.session_state["user_id"])
    dates = sorted({h.timestamp.strftime("%Y-%m-%d") for h in hist}, reverse=True)
    if not dates:
        return
    st.markdown("### 📅 Mes dates")
    for d in dates:
        if st.button(d, key=f"date-{d}"):
            st.session_state.selected_date = d
            st.session_state.chat_mode = "history"
            st.rerun()

# -----------------------------------------------------------------------
def _logout():
    """Nettoie les infos d’auth et réinitialise la session."""
    # 1) retirer les clés sensibles
    for k in ("user", "user_id", "auth_action"):
        st.session_state.pop(k, None)

    # 2) remettre l’écran sur la page d’accueil / choix
    st.session_state.current_screen = "landing"   # ou "auth_choice"

    # 3) (optionnel) vider d’autres états si tu veux
    st.session_state.pop("current_doc_id", None)
    st.session_state.pop("chat_mode", None)
    # ne vide pas vector_db si tu préfères le garder en cache !

import streamlit as st
from core.auth import crud, database
from app.components.chat import answer_question
from app.components.pdf_viewer import display_file_viewer_by_id


def render():
    date_str = st.session_state.get("selected_date")

    if "view_doc_id" not in st.session_state:
        st.session_state.view_doc_id = None

    if not date_str:
        st.error("Pas de date sélectionnée") 
        return

    db  = database.SessionLocal()
    uid = st.session_state["user_id"]
    hist = crud.get_user_history(db, uid)
    messages = [h for h in hist if h.timestamp.strftime("%Y-%m-%d") == date_str]
    doc_ids  = {h.document_id for h in messages if h.document_id}
    doc_id   = next(iter(doc_ids), None)

    if st.session_state.view_doc_id:
        with st.container():
            display_file_viewer_by_id(st.session_state.view_doc_id)
            st.markdown("---")
    
    # Layout
    if doc_id:
        col_pdf, col_chat = st.columns([1, 2])
        with col_pdf: 
            display_file_viewer_by_id(doc_id)
    else:
        col_chat = st.container()

    with col_chat:
        st.title(f" Historique du {date_str}")
        for h in messages:
            head_col, trash_col = st.columns([10, 1])
            head_col.markdown(f"** {h.timestamp.strftime('%H:%M:%S')}**")
            if trash_col.button("Supprimer", key=f"del-msg-{h.id}", help="Supprimer"):
                crud.delete_message(db, h.id, uid)
                
            head_col, view_col, trash_col = st.columns([9, 1, 1])
            if h.document_id and view_col.button("Voir pdf", key=f"view-{h.id}", help="Voir le PDF"):
                st.session_state.view_doc_id = h.document_id
            
            st.markdown(f"** Q :** {h.question}")
            st.markdown(f"** R :** {h.answer}")
            st.markdown("-----")

        st.markdown(" Nouvelle question")
        q = st.text_input("Votre question…", key="hist_q")
        if st.button("Envoyer", key="hist_send") and q:
            ans = answer_question(q, doc_id=doc_id)
            st.markdown(f"** R :** {ans}")
            crud.save_message(db, uid, q, ans, document_id=doc_id)

        if st.button("⬅️ Retour au chat"):
            st.session_state.chat_mode = "regular"
            st.session_state.selected_date = None
            st.session_state.view_doc_id    = None
            st.rerun()

import streamlit as st
from core.llm import LLMManager
from core.auth import crud, database, models
from pathlib import Path
from core.document import DocumentProcessor
from reporting.log import track_event, log_event


def chat_interface():
    st.subheader("💬 Chat avec vos documents")
    
    # Affichage historique
    for msg in st.session_state.get('chat_history', []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Nouveau message
    if prompt := st.chat_input("Posez votre question..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        #if 'vector_db' in st.session_state and st.session_state.vector_db:
        #    with st.spinner("Recherche en cours..."):
        #        with track_event(
        #            event_type="query",
        #            user_id=st.session_state.get("user_id"),
        #            session_id=st.session_state.get("session_id"),
        #            prompt=prompt,
        #            payload={"top_k": 3, "source": "chat_interface"}
        #        ):
        #            try:
        #                llm = LLMManager(model_name=st.session_state.get("selected_model", "llama3.2:latest"))
        #                context = st.session_state.vector_db.similarity_search(prompt, k=3)
        #                response = llm.generate_answer(context, prompt)

        #                with st.chat_message("assistant"):
        #                    st.markdown(response)
        #                st.session_state.chat_history.append({"role": "assistant", "content": response})

        #                if ("user_id" in st.session_state and st.session_state["user_id"] is not None):
        #                    db = database.SessionLocal()
        #                    crud.save_chat_history(db, user_id=st.session_state["user_id"], question=prompt, answer=response)
        #            except Exception as e:
        #                log_event(
        #                    event_type="error",
        #                    user_id=st.session_state.get("user_id"),
        #                    session_id=st.session_state.get("session_id"),
        #                    payload={"where": "chat_interface", "error": str(e)[:300]}
        #                )
        #                st.error(f"Erreur : {str(e)}")
        if 'vector_db' in st.session_state and st.session_state.vector_db:
            with st.spinner("Recherche en cours..."):
                with track_event(...):
                    try:
                        llm = LLMManager(model_name=st.session_state.get("selected_model", "llama3.2:latest"))
                        context = st.session_state.vector_db.similarity_search(prompt, k=3)

                        # ✅ FALLBACK si la recherche ne renvoie rien
                        if not context:
                            response = llm.generate_general(prompt, max_tokens=600)
                        else:
                            response = llm.generate_answer(context, prompt)

                        with st.chat_message("assistant"):
                            st.markdown(response)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})

                        if ("user_id" in st.session_state and st.session_state["user_id"] is not None):
                            db = database.SessionLocal()
                            crud.save_chat_history(db, user_id=st.session_state["user_id"], question=prompt, answer=response)
                    except Exception as e:
                        log_event(...)
                        st.error(f"Erreur : {str(e)}")
        else:
            #st.warning("Veuillez d'abord charger des documents")
            llm = LLMManager(model_name=st.session_state.get("selected_model", "llama3.2:latest"))
            try:
                response = llm.generate_general(prompt, max_tokens=600)
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

                if ("user_id" in st.session_state and st.session_state["user_id"] is not None):
                    db = database.SessionLocal()
                    crud.save_chat_history(db, user_id=st.session_state["user_id"], question=prompt, answer=response)
            except Exception as e:
                log_event(...)
                st.error(f"Erreur : {str(e)}")


def answer_question(question: str, doc_id: int | None = None) -> str:
    """
    Prépare le contexte documentaire puis interroge le LLM.
    Enregistre la nouvelle Q/R en base.
    """
    db  = database.SessionLocal()
    uid = st.session_state["user_id"]

    with track_event(
        event_type="query",
        user_id=uid,
        session_id=st.session_state.get("session_id"),
        prompt=question,
        payload={"doc_id": doc_id, "source": "history_view"}
    ):

        # -------- 1) chemins PDF ------------------------------------------------
        if doc_id:
            doc_paths = [db.get(models.Document, doc_id).path]
        else:
            docs = crud.list_user_documents(db, uid)
            doc_paths = [d.path for d in docs]

        # -------- 2) Charger et découper les documents --------------------------
        processor = DocumentProcessor()
        context_docs = []
        for p in doc_paths:
            raw_docs  = processor.load_document(Path(p))     # PDF/TXT → LangchainDocument
            chunks    = processor.split_documents(raw_docs)  # découpe en segments
            context_docs.extend(chunks)

        # -------- 3) Appel du LLM -----------------------------------------------
        llm = LLMManager(model_name=st.session_state.get("selected_model", "llama3.2:latest"))
        answer = llm.generate_answer(context_docs, question)

        # -------- 4) Sauvegarde en BD -------------------------------------------
        crud.save_message(db, uid, question, answer, document_id=doc_id)
        return answer

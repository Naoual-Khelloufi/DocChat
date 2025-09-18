import streamlit as st
from core.llm import LLMManager
from core.auth import crud, database, models
from pathlib import Path
from core.document import DocumentProcessor
from reporting.log import track_event, log_event


def chat_interface():
    st.subheader("💬 Chat avec vos documents")
    
    # Display history
    for msg in st.session_state.get('chat_history', []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # New message
    prompt = st.chat_input("Posez votre question...")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        llm = LLMManager(model_name=st.session_state.get("selected_model", "llama3.2:latest"))

        try:
            with track_event(
                event_type="query",
                user_id=st.session_state.get("user_id"),
                session_id=st.session_state.get("session_id"),
                prompt=prompt,
                payload={"source": "chat_interface", "top_k": 3}
            ):
                # 1) Context : if index present
                context = []
                if 'vector_db' in st.session_state and st.session_state.vector_db:
                    context = st.session_state.vector_db.similarity_search(prompt, k=3)

                # 2) Answer : if context : RAG , else : general
                if context:
                    response = llm.generate_answer(context, prompt)
                else:
                    response = llm.generate_general(prompt, max_tokens=600)

            # 3) Display + persistence
            with st.chat_message("assistant"):
                st.markdown(response)

            st.session_state.chat_history.append({"role": "assistant", "content": response})

            if ("user_id" in st.session_state and st.session_state["user_id"] is not None):
                db = database.SessionLocal()
                crud.save_chat_history(db, user_id=st.session_state["user_id"], question=prompt, answer=response)

        except Exception as e:
            log_event(
                event_type="error",
                user_id=st.session_state.get("user_id"),
                session_id=st.session_state.get("session_id"),
                status="error",
                latency_ms=0,
                prompt=(prompt or "")[:500],
                payload={"where": "chat_interface", "error": str(e)[:300]},
            )
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

        # ----- PDF path -------
        if doc_id:
            doc_paths = [db.get(models.Document, doc_id).path]
        else:
            docs = crud.list_user_documents(db, uid)
            doc_paths = [d.path for d in docs]

        # ----- Load and split docs ------
        processor = DocumentProcessor()
        context_docs = []
        for p in doc_paths:
            raw_docs  = processor.load_document(Path(p))  
            chunks    = processor.split_documents(raw_docs)  
            context_docs.extend(chunks)

        # ---- Call the LLM ------
        llm = LLMManager(model_name=st.session_state.get("selected_model", "llama3.2:latest"))
        answer = llm.generate_answer(context_docs, question)

        # ----- Save in Database ------
        crud.save_message(db, uid, question, answer, document_id=doc_id)
        return answer

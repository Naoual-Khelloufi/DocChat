import streamlit as st
from core.llm import LLMManager

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
        
        if 'vector_db' in st.session_state and st.session_state.vector_db:
            with st.spinner("Recherche en cours..."):
                try:
                    llm = LLMManager(model_name=st.session_state.get("selected_model", "llama2"))
                    context = st.session_state.vector_db.similarity_search(prompt, k=3)
                    response = llm.generate_answer(context, prompt)
                    
                    with st.chat_message("assistant"):
                        st.markdown(response)
                    
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")
        else:
            st.warning("Veuillez d'abord charger des documents")
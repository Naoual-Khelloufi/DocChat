import streamlit as st
from components.sidebar import show_sidebar
from components.chat import chat_interface
from components.pdf_viewer import display_pdf_viewer, display_pdf_viewer_by_id
from app.components.auth.choice import show_auth_choice
from app.components.auth.login import show_login
from app.components.auth.register import show_register
from app.components.admin_dashboard import render as admin_dashboard  # 🆕
from app.components.profile_page import render as profile_page   # adapte le chemin
from app.components.history_view import render as history_view

def init_session_state():
    # États existants
    if 'vector_db' not in st.session_state:
        st.session_state.vector_db = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    # Nouveaux états pour l'authentification
    if 'current_screen' not in st.session_state:
        st.session_state.current_screen = "landing"  # landing → auth_choice → login/register/main_app
    if 'user' not in st.session_state:
        st.session_state.user = None

def landing_page():
    """Écran d'accueil avec bouton Commencer"""
    st.title("📚 RAG Local avec Ollama")
    st.markdown("""
    Système intelligent de chat avec vos documents utilisant Ollama et LangChain.
    """)
    
    if st.button("Commencer", key="start_btn"):
        st.session_state.current_screen = "auth_choice"
        st.rerun()



#def main_interface():
#    """Votre interface principale existante"""
#    st.title("📚 RAG Local avec Ollama")
    
    # Sidebar pour upload et configuration
#    temp_dir = show_sidebar()
    
    # Colonnes principales
#    col1, col2 = st.columns([1, 2])
    
#    with col1:
#        if st.session_state.uploaded_files:
#            display_pdf_viewer(temp_dir)
    
#    with col2:
#        chat_interface()


def main_interface():
    st.title("📚 RAG Local avec Ollama")
    temp_dir = show_sidebar()

    # mode normal ou historique
    mode = st.session_state.get("chat_mode", "regular")

    if mode == "history":
        history_view()
        return

    # --- vue régulière ---
    doc_id = st.session_state.get("current_doc_id")
    col1, col2 = st.columns([1, 2])

    with col1:
        if doc_id:
            display_pdf_viewer_by_id(doc_id)
        elif st.session_state.uploaded_files:
            display_pdf_viewer(temp_dir)

    with col2:
        chat_interface()




def main():
    init_session_state()
    st.set_page_config(page_title="Ollama RAG", layout="wide")

    # Router basé sur current_screen
    if st.session_state.current_screen == "landing":
        landing_page()

    elif st.session_state.current_screen == "auth_choice":
        st.title("📚 RAG Local avec Ollama")
        show_auth_choice()
        
        # Gestion des actions après choix
        if st.session_state.get("auth_action") == "login":
            st.session_state.current_screen = "login"
            st.rerun()
        elif st.session_state.get("auth_action") == "register":
            st.session_state.current_screen = "register"
            st.rerun()
        elif st.session_state.get("auth_action") == "guest":
            st.session_state.user = {"id": None,"username": "invité", "role": "guest"}
            st.session_state.current_screen = "main_app"
            st.rerun()

    elif st.session_state.current_screen == "login":
        st.title("📚 RAG Local avec Ollama")
        if show_login():  # Retourne True si connexion réussie
            st.session_state.current_screen = "main_app"
            st.rerun()

    elif st.session_state.current_screen == "register":
        st.title("📚 RAG Local avec Ollama")
        if show_register():  # Retourne True si inscription réussie
            st.session_state.current_screen = "login"  # Redirige vers le login
            st.rerun()

    ############
    elif st.session_state.current_screen == "profile":
        if st.session_state.user:
            profile_page()             # affiche la page profil
        else:
            st.warning("Vous devez être connecté.")
            st.session_state.current_screen = "auth_choice"
    #############
    elif st.session_state.current_screen == "admin_dashboard":
    # accès réservé
        if (
            st.session_state.user
            and st.session_state.user.get("role") == "admin"
        ):
            admin_dashboard()                       # appelle render() de la page
        else:
            st.error("Accès réservé à l’administrateur.")
            st.session_state.current_screen = "main_app"
            st.rerun()

    elif st.session_state.current_screen == "main_app":
        # Seulement si connecté ou invité
        if st.session_state.user:
            main_interface()
        else:
            st.warning("Veuillez vous authentifier")
            st.session_state.current_screen = "auth_choice"
            st.rerun()

if __name__ == "__main__":
    main()
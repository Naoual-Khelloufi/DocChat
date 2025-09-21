import streamlit as st
from components.sidebar import show_sidebar
from components.chat import chat_interface
from app.components.auth.choice import show_auth_choice
from app.components.auth.login import show_login
from app.components.auth.register import show_register
from app.components.auth.reset_password import show_reset_password
from app.components.admin_dashboard import render as admin_dashboard 
from app.components.profile_page import render as profile_page
from app.components.history_view import render as history_view
from app.components.auth.reset_password_confirm import show_reset_password_confirm
from components.pdf_viewer import display_file_viewer, display_file_viewer_by_id
from utils.nav import navigate
from reporting.db import init_db
import base64
import mimetypes
from pathlib import Path

def init_session_state():
    # Existing states
    if 'vector_db' not in st.session_state:
        st.session_state.vector_db = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    # New states for authentication
    if 'current_screen' not in st.session_state:
        st.session_state.current_screen = "landing"  # landing -> auth_choice -> login/register/main_app
    if 'user' not in st.session_state:
        st.session_state.user = None

#--------------
def _load_css(path: str = "assets/style.css"):
    p = Path(path)
    if p.exists():
        st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

def _img_data_uri(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"
#---------------

def landing_page():
    """Improved home screen"""
    _load_css("assets/style.css")
    logo_src = _img_data_uri("assets/logo_1.png")
    st.markdown(
        f"""
        <section class="landing-header">
          <img class="landing-logo" src="{logo_src}" alt="DocChat Logo" />
          <p class="landing-tagline">
            Quand vos documents prennent la parole.
          </p>
        </section>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns(3)

    with col1:
     if st.button("Connexion", key="login_btn", type="primary"):
        st.session_state.auth_action = "login"
        navigate("login")

    with col2:
     if st.button("Inscription", key="register_btn", type="primary"):
        st.session_state.auth_action = "register"
        navigate("register")

    with col3:
     if st.button("Continuer sans compte", key="guest_btn", type="primary"):
        st.session_state.user = {"id": None, "username": "invité", "role": "guest"}
        navigate("main_app")
 
    st.subheader("Nos Services")
    
    service1, service2, service3 = st.columns(3)
    
    with service1:
        st.markdown("""
        <div class='service-card'>
            <h4>Analyse de documents</h4>
            <p>Extraction intelligente d'informations</p>
        </div>
        """, unsafe_allow_html=True)
    
    with service2:
        st.markdown("""
        <div class='service-card'>
            <h4>Recherche contextuelle</h4>
            <p>Réponses précises basées sur vos PDF</p>
        </div>
        """, unsafe_allow_html=True)
    
    with service3:
        st.markdown("""
        <div class='service-card'>
            <h4>Historique des conversations</h4>
            <p>Retrouvez toutes vos interactions</p>
        </div>
        """, unsafe_allow_html=True)

def main_interface():
    _load_css()
    src = _img_data_uri("assets/logo_1.png")  
    st.markdown(
        f"""
        <div class="login-logo">
            <img src="{src}" alt="DocChat Logo"/>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    temp_dir = show_sidebar()
    mode = st.session_state.get("chat_mode", "regular")

    if mode == "history":
        history_view()
        return

    # Regular view
    doc_id = st.session_state.get("current_doc_id")
    col1, col2 = st.columns([1, 2])

    with col1:
        if doc_id:
            display_file_viewer_by_id(doc_id)
        elif st.session_state.uploaded_files:
            display_file_viewer(temp_dir)

    with col2:
        chat_interface()

def main():
    init_session_state()
    st.set_page_config(
    page_title="DocChat",
    page_icon="/home/naoual/nlp_rag_system/assets/logo.ico",
    layout="wide"
    )
    init_db()
    # Read url parameters with the modern api
    params = st.query_params
    screen_param = params.get("screen")     # string or None
    token_param  = params.get("token")      # string or None

    if token_param:
        st.session_state.reset_token = token_param
        st.session_state.current_screen = "reset_password_confirm"
        st.query_params.from_dict({"screen": "reset_password_confirm"})
        st.rerun()
    elif screen_param and screen_param != st.session_state.current_screen:
        st.session_state.current_screen = screen_param

    if st.session_state.current_screen == "landing":
        landing_page()

    elif st.session_state.current_screen == "auth_choice":
        show_auth_choice()
        
        # Manage actions after selection
        if st.session_state.get("auth_action") == "login":
            navigate("login")  
        elif st.session_state.get("auth_action") == "register":
            navigate("register")
        elif st.session_state.get("auth_action") == "guest":
            st.session_state.user = {"id": None,"username": "invité", "role": "guest"}
            navigate("main_app")

    elif st.session_state.current_screen == "login":
        if show_login():
            st.session_state.current_screen = "main_app"
            st.query_params.from_dict({"screen": "main_app"})
            st.rerun()

    elif st.session_state.current_screen == "register":
        if show_register():
            st.session_state.current_screen = "login"
            st.rerun()

    elif st.session_state.current_screen == "reset_password":
        show_reset_password()
    
    elif st.session_state.current_screen == "reset_password_confirm":
        show_reset_password_confirm()

    elif st.session_state.current_screen == "profile":
        if st.session_state.user:
            profile_page()
        else:
            st.warning("Vous devez être connecté.")
            st.session_state.current_screen = "auth_choice"
    
    elif st.session_state.current_screen == "admin_dashboard":
        if (
            st.session_state.user
            and st.session_state.user.get("role") == "admin"
        ):
            admin_dashboard()
        else:
            st.error("Accès réservé à l’administrateur.")
            st.session_state.current_screen = "main_app"
            st.rerun()

    elif st.session_state.current_screen == "main_app":
        # Only if logged in or guest
        if st.session_state.user:
            main_interface()
        else:
            st.warning("Veuillez vous authentifier")
            st.session_state.current_screen = "auth_choice"
            st.rerun()

if __name__ == "__main__":
    main()
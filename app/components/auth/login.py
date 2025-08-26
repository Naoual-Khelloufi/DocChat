import streamlit as st
from pathlib import Path
from core.auth.database import get_db
from core.auth.models import User

def _load_css(path: str = "assets/style-login.css") -> None:
    p = Path(path)
    if p.exists():
        st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS introuvable: {p}")

def show_login() -> bool:
    _load_css()  # applique les styles (ciblage data-testid dans le CSS)
    st.markdown("<h1 class='login-title'>Connexion</h1>", unsafe_allow_html=True)

    # Centrer le formulaire
    _, col, _ = st.columns([1, 2, 1])
    with col:
        db = get_db()
        try:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "", placeholder="Nom d'utilisateur",
                    key="login_username", label_visibility="collapsed"
                )
                password = st.text_input(
                    "", placeholder="Mot de passe",
                    type="password", key="login_password",
                    label_visibility="collapsed"
                )
                submitted = st.form_submit_button("Se connecter")

            # Liens bas de page (2 colonnes)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Mot de passe oublié ?", key="forgot_pass"):
                    st.session_state.current_screen = "reset_password"     # adapte à ta vue “reset”
                    st.rerun()
            with c2:
                if st.button("Créer un compte", key="create_account"):
                    st.session_state.current_screen = "register"    # vue d’inscription
                    st.rerun()

            # Auth
            if submitted:
                if not username.strip() or not password.strip():
                    st.error("Veuillez renseigner le nom d'utilisateur et le mot de passe.")
                    return False

                user = db.query(User).filter(User.username == username).first()
                if user and user.verify_password(password):
                    st.session_state.user = {
                        "id": user.id,
                        "username": user.username,
                        "role": "admin" if user.is_admin else "user",
                    }
                    st.session_state.current_screen = "main_app"
                    st.rerun()  # va à l’écran principal
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect")

            return False
        finally:
            db.close()

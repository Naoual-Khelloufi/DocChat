from pathlib import Path
import streamlit as st
from core.auth.database import get_db
from core.auth.models import User
import base64
import mimetypes

def _load_css(path: str = "assets/style-login.css"):
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

def show_login() -> bool:
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
    st.markdown("<h1 class='login-title'>Connexion</h1>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        db = get_db()
        try:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "", placeholder="Nom d'utilisateur", key="login_username",
                    label_visibility="collapsed",
                )
                password = st.text_input(
                    "", placeholder="Mot de passe", type="password", key="login_password",
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button("Se connecter")

            # Liens bas de page
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Mot de passe oublié ?", key="forgot_pass"):
                    st.session_state.current_screen = "reset_password"
                    st.query_params.from_dict({"screen": "reset_password"})  # MAJ URL
                    st.rerun()
            with c2:
                if st.button("Créer un compte", key="create_account"):
                    st.session_state.current_screen = "register"
                    st.query_params.from_dict({"screen": "register"})        # MAJ URL
                    st.rerun()

            if not submitted:
                return False

            # ----- Auth -----
            user = db.query(User).filter(User.username == username).first()
            if user and user.verify_password(password):
                st.session_state.user = {
                    "id": user.id,
                    "username": user.username,
                    "role": "admin" if getattr(user, "is_admin", False) else "user",
                }
                # ⚠️ Ne PAS faire st.rerun() ici
                # ⚠️ Ne PAS changer current_screen ici
                return True
            else:
                st.error("Identifiants incorrects")
                return False
        finally:
            db.close()

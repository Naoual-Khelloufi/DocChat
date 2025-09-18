import re
import time
import streamlit as st
from pathlib import Path
from core.auth.database import get_db
from core.auth.service import request_password_reset 
import base64
import mimetypes

# ----Style-------
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


# ---- Rate-limit simple (session)------
def can_request(email: str) -> bool:
    # email validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""):
        return False
    key = f"rp_last_{email.lower()}"
    now = time.time()
    last = st.session_state.get(key)
    if last and (now - last) < 900:
        return False
    st.session_state[key] = now
    return True


def show_reset_password():
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
    st.markdown("<h1 class='login-title'>Réinitialiser le mot de passe</h1>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("reset_form", clear_on_submit=False):
            email = st.text_input(
                "", placeholder="Adresse e-mail associée au compte",
                key="reset_email", label_visibility="collapsed"
            )
            submitted = st.form_submit_button("Envoyer le lien de réinitialisation")

        # Back to connexion
        if st.button("← Retour à la connexion", key="back_to_login"):
            st.session_state.current_screen = "login"
            st.rerun()

        if submitted:
            email = (email or "").strip()
            if not can_request(email):
                st.warning("Demande trop fréquente ou e-mail invalide. Réessayez dans ~15 minutes.")
                return

            db = get_db()
            try:
                request_password_reset(db, email)
            finally:
                db.close()

            st.success("Si un compte existe pour cette adresse, un e-mail vient d’être envoyé.")

# app/auth/reset_password.py
import re
import time
import streamlit as st
from pathlib import Path

from core.auth.database import get_db
from core.auth.service import request_password_reset  # doit exister côté backend

# ----------- CSS -----------
def _load_css(path: str = "assets/style-login.css"):
    p = Path(path)
    if p.exists():
        st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ----------- Rate-limit simple (session) -----------
def can_request(email: str) -> bool:
    # validation rapide d'e-mail
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""):
        return False
    key = f"rp_last_{email.lower()}"
    now = time.time()
    last = st.session_state.get(key)
    # 900s = 15 minutes
    if last and (now - last) < 900:
        return False
    st.session_state[key] = now
    return True

# ----------- UI -----------
def show_reset_password():
    _load_css()
    st.markdown("<h1 class='login-title'>Réinitialiser le mot de passe</h1>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("reset_form", clear_on_submit=False):
            email = st.text_input(
                "", placeholder="Adresse e-mail associée au compte",
                key="reset_email", label_visibility="collapsed"
            )
            submitted = st.form_submit_button("Envoyer le lien de réinitialisation")

        # Retour à la connexion
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
                # Réponse neutre côté UI: ne révèle pas si l'email existe ou non
                request_password_reset(db, email)
            finally:
                db.close()

            st.success("Si un compte existe pour cette adresse, un e-mail vient d’être envoyé.")

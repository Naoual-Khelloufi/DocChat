# app/auth/reset_password.py
import streamlit as st
from pathlib import Path
# from core.auth.email import send_reset_email  # à implémenter côté backend

def _load_css(path: str = "assets/style-login.css"):
    p = Path(path)
    if p.exists():
        st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

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

        # Retour
        if st.button("← Retour à la connexion", key="back_to_login"):
            st.session_state.current_screen = "login"
            st.rerun()

        if submitted:
            if not email.strip():
                st.error("Veuillez entrer votre adresse e-mail.")
            else:
                # TODO: déclencher ton backend d’envoi (token + e-mail)
                # send_reset_email(email)
                st.success(
                    "Si un compte existe pour cette adresse, un e-mail de réinitialisation vient d’être envoyé."
                )

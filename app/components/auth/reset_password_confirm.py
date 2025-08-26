import streamlit as st
from pathlib import Path
from core.auth.database import get_db
from core.auth.service import verify_reset_token, consume_reset_token

def _load_css(path="assets/style-login.css"):
    p = Path(path)
    if p.exists():
        st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

def show_reset_password_confirm():
    _load_css()
    st.markdown("<h1 class='login-title'>Définir un nouveau mot de passe</h1>", unsafe_allow_html=True)

    params = st.experimental_get_query_params()
    raw_token = (params.get("token") or [None])[0]

    _, col, _ = st.columns([1,2,1])
    with col:
        if not raw_token:
            st.error("Lien invalide (token manquant).")
            if st.button("Retour à la connexion"):
                st.session_state.current_screen = "login"
                st.rerun()
            return

        with st.form("confirm_form", clear_on_submit=False):
            new_pwd  = st.text_input("", placeholder="Nouveau mot de passe", type="password", label_visibility="collapsed")
            new_pwd2 = st.text_input("", placeholder="Confirmer le mot de passe", type="password", label_visibility="collapsed")
            submitted = st.form_submit_button("Confirmer")

        if submitted:
            if len(new_pwd) < 8:
                st.error("Le mot de passe doit contenir au moins 8 caractères.")
                return
            if new_pwd != new_pwd2:
                st.error("Les mots de passe ne correspondent pas.")
                return

            db = get_db()
            try:
                user = verify_reset_token(db, raw_token)
                if not user:
                    st.error("Lien invalide ou expiré.")
                    return
                user.set_password(new_pwd)   # خاصها تكون فالموديل
                db.commit()
                consume_reset_token(db, raw_token)
            finally:
                db.close()

            st.success("Mot de passe modifié avec succès.")
            if st.button("Se connecter"):
                st.session_state.current_screen = "login"
                st.rerun()

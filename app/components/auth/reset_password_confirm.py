import streamlit as st
from pathlib import Path
from core.auth.database import get_db
from core.auth.service import verify_reset_token, consume_reset_token
import base64
import mimetypes

def _load_css(path="assets/style-login.css"):
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

def show_reset_password_confirm():
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
    st.markdown("<h1 class='login-title'>Définir un nouveau mot de passe</h1>", unsafe_allow_html=True)

    # Token from the URL or from the session
    raw_token = st.query_params.get("token") or st.session_state.get("reset_token")

    # If a token is present in the URL, we store it and clean the URL
    if st.query_params.get("token"):
        st.session_state.reset_token = raw_token
        st.query_params.from_dict({"screen": "reset_password_confirm"}) 
        st.rerun()

    # Automatically redirect to login if the token do not exist
    if not raw_token:
        st.session_state.pop("reset_token", None)
        st.session_state.current_screen = "login"
        st.query_params.from_dict({"screen": "login"})
        st.rerun()
        st.stop() 

    _, col, _ = st.columns([1, 2, 1])
    with col:
        if not raw_token:
            st.error("Lien invalide (token manquant).")
            if st.button("← Retour à la connexion", key="back_to_login"):
                st.session_state.pop("reset_token", None)
                st.session_state.current_screen = "login"
                st.query_params.from_dict({"screen": "login"})
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
                user.set_password(new_pwd)
                db.commit()
                consume_reset_token(db, raw_token)
                st.session_state.pop("reset_token", None)
            finally:
                db.close()

            st.success("Mot de passe modifié avec succès.")
            if st.button("Se connecter", key="back_login_after_success"):
                st.session_state.current_screen = "login"
                st.query_params.from_dict({"screen": "login"})
                st.rerun()



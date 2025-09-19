import streamlit as st
from core.auth import crud, database
from collections import defaultdict
from utils.nav import navigate
import base64
import mimetypes
from pathlib import Path

#------------
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
#------------

def render():
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
    user = st.session_state.user
    st.header("Mon profil")

    with st.form("edit_profile"):
        new_username = st.text_input("Nom d'utilisateur", value=user["username"])
        new_email    = st.text_input("Email", value=user.get("email") or "")
        new_password = st.text_input("Nouveau mot de passe", type="password")

        if st.form_submit_button("Enregistrer"):
            db = database.SessionLocal()
            crud.update_user(
                db,
                user_id=user["id"],
                username=new_username,
                email=new_email or None,
                password=new_password or None, 
            )
            st.success("Profil mis à jour !")
            # Update session
            st.session_state.user["username"] = new_username
            st.session_state.user["email"] = new_email

    st.markdown("---")

    # Personnel history
    st.subheader("Mon historique")

    db = database.SessionLocal()
    history = crud.get_user_history(db, user["id"]) 

    # Grouped by date
    grouped = defaultdict(list)
    for h in history:
        grouped[h.timestamp.strftime("%Y-%m-%d")].append(h)

    dates = sorted(grouped.keys(), reverse=True)
    date_sel = st.selectbox("Choisir une date", ["---"] + dates, index=0)

    if date_sel != "---":
        for h in grouped[date_sel]:
            st.markdown(f"** {h.timestamp.strftime('%H:%M:%S')}**")
            st.markdown(f"** Q :** {h.question}")
            st.markdown(f"** R :** {h.answer}")
            st.markdown("-----")

    if st.button(" Supprimer mon compte", type="primary"):
        st.session_state.show_confirm_delete = True

    if st.session_state.get("show_confirm_delete"):
        st.warning(
            "Cette action est **irréversible** ! "
            "Vos documents et votre historique seront supprimés."
        )
        col_yes, col_no = st.columns(2)
        if col_yes.button(" Oui, supprimer définitivement"):
            db  = database.SessionLocal()
            uid = st.session_state["user_id"]
            crud.delete_user_and_data(db, uid)

            # Force the logout
            for k in ("user", "user_id", "auth_action"):
                st.session_state.pop(k, None)
            st.session_state.current_screen = "landing"
            st.success("Compte supprimé.")
        if col_no.button(" Annuler"):
            st.session_state.show_confirm_delete = False

    if st.button("⬅️ Retour"):
        navigate("main_app")
    
    if not history:
        st.info("Aucun message enregistré.")
        return
        
